"""Drills: clearly-labelled hypothetical events that flow through the real pipeline
(scout -> analyst -> warden -> quartermaster), plus the Quartermaster's resource optimizer."""
from __future__ import annotations

import datetime as dt
import json
import math
import os

SCENARIOS = {
    "Earthquake": {"kind": "earthquake"},
    "Typhoon / hurricane": {"kind": "storm"},
}


def drill_events(rows: list[dict]) -> list[dict]:
    """Turn active drill rows into scout events (ids 'drill-...')."""
    out = []
    now = dt.datetime.now(dt.timezone.utc)
    for d in rows:
        if not d.get("active", True):
            continue
        t0 = d.get("created_at") or now.isoformat()
        if d["kind"] == "earthquake":
            mag, depth = float(d.get("mag") or 7.0), float(d.get("depth_km") or 15)
            out.append({"id": f"drill-{d['id']}", "kind": "earthquake",
                        "title": f"DRILL: M{mag:.1f} near {d.get('label') or 'target'}",
                        "lat": d["lat"], "lon": d["lon"], "severity": max(0.05, min(1.0, (mag - 2.5) / 5)),
                        "status": "awake", "seen_at": t0,
                        "extra": {"mag": mag, "depth_km": depth, "event_time": t0, "drill": True}})
        else:
            v = float(d.get("vmax_kt") or 120)
            hdg, spd = math.radians(float(d.get("heading_deg") or 300)), float(d.get("speed_kmh") or 20)
            track = []
            for k in (3, 2, 1, 0):          # positions 6 h apart, ending at the current centre
                back = spd * 6 * k
                la = d["lat"] - back * math.cos(hdg) / 110.57
                lo = d["lon"] - back * math.sin(hdg) / (111.32 * math.cos(math.radians(d["lat"])))
                track.append([la, lo, (now - dt.timedelta(hours=6 * k)).isoformat()])
            out.append({"id": f"drill-{d['id']}", "kind": "storm",
                        "title": f"DRILL: {v:.0f}-kt cyclone approaching {d.get('label') or 'target'}",
                        "lat": d["lat"], "lon": d["lon"], "severity": max(0.3, min(1.0, v / 140)),
                        "status": "awake", "seen_at": t0,
                        "extra": {"magnitude": v, "magnitude_unit": "kts", "track": track, "drill": True}})
    return out


def start_position(target_lat: float, target_lon: float, hours_out: float, heading_deg: float,
                   speed_kmh: float) -> tuple[float, float]:
    """Where a storm must be now to reach the target in `hours_out` on this heading."""
    dist = speed_kmh * hours_out
    h = math.radians(heading_deg)
    la = target_lat - dist * math.cos(h) / 110.57
    lo = target_lon - dist * math.sin(h) / (111.32 * math.cos(math.radians(target_lat)))
    return la, lo


# ---------------------------------------------------------------- resource optimizer
EXPOSED = {1: 0.01, 2: 0.05, 3: 0.15}       # illustrative share of population needing help
MED_PER_100K = {"earthquake": 2.0, "tsunami": 2.0, "cyclone": 1.5, "heat": 0.6, "wind": 0.3, "official": 0.5}


def allocate(missions: list[dict], pops: dict[str, float]) -> dict:
    """Greedy allocation of scarce water trucks and medical teams across active missions.

    Objective: maximise sum_i w_i * min(1, alloc_i / need_i) with w_i = level^2 (warnings weigh 9x
    advisories). Each unit goes to the mission with the largest marginal weighted coverage gain;
    for this separable concave objective, the greedy choice is optimal.
    """
    trucks = int(os.getenv("WATER_TRUCKS", "25"))
    teams = int(os.getenv("MED_TEAMS", "8"))
    rows = []
    for m in missions:
        lvl = int(m.get("level") or 1)
        people = pops.get(m["place_id"], 2e5) * EXPOSED.get(lvl, 0.01)
        gap = any(t["title"] == "Flag medical capacity gap" for t in json.loads(m.get("tasks_json") or "[]"))
        rows.append({"mission": m["id"], "place": m["place_name"], "hazard": m["hazard"], "level": lvl,
                     "people_at_risk": int(people),
                     "trucks_need": math.ceil(people * 15 * 3 / 10000),
                     "teams_need": max(1, math.ceil(people / 1e5 * MED_PER_100K.get(m["hazard"], 0.5) * (2 if gap else 1))),
                     "trucks": 0, "teams": 0, "w": lvl ** 2})

    def give(pool: int, need_key: str, got_key: str) -> None:
        for _ in range(pool):
            best, gain = None, 0.0
            for r in rows:
                if r[got_key] < r[need_key]:
                    g = r["w"] / r[need_key]
                    if g > gain:
                        best, gain = r, g
            if best is None:
                return
            best[got_key] += 1

    give(trucks, "trucks_need", "trucks")
    give(teams, "teams_need", "teams")
    for r in rows:
        r["water_coverage"] = round(100 * r["trucks"] / r["trucks_need"]) if r["trucks_need"] else 100
        r["medical_coverage"] = round(100 * r["teams"] / r["teams_need"]) if r["teams_need"] else 100
    rows.sort(key=lambda r: (-r["level"], -r["people_at_risk"]))
    return {"pool": {"water_trucks": trucks, "med_teams": teams}, "rows": rows,
            "unmet_trucks": sum(r["trucks_need"] - r["trucks"] for r in rows),
            "unmet_teams": sum(r["teams_need"] - r["teams"] for r in rows)}
