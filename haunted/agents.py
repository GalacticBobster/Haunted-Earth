"""The three agents of Haunted Earth.

  python -m haunted.agents scout     [--sample] [--every 60]
  python -m haunted.agents analyst   [--every 5]
  python -m haunted.agents narrator  [--every 5]

Scout     polls open hazard feeds -> updates one Haunt actor per event -> posts #sightings
Analyst   reads #sightings -> runs physics on the actor's state -> posts #verdicts
Narrator  reads #verdicts -> writes a spooky line (LLM, numbers locked) -> posts #stories
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("DURABLE_ACTORS_CONTROL_PLANE_URL", "http://127.0.0.1:7100")

from generated import actors as _actors  # noqa: E402  (created by `durable-actors generate`)

from . import board, relay  # noqa: E402
from .feeds import fetch_all, iso, now  # noqa: E402
from .llm import narrate  # noqa: E402
from .physics import analyze  # noqa: E402

class _Retry:
    """Wrap an actor stub so calls retry while the actor server is (re)starting."""

    def __init__(self, stub):
        self._stub = stub

    def __getattr__(self, name):
        fn = getattr(self._stub, name)
        if not callable(fn):
            return fn

        def call(*a, **kw):
            for attempt in range(15):
                try:
                    return fn(*a, **kw)
                except Exception as exc:
                    msg = str(exc)
                    if attempt == 14 or not any(w in msg for w in ("not ready", "unavailable", "Connection")):
                        raise
                    time.sleep(1)
        return call


class actors:  # same API as generated.actors, with retries
    class Haunt:
        @staticmethod
        def get(i):
            return _Retry(_actors.Haunt.get(i))

    class Globe:
        @staticmethod
        def get(i):
            return _Retry(_actors.Globe.get(i))


FEED_PREFIX = {"USGS": "eq-", "EONET": "eo-", "SWPC": "aurora-"}
MAX_POSTS_PER_CYCLE = 25


def log(who: str, msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} [{who}] {msg}", flush=True)


def say(channel: str, who: str, hid: str | None, text: str) -> None:
    """Post on Agent Relay and copy to the Supabase chatter feed."""
    try:
        relay.post(channel, text, who)
    except Exception as exc:
        log(who, f"relay post failed: {exc}")
    try:
        board.log_chatter(who, hid, text)
    except Exception as exc:
        log(who, f"chatter write failed: {exc}")


def state_dict(s) -> dict:
    d = s.model_dump()
    d["extra"] = json.loads(d.pop("extra_json") or "{}")
    return d


# ---------------------------------------------------------------- scout
def scout_cycle(globe, sample: bool) -> None:
    events, errors = fetch_all(sample=sample)
    for e in errors:
        log("scout", f"feed error {e}")
    ok_prefixes = [p for name, p in FEED_PREFIX.items() if not any(x.startswith(name) for x in errors)]

    def sight(ev):
        h = actors.Haunt.get(ev["id"])
        res = h.sight(ev["kind"], ev["title"], float(ev["lat"]), float(ev["lon"]),
                      float(ev["severity"]), ev["status"], ev["seen_at"], json.dumps(ev["extra"]))
        return ev, res, (h.state() if res != "same" else None)

    def close(hid):
        h = actors.Haunt.get(hid)
        return h.state() if h.close(iso(now())) else None

    # each event is its own actor, so they can be updated in parallel without races
    changed_states, to_post = [], []
    seen_ids = {ev["id"] for ev in events}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for ev, res, st in pool.map(sight, events):
            if res == "new":
                globe.register(ev["id"])
            if st is not None:
                changed_states.append(st)
                if ev["status"] != "closed":
                    to_post.append((ev["severity"], res, ev))
        # events that vanished from a healthy feed: close their eyes
        gone = [h for h in globe.all_ids()
                if h not in seen_ids and any(h.startswith(p) for p in ok_prefixes)]
        changed_states += [st for st in pool.map(close, gone) if st is not None]

    board.mirror_many(changed_states)
    to_post.sort(key=lambda x: -x[0])
    for sev, res, ev in to_post[:MAX_POSTS_PER_CYCLE]:
        say("sightings", "scout", ev["id"],
            f"[id={ev['id']}] {res.upper()} {ev['kind']}: {ev['title']} (severity {sev:.2f}, {ev['status']})")
    log("scout", f"{len(events)} events, {len(changed_states)} changed, "
                 f"{min(len(to_post), MAX_POSTS_PER_CYCLE)} posted; board={board.mode()}")


def run_scout(sample: bool, every: int, once: bool) -> None:
    relay.setup()
    globe = actors.Globe.get("earth")
    run = globe.scout_started()
    known = globe.all_ids()
    log("scout", f"start #{run}; globe already remembers {len(known)} haunts")
    if known:  # rebuild the public board from the actors (the actors are the source of truth)
        with ThreadPoolExecutor(max_workers=12) as pool:
            board.mirror_many(list(pool.map(lambda i: actors.Haunt.get(i).state(), known)))
        log("scout", f"resynced {len(known)} haunts from actors to the board")
    while True:
        try:
            scout_cycle(globe, sample)
        except Exception:
            log("scout", traceback.format_exc())
        if once:
            return
        time.sleep(every)


# ---------------------------------------------------------------- analyst
def analyse_one(hid: str, others: list[dict]) -> bool:
    h = actors.Haunt.get(hid)
    if not h.needs_analysis():
        return False
    s = state_dict(h.state())
    result = analyze(s, others)
    h.set_verdict(result["verdict"])
    board.mirror_haunt(h.state())
    say("verdicts", "analyst", hid, f"[id={hid}] {s['title']}: {result['verdict']}")
    return True


def run_analyst(every: int, once: bool) -> None:
    relay.setup()
    done_msgs: set[str] = set()
    log("analyst", "start")
    while True:
        try:
            others = board.load_haunts()
            n = 0
            for m in relay.read("sightings", "analyst"):
                if m["id"] in done_msgs:
                    continue
                done_msgs.add(m["id"])
                hid = relay.haunt_id(m["text"])
                if hid and analyse_one(hid, others):
                    n += 1
            # backlog sweep: anything on the board still without a verdict (durable catch-up)
            backlog = sorted((r for r in others if not r.get("verdict") and r.get("status") != "closed"),
                             key=lambda r: -(r.get("severity") or 0))[:10]
            for r in backlog:
                if analyse_one(r["id"], others):
                    n += 1
            if n:
                log("analyst", f"{n} verdicts")
        except Exception:
            log("analyst", traceback.format_exc())
        if once:
            return
        time.sleep(every)


# ---------------------------------------------------------------- narrator
def narrate_one(hid: str) -> bool:
    h = actors.Haunt.get(hid)
    if not h.needs_story():
        return False
    s = h.state()
    story, source = narrate(s.title, s.kind, s.verdict)
    h.set_story(story, s.verdict)
    board.mirror_haunt(h.state())
    say("stories", "narrator", hid, f"[id={hid}] {story}")
    log("narrator", f"{hid} via {source}")
    return True


def run_narrator(every: int, once: bool) -> None:
    relay.setup()
    done_msgs: set[str] = set()
    log("narrator", "start")
    while True:
        try:
            msgs = [m for m in relay.read("verdicts", "narrator") if m["id"] not in done_msgs]
            for m in msgs[-5:]:                 # newest first-class; LLM calls are slow
                done_msgs.add(m["id"])
                hid = relay.haunt_id(m["text"])
                if hid:
                    narrate_one(hid)
            for m in msgs[:-5]:
                done_msgs.add(m["id"])          # older ones caught by the sweep below
            rows = sorted((r for r in board.load_haunts()
                           if r.get("verdict") and not r.get("story") and r.get("status") != "closed"),
                          key=lambda r: -(r.get("severity") or 0))[:3]
            for r in rows:
                narrate_one(r["id"])
        except Exception:
            log("narrator", traceback.format_exc())
        if once:
            return
        time.sleep(every)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", choices=["scout", "analyst", "narrator"])
    ap.add_argument("--sample", action="store_true", help="use bundled offline data")
    ap.add_argument("--every", type=int, default=None, help="seconds between cycles")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    if a.agent == "scout":
        run_scout(a.sample, a.every or 60, a.once)
    elif a.agent == "analyst":
        run_analyst(a.every or 5, a.once)
    else:
        run_narrator(a.every or 5, a.once)


if __name__ == "__main__":
    sys.exit(main())
