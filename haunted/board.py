"""Supabase: the public board the globe reads. Falls back to a local JSON file if not configured."""
from __future__ import annotations

import json
import os
import pathlib
import threading

from dotenv import load_dotenv

load_dotenv()
LOCAL = pathlib.Path(__file__).resolve().parent.parent / "board_local.json"
_lock = threading.Lock()
_sb = None

HAUNT_COLS = ("id", "kind", "title", "lat", "lon", "severity", "status",
              "verdict", "story", "first_seen")


def client():
    global _sb
    if _sb is None and os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        from supabase import create_client
        _sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _sb


def mode() -> str:
    return "supabase" if client() else "local file"


def _local() -> dict:
    if LOCAL.exists():
        try:
            return json.loads(LOCAL.read_text())
        except json.JSONDecodeError:
            pass
    return {"haunts": {}, "chatter": []}


def _save_local(d: dict) -> None:
    tmp = LOCAL.with_suffix(".tmp")
    tmp.write_text(json.dumps(d))
    tmp.replace(LOCAL)


def mirror_many(states: list) -> None:
    """Copy actors' current state into the haunts table (one batched upsert)."""
    from .feeds import iso, now
    if not states:
        return
    rows = [{**{c: getattr(s, c) for c in HAUNT_COLS}, "updated_at": iso(now())} for s in states]
    sb = client()
    if sb:
        for i in range(0, len(rows), 200):
            sb.table("haunts").upsert(rows[i:i + 200]).execute()
        return
    with _lock:
        d = _local()
        for r in rows:
            d["haunts"][r["id"]] = r
        _save_local(d)


def mirror_haunt(state) -> None:
    mirror_many([state])


def log_chatter(sender: str, haunt_id: str | None, message: str) -> None:
    from .feeds import iso, now
    row = {"sender": sender, "haunt_id": haunt_id, "message": message[:1000]}
    sb = client()
    if sb:
        sb.table("chatter").insert(row).execute()
        return
    with _lock:
        d = _local()
        d["chatter"] = (d["chatter"] + [{**row, "created_at": iso(now())}])[-200:]
        _save_local(d)


def load_haunts() -> list[dict]:
    sb = client()
    if sb:
        return sb.table("haunts").select("*").execute().data or []
    return list(_local()["haunts"].values())


def load_chatter(limit: int = 25) -> list[dict]:
    sb = client()
    if sb:
        return (sb.table("chatter").select("*").order("id", desc=True).limit(limit)
                .execute().data or [])
    return list(reversed(_local()["chatter"][-limit:]))
