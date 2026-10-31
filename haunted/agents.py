"""The three agents of Haunted Earth.

  python -m haunted.agents scout     [--sample] [--every 60]
  python -m haunted.agents analyst   [--every 5]
  python -m haunted.agents narrator  [--every 5]

Scout     polls open hazard feeds -> updates one Haunt actor per event -> posts #sightings
Analyst   reads #sightings -> runs physics on the actor's state -> posts #verdicts
Narrator  reads #verdicts -> writes a spooky line (LLM, numbers locked) -> posts #stories

Newsroom:
  python -m haunted.agents herald   [--sample]
  python -m haunted.agents checker  --role seismologist|meteorologist|spaceweather
  python -m haunted.agents judge

Herald    finds news about the biggest live haunts, extracts numeric claims -> posts #news
Checkers  each specialist checks claims in its field against the official data -> posts #factcheck
Judge     keeps a durable credibility ledger per outlet (Beta-binomial) -> Supabase
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
from .warn import LEVELS  # noqa: E402

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

    class Place:
        @staticmethod
        def get(i):
            return _Retry(_actors.Place.get(i))

    class Mission:
        @staticmethod
        def get(i):
            return _Retry(_actors.Mission.get(i))

    class Crew:
        @staticmethod
        def get(i):
            return _Retry(_actors.Crew.get(i))

    class Outlet:
        @staticmethod
        def get(i):
            return _Retry(_actors.Outlet.get(i))


FEED_PREFIX = {"USGS": "eq-", "EONET": "eo-", "SWPC": "aurora-", "GDACS": "gd-"}
MAX_POSTS_PER_CYCLE = 25


AGENT_NAME = "agent"
LAST_ACTION = {"msg": ""}


def log(who: str, msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} [{who}] {msg}", flush=True)
    if "Traceback" not in msg:
        LAST_ACTION["msg"] = msg[:160]


def _crew_row(st) -> dict:
    return {"name": st.name, "pid": os.getpid(), "runs": st.runs, "cycles": st.cycles,
            "last_action": st.last_action, "last_seen": st.last_seen, "started": st.started}


def beat() -> None:
    """Heartbeat: durable cycle counter + status row for the dashboard's Crew tab."""
    try:
        c = actors.Crew.get(AGENT_NAME)
        c.beat(LAST_ACTION["msg"], iso(now()))
        board.mirror_agent(_crew_row(c.state()))
    except Exception:
        pass


def crew_start() -> None:
    try:
        c = actors.Crew.get(AGENT_NAME)
        runs = c.start(iso(now()))
        st = c.state()
        LAST_ACTION["msg"] = f"online (start #{runs}); {st.cycles} cycles remembered from before"
        log(AGENT_NAME, LAST_ACTION["msg"])
        board.mirror_agent(_crew_row(c.state()))
    except Exception as exc:
        log(AGENT_NAME, f"crew start failed: {exc}")


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
    from .drills import drill_events
    events += drill_events(board.load_drills())          # DRILL events flow through the real pipeline
    ok_prefixes = [p for name, p in FEED_PREFIX.items() if not any(x.startswith(name) for x in errors)]
    ok_prefixes.append("drill-")

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
        beat()
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
        beat()
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
        beat()
        time.sleep(every)


# ---------------------------------------------------------------- newsroom
NEWS_EVERY_MIN = 10
NEWS_TOP_N = 15


def _sample_news() -> dict:
    import pathlib
    d = json.loads((pathlib.Path(__file__).parent / "sample_data.json").read_text())
    return d.get("news", {})


def run_herald(sample: bool, every: int, once: bool) -> None:
    from .feeds import iso as _iso
    from .news import art_id, extract_claims, fetch_news, llm_claims
    use_llm = bool(os.getenv("OPENAI_API_KEY"))     # local LLMs are too slow for every headline
    log("herald", f"start (LLM claim extraction: {'on' if use_llm else 'off'})")
    samples = _sample_news() if sample else {}
    while True:
        try:
            rows = [r for r in board.load_haunts() if r.get("status") != "closed"
                    and not r["id"].startswith("drill-")
                    and r.get("kind") in ("earthquake", "storm", "aurora", "volcano", "wildfire")]
            rows.sort(key=lambda r: -(r.get("severity") or 0))
            for r in rows[:NEWS_TOP_N]:
                h = actors.Haunt.get(r["id"])
                last = h.last_news_check()
                age_min = ((now() - __import__("datetime").datetime.fromisoformat(last)).total_seconds() / 60
                           if last else 1e9)
                if age_min < NEWS_EVERY_MIN:
                    continue
                if sample:
                    arts = [{**a, "id": art_id(a["url"])} for a in samples.get(r["id"], [])]
                    errs = []
                else:
                    arts, errs = fetch_news(r)
                for e in errs:
                    log("herald", f"{r['id']} news error {e}")
                for a in arts:
                    claims = extract_claims(a["title"] + ". " + a.get("summary", ""))
                    if use_llm and not claims:
                        claims = llm_claims(a["title"])
                    a["claims"] = claims
                new_ids = h.add_articles(json.dumps(arts), _iso(now()))
                for a in arts:
                    if a["id"] in new_ids:
                        say("news", "herald", r["id"],
                            f"[id={r['id']}] [art={a['id']}] {a['outlet']}: \"{a['title']}\" "
                            f"({len(a['claims'])} claim(s))")
                log("herald", f"{r['id']}: {len(arts)} articles, {len(new_ids)} new")
        except Exception:
            log("herald", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


def check_haunt(role: str, hid: str) -> int:
    from .factcheck import run_checks
    h = actors.Haunt.get(hid)
    pending = h.pending_articles(role)
    if not pending:
        return 0
    s = state_dict(h.state())
    n = 0
    for a in pending:
        checks = run_checks(role, s["kind"], json.loads(a.claims_json), s["extra"])
        for c in checks:
            cl = c["claim"]
            claim_txt = f"{cl['type']}={cl['value']:g}{(' ' + cl['unit']) if cl.get('unit') else ''}"
            board.log_factcheck({"haunt_id": hid, "article_url": a.url, "headline": a.title,
                                 "outlet": a.outlet, "checker": role, "claim": claim_txt,
                                 "verdict": c["verdict"], "explanation": c["explanation"]})
            say("factcheck", role, hid,
                f"[id={hid}] [art={a.id}] [outlet={a.outlet}] [claim={claim_txt}] "
                f"{c['verdict']}: {c['explanation']}")
            n += 1
        h.mark_checked(a.id, role)
    return n


def run_checker(role: str, every: int, once: bool) -> None:
    from .factcheck import ROLES
    kinds = ROLES[role]["kinds"]
    log(role, f"start; checks {', '.join(sorted(ROLES[role]['claims']))} on {', '.join(kinds)}")
    while True:
        try:
            targets = set()
            for m in relay.read("news", role):
                t = relay.tags(m["text"])
                if t.get("id"):
                    targets.add(t["id"])
            # durable sweep: also any haunt of my kinds with articles I haven't checked
            targets |= {r["id"] for r in board.load_haunts()
                        if r.get("kind") in kinds and r.get("status") != "closed"}
            n = sum(check_haunt(role, hid) for hid in targets)
            if n:
                log(role, f"{n} claims checked")
        except Exception:
            log(role, traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


def run_judge(every: int, once: bool) -> None:
    from .factcheck import credibility
    done: set[str] = set()
    log("judge", "start")
    while True:
        try:
            touched = set()
            for m in relay.read("factcheck", "judge", limit=100):
                if m["id"] in done:
                    continue
                done.add(m["id"])
                t = relay.tags(m["text"])
                verdict = next((v for v in ("CONFIRMED", "MISMATCH", "PLAUSIBLE", "IMPLAUSIBLE", "UNVERIFIABLE")
                                if f"] {v}:" in m["text"]), None)
                if not (t.get("outlet") and t.get("art") and verdict):
                    continue
                key = f"{t['art']}:{m['sender']}:{t.get('claim', '')}"
                if actors.Outlet.get(t["outlet"]).record(key, verdict):
                    touched.add(t["outlet"])
            for o in touched:
                L = actors.Outlet.get(o).ledger()
                mean, sd = credibility(L.confirmed, L.plausible, L.mismatched, L.implausible)
                board.mirror_outlet({"outlet": o, "confirmed": L.confirmed, "plausible": L.plausible,
                                     "mismatched": L.mismatched, "implausible": L.implausible,
                                     "unverifiable": L.unverifiable, "score": round(mean, 3),
                                     "score_sd": round(sd, 3)})
                if L.mismatched + L.implausible:
                    say("stories", "judge", None,
                        f"Ledger: {o} credibility {mean:.0%} ± {sd:.0%} "
                        f"({L.confirmed} confirmed, {L.mismatched + L.implausible} contradicted by physics)")
            if touched:
                log("judge", f"updated {len(touched)} outlet ledger(s)")
        except Exception:
            log("judge", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


# ---------------------------------------------------------------- corroborator
def _sample(key: str):
    import pathlib
    return json.loads((pathlib.Path(__file__).parent / "sample_data.json").read_text()).get(key)


def run_corroborator(sample: bool, every: int, once: bool) -> None:
    """Polls EMSC, JMA and GDACS itself; matches each report to a USGS quake (or spawns a new
    haunt for quakes USGS hasn't listed) and keeps a multi-agency consensus magnitude."""
    import hashlib
    from .consensus import combine, describe, same_quake
    from .world import fetch_quake_reports
    globe = actors.Globe.get("earth")
    log("corroborator", "start; sources EMSC, JMA, GDACS vs USGS")
    while True:
        try:
            # candidate quakes = USGS haunts + ones I spawned earlier
            cands = []
            for r in board.load_haunts():
                if r.get("kind") != "earthquake" or r.get("status") == "closed":
                    continue
                st = state_dict(actors.Haunt.get(r["id"]).state())
                ex = st["extra"]
                cands.append({"id": r["id"], "agency": ex.get("agency", "USGS"), "mag": float(ex.get("mag", 0)),
                              "lat": st["lat"], "lon": st["lon"], "time": ex.get("event_time"),
                              "depth_km": ex.get("depth_km")})
            if sample:
                import datetime as _dt
                reports, errs = _sample("quake_reports") or [], []
                for r in reports:   # sample: align with the sample USGS quake it describes
                    like = next((c for c in cands if c["id"] == r.get("like")), None)
                    t = _dt.datetime.fromisoformat(like["time"]) if like and like["time"] else \
                        _dt.datetime(2026, 10, 31, 12, tzinfo=_dt.timezone.utc)
                    r["time"] = iso(t + _dt.timedelta(seconds=r.get("dt_s", 0)))
            else:
                reports, errs = fetch_quake_reports()
            for e in errs:
                log("corroborator", f"feed error {e}")
            touched, spawned = set(), 0
            for rep in reports:
                match = next((c for c in cands if same_quake(rep, c)), None)
                if match is None:
                    if rep["mag"] < 4.5:
                        continue
                    hid = "xq-" + hashlib.sha1(f"{rep['ref']}".encode()).hexdigest()[:10]
                    h = actors.Haunt.get(hid)
                    status = "awake"
                    res = h.sight("earthquake", f"M{rep['mag']:.1f} {rep.get('place') or 'unlisted region'} ({rep['agency']})",
                                  rep["lat"], rep["lon"], max(0.05, min(1.0, (rep["mag"] - 2.5) / 5)), status,
                                  rep["time"] or iso(now()),
                                  json.dumps({"mag": rep["mag"], "depth_km": rep.get("depth_km"),
                                              "event_time": rep["time"], "agency": rep["agency"]}))
                    if res == "new":
                        globe.register(hid)
                        spawned += 1
                        board.mirror_haunt(h.state())
                        say("sightings", "corroborator", hid,
                            f"[id={hid}] NEW earthquake: M{rep['mag']:.1f} {rep.get('place')} reported by "
                            f"{rep['agency']}, not in the USGS feed yet")
                    match = {"id": hid, "agency": rep["agency"], **rep}
                    cands.append(match)
                if match["agency"] == rep["agency"]:
                    continue        # a source can't corroborate itself
                if actors.Haunt.get(match["id"]).add_report(rep["agency"], json.dumps(
                        {"mag": rep["mag"], "ref": rep["ref"], "depth_km": rep.get("depth_km")})):
                    touched.add(match["id"])
            for hid in touched:
                h = actors.Haunt.get(hid)
                st = state_dict(h.state())
                base = {"agency": st["extra"].get("agency", "USGS"), "mag": float(st["extra"].get("mag", 0))}
                reps = [base] + [{"agency": a, "mag": float(v["mag"])} for a, v in json.loads(h.reports()).items()]
                c = combine(reps)
                text = describe(c, reps)
                h.set_consensus(text)
                board.mirror_haunt(h.state())
                say("consensus", "corroborator", hid, f"[id={hid}] {st['title']}: {text}")
                if not c["agree"]:
                    say("stories", "corroborator", hid, f"[id={hid}] Agencies disagree on {st['title']}: {text}")
            if touched or spawned:
                log("corroborator", f"{len(touched)} consensus updates, {spawned} new quakes spawned")
        except Exception:
            log("corroborator", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


# ---------------------------------------------------------------- sentinel
def run_sentinel(sample: bool, every: int, once: bool) -> None:
    """US county alert board from NWS; links alerts to haunts within 100 km (once, durably)."""
    from .physics import haversine_km
    from .world import fetch_county_alerts, parse_nws
    log("sentinel", "start; NWS active alerts by county")
    while True:
        try:
            rows = parse_nws(_sample("nws") or {}) if sample else fetch_county_alerts()
            haunts = [h for h in board.load_haunts() if h.get("status") != "closed" and h.get("kind") != "aurora"]
            links = 0
            for r in rows:
                if r["lat"] is None:
                    continue
                near = min(((haversine_km(r["lat"], r["lon"], h["lat"], h["lon"]), h) for h in haunts),
                           key=lambda x: x[0], default=None)
                if near and near[0] <= 100:
                    d, h = near
                    r["linked_haunt"] = h["id"]
                    key = f"{r['event']}|{r['fips']}"
                    if actors.Haunt.get(h["id"]).add_alert(key):
                        links += 1
                        say("alerts", "sentinel", h["id"],
                            f"[id={h['id']}] ⚠ {r['event']} ({r['severity']}) in {r['county']}, {r['state']}: "
                            f"alert area centred ~{d:.0f} km from {h['title']}")
            board.replace_county_alerts(rows)
            counties = len({(r["state"], r["county"]) for r in rows})
            log("sentinel", f"{len(rows)} alert-county rows across {counties} counties; {links} new haunt links")
        except Exception:
            log("sentinel", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


# ---------------------------------------------------------------- warden (warning system)
def email_place(p: dict, changes: list) -> None:
    """Welcome once per address, then email issued/upgraded warnings at or above ALERT_MIN_LEVEL."""
    from . import notify
    to = (p.get("email") or "").strip()
    if not to:
        return
    if not notify.configured():
        return
    min_level = int(os.getenv("ALERT_MIN_LEVEL", "1"))
    try:
        if actors.Place.get(p["id"]).welcome(to):
            notify.send(to, *notify.welcome_email(p))
            log("warden", f"welcome email -> place {p['id']}")
        for c in changes:
            if c.change in ("issued", "upgraded") and c.level >= min_level:
                notify.send(to, *notify.change_email(p, c))
                log("warden", f"alert email ({c.hazard}, level {c.level}) -> place {p['id']}")
    except Exception as exc:
        log("warden", f"email to place {p['id']} failed: {exc}")


def run_warden(sample: bool, every: int, once: bool) -> None:
    """Place-specific Advisory/Watch/Warning from physics + official alerts. Each place is a
    durable actor that only reports changes (issued / upgraded / downgraded / expired)."""
    from .warn import (LEVELS, aurora_threat, cyclone_threat, nws_threats, quake_threat,
                       weather_threats)
    from .world import fetch_nws_point, fetch_open_meteo, is_us
    wx_cache: dict[str, tuple[float, dict]] = {}
    traffic_cache: dict[str, tuple[float, dict | None]] = {}
    log("warden", "start")
    while True:
        try:
            places = board.load_places()
            if sample:
                for sp in _sample("places") or []:
                    if not any(p["id"] == sp["id"] for p in places):
                        board.add_place(sp["name"], sp["lat"], sp["lon"], sp["coastal"])
                places = board.load_places()
            live = [h for h in board.load_haunts() if h.get("status") in ("awake", "fading")]
            quakes, storms, kp = [], [], None
            for h in live:
                if h["kind"] not in ("earthquake", "storm", "aurora"):
                    continue
                st = state_dict(actors.Haunt.get(h["id"]).state())
                if h["kind"] == "earthquake":
                    quakes.append({"id": h["id"], "lat": st["lat"], "lon": st["lon"],
                                   "mag": st["extra"].get("mag", 0), "depth_km": st["extra"].get("depth_km")})
                elif h["kind"] == "storm":
                    storms.append(st)
                else:
                    kp = st["extra"].get("kp")
            # drills take effect immediately (no wait for the scout's next pass)
            from .drills import drill_events
            seen_ids = {q["id"] for q in quakes} | {s_["id"] for s_ in storms}
            for ev in drill_events(board.load_drills()):
                if ev["id"] in seen_ids:
                    continue
                if ev["kind"] == "earthquake":
                    quakes.append({"id": ev["id"], "lat": ev["lat"], "lon": ev["lon"],
                                   "mag": ev["extra"]["mag"], "depth_km": ev["extra"]["depth_km"]})
                else:
                    storms.append({"id": ev["id"], "title": ev["title"], "extra": ev["extra"]})
            issued = 0
            # ---- Airport Watch: METAR + SIGMET + traffic for airport places (apt-xxxx)
            from .aviation import (AIRPORTS, aviation_threats, fetch_metars, fetch_sigmets, fetch_traffic,
                                   icao_of, snapshot)
            apt_snaps: dict[str, dict] = {}
            icaos = [icao_of(p["id"]) for p in places if icao_of(p["id"]) in AIRPORTS]
            if icaos:
                try:
                    if sample:
                        av = _sample("aviation") or {}
                        metars, sigs = av.get("metars", {}), av.get("sigmets", [])
                    else:
                        metars, sigs = fetch_metars(icaos), fetch_sigmets()
                        need = [ic for ic in icaos if time.time() - traffic_cache.get(ic, (0, None))[0] > 600]

                        def _tr(ic):
                            try:
                                a = AIRPORTS[ic]
                                return ic, fetch_traffic(a[1], a[2])
                            except Exception:
                                return ic, None
                        with ThreadPoolExecutor(max_workers=8) as tpool:
                            for ic, tr in tpool.map(_tr, need):
                                traffic_cache[ic] = (time.time(), tr)
                    for ic in icaos:
                        tr = None
                        if not sample:
                            ts_, tr = traffic_cache.get(ic, (0, None))
                            if time.time() - ts_ > 600:
                                try:
                                    a = AIRPORTS[ic]
                                    tr = fetch_traffic(a[1], a[2])
                                except Exception:
                                    tr = None
                                traffic_cache[ic] = (time.time(), tr)
                        else:
                            tr = (av.get("traffic") or {}).get(ic)
                        apt_snaps[ic] = snapshot(ic, metars.get(ic), sigs, tr)
                    board.mirror_airports(list(apt_snaps.values()))
                except Exception as exc:
                    log("warden", f"aviation fetch failed: {exc}")
            def handle(p):
                items = []
                if icao_of(p["id"]) in apt_snaps:
                    items += aviation_threats(apt_snaps[icao_of(p["id"])])
                for q in quakes:
                    t = quake_threat(q, p)
                    if t:
                        items.append(t)
                for s_ in storms:
                    t = cyclone_threat(s_, p)
                    if t:
                        items.append(t)
                if kp is not None:
                    t = aurora_threat(float(kp), p)
                    if t:
                        items.append(t)
                try:
                    if sample:
                        wx = (_sample("weather") or {}).get(p["id"], {})
                    else:
                        ts, wx = wx_cache.get(p["id"], (0, {}))
                        if time.time() - ts > 1800:
                            wx = fetch_open_meteo(p["lat"], p["lon"])
                            wx_cache[p["id"]] = (time.time(), wx)
                    items += weather_threats(p, wx)
                    if not sample and is_us(p["lat"], p["lon"]):
                        items += nws_threats(fetch_nws_point(p["lat"], p["lon"]))
                except Exception as exc:
                    log("warden", f"{p['id']} forecast/alert fetch failed: {exc}")
                # one warning per key; keep the highest level
                best: dict[str, dict] = {}
                for i in items:
                    if i["key"] not in best or i["level"] > best[i["key"]]["level"]:
                        best[i["key"]] = i
                items = sorted(best.values(), key=lambda i: -i["level"])
                changes = actors.Place.get(p["id"]).update(p["name"], float(p["lat"]), float(p["lon"]),
                                                           json.dumps(items), iso(now()))
                board.replace_warnings(p["id"], [{"key": i["key"], "place_name": p["name"],
                                                  "hazard": i["hazard"], "level": i["level"],
                                                  "level_name": LEVELS[i["level"]], "headline": i["headline"],
                                                  "detail": i["detail"]} for i in items])
                for c in changes:
                    word = LEVELS[c.level].upper() if c.change != "expired" else "ALL CLEAR"
                    say("warnings", "warden", None,
                        f"[place={p['id']}] {word} {c.change} for {p['name']}: {c.headline}")
                email_place(p, changes)
                return len(changes)

            def safe(p):
                try:
                    return handle(p)
                except Exception as exc:
                    log("warden", f"{p.get('id')} failed: {exc}")
                    return 0
            with ThreadPoolExecutor(max_workers=8) as ppool:
                issued = sum(ppool.map(safe, places))
            if issued:
                log("warden", f"{issued} warning changes across {len(places)} places")
        except Exception:
            log("warden", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


# ---------------------------------------------------------------- quartermaster (relief missions)
def run_quartermaster(sample: bool, every: int, once: bool) -> None:
    """Opens a relief Mission for every place at Watch/Warning, works its tasks, and lets finished
    tasks spawn follow-ups (bounded depth), e.g. no shelters -> widen search -> medical gap -> request."""
    from .relief import CHECKLIST, fetch_resources, needs_72h, parse_resources, summarize
    min_level = int(os.getenv("RELIEF_MIN_LEVEL", "2"))
    cache: dict[str, list] = {}
    log("quartermaster", f"start; missions open at level >= {min_level}")

    def resources(mid: str, place: dict, km: float) -> list:
        key = f"{mid}@{km}"
        if key not in cache:
            if sample:
                raw = (_sample("resources") or {}).get(place["id"], {"elements": []})
                cache[key] = [r for r in parse_resources(raw, place["lat"], place["lon"]) if r["km"] <= km]
            else:
                cache[key] = fetch_resources(place["lat"], place["lon"], km)
        return cache[key]

    def work(mid: str, m, t, place: dict, row: dict) -> tuple[str, list]:
        """Do one task; return (result, follow-ups)."""
        title = t.title
        if title.startswith("Map nearby help within"):
            km = float(title.split("within ")[1].split()[0])
            res = resources(mid, place, km)
            row["resources"] = res[:40]
            c = summarize(res)
            shelters = c.get("shelter", 0) + c.get("assembly point", 0)
            medical = c.get("hospital", 0) + c.get("clinic", 0)
            spawn = []
            if shelters == 0 and km < 40:
                spawn.append(("Map nearby help within 40 km", "scout"))
            if medical < 2:
                spawn.append(("Flag medical capacity gap", "medic"))
            spawn.append(("Publish nearest-help list", "comms"))
            return (f"{len(res)} sites within {km:.0f} km: " +
                    (", ".join(f"{v} {k}" for k, v in sorted(c.items())) or "none mapped in OpenStreetMap"), spawn)
        if title == "Flag medical capacity gap":
            med = [r for r in row.get("resources", []) if r["kind"] in ("hospital", "clinic")]
            near = f"nearest: {med[0]['name']} at {med[0]['km']} km" if med else "none mapped nearby"
            return (f"Only {len(med)} hospital/clinic sites mapped; {near}.",
                    [("Draft request for mobile medical support", "medic")])
        if title == "Draft request for mobile medical support":
            return (f"REQUEST: mobile medical team / field clinic for {place['name']} "
                    f"({place['lat']:.2f}, {place['lon']:.2f}) ahead of {m.hazard}. Local hospital capacity is thin.", [])
        if title == "Publish nearest-help list":
            top = []
            for kind in ("hospital", "shelter", "assembly point", "drinking water", "pharmacy", "fire station"):
                top += [r for r in row.get("resources", []) if r["kind"] == kind][:2]
            row["nearest"] = top[:8]
            return ("; ".join(f"{r['kind']}: {r['name']} ({r['km']} km)" for r in top[:5]) or "nothing mapped", [])
        if title.startswith("Estimate 72-hour supplies"):
            n = needs_72h(1000)
            row["needs"] = n
            return (f"Per 1,000 people for 72 h (Sphere minimums): {n['water_litres']:,} L water "
                    f"(~{n['water_trucks_10k_L']} × 10,000 L trucks), {n['food_kcal'] / 1e6:.1f} M kcal food, "
                    f"{n['shelter_m2']:,.0f} m² covered shelter.", [("Draft volunteer & donation call", "comms")])
        if title == "Draft volunteer & donation call":
            n = row.get("needs") or needs_72h(1000)
            return (f"{m.hazard.title()} {LEVELS[m.level].lower()} for {place['name']}. Help needed: drinking water "
                    f"(15 L per person per day), food, tarps/shelter, power banks, first-aid kits. Volunteers: check on "
                    f"elderly neighbours and staff shelters. Donate through recognised local relief organisations.", [])
        if title.startswith("Find usable alternates within"):
            from .aviation import AIRPORTS, alternates, fetch_metars, icao_of
            ic = icao_of(place["id"])
            km = float(title.split("within ")[1].split()[0])
            if sample:
                mets = (_sample("aviation") or {}).get("metars", {})
            else:
                mets = fetch_metars(list(AIRPORTS))
            alts = alternates(ic, km, mets)
            ok = [a for a in alts if a["usable"]]
            row["alternates"] = alts[:6]
            row["nearest"] = [{"kind": f"alternate · {a['cat']}", "name": f"{a['icao']} {a['name']}", "km": a["km"],
                               "directions": f"https://aviationweather.gov/data/metar/?ids={a['icao']}"} for a in ok[:5]]
            spawn = [("Widen alternates search to 1500 km", "ops")] if not ok and km < 1500 else []
            spawn.append(("Notify dispatch of alternates", "comms"))
            return ((", ".join(f"{a['icao']} {a['cat']} {a['km']} km" for a in ok[:4]) or
                     f"no usable alternates within {km:.0f} km"), spawn)
        if title.startswith("Widen alternates search to"):
            return work(mid, m, type(t)(**{**t.model_dump(), "title": "Find usable alternates within 1500 km"}),
                        place, row)
        if title == "Notify dispatch of alternates":
            alts = [a for a in row.get("alternates", []) if a["usable"]]
            return (f"DISPATCH: {m.hazard} at {place['name']}. Usable alternates: "
                    + (", ".join(f"{a['icao']} ({a['name']}, {a['km']} km, {a['cat']})" for a in alts[:3]) or "none listed")
                    + ". Load extra holding/diversion fuel.", [])
        if title == "Runway & taxiway inspection after shaking":
            return ("Inspect runway pavement, lighting, ILS/navaids and tower before reopening; issue NOTAM.", [])
        if title.endswith("ops checklist"):
            from .aviation import OPS_CHECKLIST
            items = OPS_CHECKLIST.get(m.hazard, ["Follow airport emergency plan"])
            row["checklist"] = items
            return " · ".join(items), []
        if title.startswith("Prepare") and "checklist" in title:
            items = CHECKLIST.get(m.hazard, CHECKLIST["official"])
            row["checklist"] = items
            return " · ".join(items), []
        return "noted", []

    while True:
        try:
            places = {p["id"]: p for p in board.load_places()}
            warns = [w for w in board.load_warnings() if int(w["level"]) >= min_level]
            wanted = {}
            for w in warns:
                if w["hazard"] == "aurora":
                    continue
                mid = f"{w['place_id']}--{w['hazard']}"   # actor ids allow letters, digits, - _
                wanted[mid] = max(wanted.get(mid, 0), int(w["level"]))
            rows = {r["id"]: r for r in board.load_missions()}
            # stand down missions whose warning has ended
            for mid, r in rows.items():
                if mid != "allocation" and mid not in wanted and r.get("status") == "active":
                    if actors.Mission.get(mid).stand_down():
                        board.mirror_mission({**r, "status": "stood down"})
                        say("relief", "quartermaster", None, f"[mission={mid}] Stood down: warning ended for {r['place_name']}")
            for mid, level in wanted.items():
                pid, hazard = mid.split("--", 1)
                place = places.get(pid)
                if not place:
                    continue
                m = actors.Mission.get(mid)
                if pid.startswith("apt-"):
                    seeds = [(f"Prepare {hazard} ops checklist", "comms")]
                    if hazard in ("flight category", "crosswind", "thunderstorm", "sigmet", "cyclone", "earthquake"):
                        seeds.insert(0, ("Find usable alternates within 400 km", "ops"))
                    if hazard == "earthquake":
                        seeds.insert(0, ("Runway & taxiway inspection after shaking", "ops"))
                else:
                    seeds = [("Map nearby help within 15 km", "scout"),
                             ("Estimate 72-hour supplies per 1,000 people", "logistics"),
                             (f"Prepare {hazard} safety checklist", "comms")]
                if m.open(pid, place["name"], hazard, level, iso(now()), json.dumps(seeds)):
                    say("relief", "quartermaster", None,
                        f"[mission={mid}] Opened {LEVELS[level]} relief mission for {place['name']} ({hazard})")
                prev = rows.get(mid, {})
                row = {"resources": json.loads(prev.get("resources_json") or "[]"),
                       "needs": json.loads(prev.get("needs_json") or "{}") or None,
                       "nearest": json.loads(prev.get("nearest_json") or "[]"),
                       "alternates": json.loads(prev.get("resources_json") or "[]") if pid.startswith("apt-") else [],
                       "checklist": json.loads(prev.get("checklist_json") or "[]")}
                for _ in range(10):                      # work up to 10 tasks per mission per cycle
                    pend = m.pending()
                    if not pend:
                        break
                    t = pend[0]
                    st_ = m.state()
                    try:
                        result, spawn = work(mid, st_, t, place, row)
                    except Exception as exc:
                        result, spawn = f"failed: {exc}", []
                    new = m.complete(t.id, result, json.dumps(spawn))
                    say("relief", "quartermaster", None,
                        f"[mission={mid}] ✓ {t.role}: {t.title}: {result[:160]}"
                        + (f" → spawned {len(new)} follow-up(s)" if new else ""))
                st_ = m.state()
                board.mirror_mission({
                    "id": mid, "place_id": pid, "place_name": place["name"], "hazard": hazard,
                    "level": st_.level, "status": st_.status,
                    "tasks_json": json.dumps([t.model_dump() for t in st_.tasks]),
                    "resources_json": json.dumps(row["resources"]), "needs_json": json.dumps(row["needs"] or {}),
                    "nearest_json": json.dumps(row["nearest"]), "checklist_json": json.dumps(row["checklist"])})
            # master optimisation: share scarce resources across every active mission
            from .cities import population
            from .drills import allocate
            active = [r for r in board.load_missions() if r.get("status") == "active" and r["id"] != "allocation"
                      and not r["id"].startswith("apt-")]
            if active:
                plan = allocate(active, {pid: population(p) for pid, p in places.items()})
                for r in plan["rows"]:
                    if places.get(r["mission"].split("--")[0], {}).get("shared"):
                        r["place"] = "shared location"
                sig = json.dumps([(r["mission"], r["trucks"], r["teams"]) for r in plan["rows"]])
                prev = next((r for r in board.load_missions() if r["id"] == "allocation"), {})
                board.mirror_mission({"id": "allocation", "place_id": "", "place_name": "", "hazard": "allocation",
                                      "level": 0, "status": "active", "tasks_json": json.dumps(plan),
                                      "resources_json": sig, "needs_json": "{}", "nearest_json": "[]",
                                      "checklist_json": "[]"})
                if prev.get("resources_json") != sig:
                    say("relief", "quartermaster", None,
                        f"Re-optimised: {plan['pool']['water_trucks']} water trucks and {plan['pool']['med_teams']} "
                        f"medical teams across {len(active)} missions; unmet: {plan['unmet_trucks']} trucks, "
                        f"{plan['unmet_teams']} teams")
        except Exception:
            log("quartermaster", traceback.format_exc())
        if once:
            return
        beat()
        time.sleep(every)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("agent", choices=["scout", "analyst", "narrator", "herald", "checker", "judge",
                                      "corroborator", "sentinel", "warden", "quartermaster"])
    ap.add_argument("--role", choices=["seismologist", "meteorologist", "spaceweather"])
    ap.add_argument("--sample", action="store_true", help="use bundled offline data")
    ap.add_argument("--every", type=int, default=None, help="seconds between cycles")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    global AGENT_NAME
    AGENT_NAME = a.role if a.agent == "checker" and a.role else a.agent
    crew_start()
    if a.agent == "scout":
        run_scout(a.sample, a.every or 60, a.once)
    elif a.agent == "analyst":
        run_analyst(a.every or 5, a.once)
    elif a.agent == "narrator":
        run_narrator(a.every or 5, a.once)
    elif a.agent == "herald":
        run_herald(a.sample, a.every or 30, a.once)
    elif a.agent == "checker":
        if not a.role:
            ap.error("checker needs --role")
        run_checker(a.role, a.every or 5, a.once)
    elif a.agent == "judge":
        run_judge(a.every or 5, a.once)
    elif a.agent == "corroborator":
        run_corroborator(a.sample, a.every or 90, a.once)
    elif a.agent == "sentinel":
        run_sentinel(a.sample, a.every or 120, a.once)
    elif a.agent == "warden":
        run_warden(a.sample, a.every or 20, a.once)
    else:
        run_quartermaster(a.sample, a.every or 30, a.once)


if __name__ == "__main__":
    sys.exit(main())
