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
              "verdict", "story", "first_seen", "consensus")
OPTIONAL_COLS = ("consensus",)   # added in v3; skipped if the Supabase column doesn't exist yet
_missing_cols: set[str] = set()


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
    rows = [{**{c: getattr(s, c, "") for c in HAUNT_COLS if c not in _missing_cols},
             "updated_at": iso(now())} for s in states]
    sb = client()
    if sb:
        for i in range(0, len(rows), 200):
            try:
                sb.table("haunts").upsert(rows[i:i + 200]).execute()
            except Exception as exc:
                bad = [c for c in OPTIONAL_COLS if c in str(exc)]
                if not bad:
                    raise
                _missing_cols.update(bad)   # old schema: drop new columns and retry
                print(f"[board] Supabase haunts table lacks {bad}; run the ALTER in supabase.sql", flush=True)
                chunk = [{k: v for k, v in r.items() if k not in bad} for r in rows[i:i + 200]]
                sb.table("haunts").upsert(chunk).execute()
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


# ---------------------------------------------------------------- newsroom tables
def log_factcheck(row: dict) -> None:
    """row: haunt_id, article_url, headline, outlet, checker, claim, verdict, explanation"""
    from .feeds import iso, now
    sb = client()
    if sb:
        sb.table("factchecks").insert(row).execute()
        return
    with _lock:
        d = _local()
        d.setdefault("factchecks", [])
        d["factchecks"] = (d["factchecks"] + [{**row, "created_at": iso(now())}])[-400:]
        _save_local(d)


def mirror_outlet(row: dict) -> None:
    """row: outlet, confirmed, plausible, mismatched, implausible, unverifiable, score, score_sd"""
    from .feeds import iso, now
    row = {**row, "updated_at": iso(now())}
    sb = client()
    if sb:
        sb.table("outlets").upsert(row).execute()
        return
    with _lock:
        d = _local()
        d.setdefault("outlets", {})[row["outlet"]] = row
        _save_local(d)


def load_factchecks(limit: int = 60) -> list[dict]:
    sb = client()
    if sb:
        return (sb.table("factchecks").select("*").order("id", desc=True).limit(limit)
                .execute().data or [])
    return list(reversed(_local().get("factchecks", [])[-limit:]))


def load_outlets() -> list[dict]:
    sb = client()
    if sb:
        return sb.table("outlets").select("*").execute().data or []
    return list(_local().get("outlets", {}).values())


# ---------------------------------------------------------------- county alerts (v3)
def replace_county_alerts(rows: list[dict]) -> None:
    """Upsert the current alerts and delete ones that are no longer active."""
    from .feeds import iso, now
    stamp = iso(now())
    cols = ("id", "fips", "state", "county", "event", "severity", "sev_rank", "headline",
            "expires", "lat", "lon", "linked_haunt")
    rows = [{**{c: r.get(c) for c in cols}, "updated_at": stamp} for r in rows]
    sb = client()
    if sb:
        for i in range(0, len(rows), 300):
            sb.table("county_alerts").upsert(rows[i:i + 300]).execute()
        sb.table("county_alerts").delete().lt("updated_at", stamp).execute()
        return
    with _lock:
        d = _local()
        d["county_alerts"] = rows
        _save_local(d)


def load_county_alerts() -> list[dict]:
    sb = client()
    if sb:
        out, start = [], 0
        while True:
            chunk = sb.table("county_alerts").select("*").range(start, start + 999).execute().data or []
            out += chunk
            if len(chunk) < 1000:
                return out
            start += 1000
    return _local().get("county_alerts", [])


# ---------------------------------------------------------------- warning system (v4)
DEFAULT_PLACES = [
    {"id": "san-francisco", "name": "San Francisco, CA", "lat": 37.77, "lon": -122.42, "coastal": True},
    {"id": "tokyo", "name": "Tokyo, Japan", "lat": 35.68, "lon": 139.69, "coastal": True},
    {"id": "hualien", "name": "Hualien, Taiwan", "lat": 23.99, "lon": 121.60, "coastal": True},
    {"id": "mumbai", "name": "Mumbai, India", "lat": 19.08, "lon": 72.88, "coastal": True},
    {"id": "lagos", "name": "Lagos, Nigeria", "lat": 6.52, "lon": 3.38, "coastal": True},
    {"id": "anchorage", "name": "Anchorage, AK", "lat": 61.22, "lon": -149.90, "coastal": True},
    {"id": "honolulu", "name": "Honolulu, HI", "lat": 21.31, "lon": -157.86, "coastal": True},
]


def load_places() -> list[dict]:
    sb = client()
    if sb:
        rows = sb.table("places").select("*").execute().data or []
        if not rows:
            sb.table("places").upsert(DEFAULT_PLACES).execute()
            rows = DEFAULT_PLACES
        return rows
    d = _local()
    if not d.get("places"):
        with _lock:
            d["places"] = {p["id"]: p for p in DEFAULT_PLACES}
            _save_local(d)
    return list(d["places"].values())


PLACE_OPTIONAL = ("email", "shared")   # v5 columns; skipped if not yet in Supabase


def add_place(name: str, lat: float, lon: float, coastal: bool, email: str | None = None,
              pid: str | None = None, shared: bool = False) -> str:
    import re
    pid = pid or (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "place")
    row = {"id": pid, "name": name, "lat": lat, "lon": lon, "coastal": coastal,
           "email": (email or None), "shared": shared}
    sb = client()
    if sb:
        try:
            sb.table("places").upsert(row).execute()
        except Exception as exc:
            if not any(c in str(exc) for c in PLACE_OPTIONAL):
                raise
            print("[board] places table lacks email/shared columns; run the v5 ALTER in supabase.sql", flush=True)
            sb.table("places").upsert({k: v for k, v in row.items() if k not in PLACE_OPTIONAL}).execute()
        return pid
    with _lock:
        d = _local()
        d.setdefault("places", {})[pid] = row
        _save_local(d)
    return pid


def get_place(pid: str) -> dict | None:
    sb = client()
    if sb:
        rows = sb.table("places").select("*").eq("id", pid).execute().data or []
        return rows[0] if rows else None
    return _local().get("places", {}).get(pid)


def clear_email(pid: str) -> None:
    sb = client()
    if sb:
        try:
            sb.table("places").update({"email": None}).eq("id", pid).execute()
        except Exception:
            pass
        return
    with _lock:
        d = _local()
        if pid in d.get("places", {}):
            d["places"][pid]["email"] = None
            _save_local(d)


def remove_place(pid: str) -> None:
    sb = client()
    if sb:
        sb.table("places").delete().eq("id", pid).execute()
        sb.table("warnings").delete().eq("place_id", pid).execute()
        return
    with _lock:
        d = _local()
        d.get("places", {}).pop(pid, None)
        d["warnings"] = [w for w in d.get("warnings", []) if w["place_id"] != pid]
        _save_local(d)


def replace_warnings(place_id: str, rows: list[dict]) -> None:
    from .feeds import iso, now
    stamp = iso(now())
    rows = [{**r, "id": f"{place_id}|{r['key']}", "place_id": place_id, "updated_at": stamp} for r in rows]
    sb = client()
    if sb:
        if rows:
            sb.table("warnings").upsert(rows).execute()
        sb.table("warnings").delete().eq("place_id", place_id).lt("updated_at", stamp).execute()
        return
    with _lock:
        d = _local()
        d["warnings"] = [w for w in d.get("warnings", []) if w["place_id"] != place_id] + rows
        _save_local(d)


def load_warnings() -> list[dict]:
    sb = client()
    if sb:
        return sb.table("warnings").select("*").execute().data or []
    return _local().get("warnings", [])


# ---------------------------------------------------------------- relief missions (v7)
def mirror_mission(row: dict) -> None:
    """row: id, place_id, place_name, hazard, level, status, tasks_json, resources_json, needs_json"""
    from .feeds import iso, now
    row = {**row, "updated_at": iso(now())}
    sb = client()
    if sb:
        sb.table("missions").upsert(row).execute()
        return
    with _lock:
        d = _local()
        d.setdefault("missions", {})[row["id"]] = row
        _save_local(d)


def load_missions() -> list[dict]:
    sb = client()
    if sb:
        return sb.table("missions").select("*").execute().data or []
    return list(_local().get("missions", {}).values())


# ---------------------------------------------------------------- drills (v8)
def add_drill(row: dict) -> None:
    from .feeds import iso, now
    row = {**row, "active": True, "created_at": iso(now())}
    sb = client()
    if sb:
        sb.table("drills").upsert(row).execute()
        return
    with _lock:
        d = _local()
        d.setdefault("drills", {})[row["id"]] = row
        _save_local(d)


def load_drills() -> list[dict]:
    sb = client()
    if sb:
        try:
            return sb.table("drills").select("*").eq("active", True).execute().data or []
        except Exception:
            return []
    return [x for x in _local().get("drills", {}).values() if x.get("active")]


def end_drills() -> None:
    sb = client()
    if sb:
        sb.table("drills").update({"active": False}).eq("active", True).execute()
        return
    with _lock:
        d = _local()
        for x in d.get("drills", {}).values():
            x["active"] = False
        _save_local(d)


# ---------------------------------------------------------------- airports (v9)
def mirror_airports(rows: list[dict]) -> None:
    import json as _j
    from .feeds import iso, now
    rows = [{"icao": r["icao"], "data_json": _j.dumps(r), "updated_at": iso(now())} for r in rows]
    sb = client()
    if sb:
        if rows:
            sb.table("airports").upsert(rows).execute()
        return
    with _lock:
        d = _local()
        for r in rows:
            d.setdefault("airports", {})[r["icao"]] = r
        _save_local(d)


def load_airports() -> list[dict]:
    import json as _j
    sb = client()
    if sb:
        try:
            rows = sb.table("airports").select("*").execute().data or []
        except Exception:
            rows = []
    else:
        rows = list(_local().get("airports", {}).values())
    return [_j.loads(r["data_json"]) for r in rows]


# ---------------------------------------------------------------- crew status (v10)
def mirror_agent(row: dict) -> None:
    sb = client()
    if sb:
        try:
            sb.table("agents").upsert(row).execute()
        except Exception:
            pass
        return
    with _lock:
        d = _local()
        d.setdefault("agents", {})[row["name"]] = row
        _save_local(d)


def load_agents() -> list[dict]:
    sb = client()
    if sb:
        try:
            return sb.table("agents").select("*").execute().data or []
        except Exception:
            return []
    return list(_local().get("agents", {}).values())
