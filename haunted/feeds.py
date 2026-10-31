"""Scouts' eyes: open hazard feeds, normalized to one event shape.

Event = {id, kind, title, lat, lon, severity (0-1), status (awake/fading/closed), seen_at, extra}
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import requests

UA = {"User-Agent": "HauntedEarth/0.1 (hackathon demo)"}
USGS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
EONET = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=20&limit=150"
SWPC_KP = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
SAMPLE = pathlib.Path(__file__).parent / "sample_data.json"

EONET_KIND = {
    "wildfires": "wildfire", "volcanoes": "volcano", "severeStorms": "storm",
    "floods": "flood", "seaLakeIce": "ice", "dustHaze": "dust", "landslides": "landslide",
    "snow": "snow", "drought": "drought", "tempExtremes": "heat",
}
BASE_SEVERITY = {"wildfire": 0.45, "volcano": 0.7, "storm": 0.6, "flood": 0.55, "ice": 0.25}


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _get(url: str) -> object:
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    return r.json()


def _quake_status(age_h: float) -> str:
    return "awake" if age_h < 6 else "fading" if age_h < 24 else "closed"


def parse_usgs(data: dict, t_now: dt.datetime) -> list[dict]:
    out = []
    for f in data.get("features", []):
        p, g = f["properties"], f["geometry"]["coordinates"]
        mag = p.get("mag")
        if mag is None:
            continue
        t = dt.datetime.fromtimestamp(p["time"] / 1000, dt.timezone.utc)
        age_h = (t_now - t).total_seconds() / 3600
        out.append({
            "id": f"eq-{f['id']}", "kind": "earthquake",
            "title": f"M{mag:.1f} {p.get('place') or 'unknown place'}",
            "lat": g[1], "lon": g[0],
            "severity": max(0.05, min(1.0, (mag - 2.5) / 5.0)),
            "status": _quake_status(age_h), "seen_at": iso(t),
            "extra": {"mag": mag, "depth_km": round(g[2], 1), "url": p.get("url"), "event_time": iso(t)},
        })
    return out


def _last_point(geoms: list[dict]) -> tuple[float, float, dict] | None:
    for g in reversed(geoms or []):
        c = g.get("coordinates")
        if g.get("type") == "Point" and c:
            return c[1], c[0], g
        if g.get("type") == "Polygon" and c:
            ring = c[0]
            return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring), g
    return None


def parse_eonet(data: dict) -> list[dict]:
    out = []
    for e in data.get("events", []):
        cats = e.get("categories") or [{}]
        kind = EONET_KIND.get(cats[0].get("id"), cats[0].get("id") or "event")
        pt = _last_point(e.get("geometry"))
        if not pt:
            continue
        lat, lon, g = pt
        sev = BASE_SEVERITY.get(kind, 0.4)
        mv = g.get("magnitudeValue")
        if kind == "storm" and mv:  # knots
            sev = max(0.3, min(1.0, float(mv) / 140.0))
        out.append({
            "id": f"eo-{e['id']}", "kind": kind, "title": e.get("title", kind),
            "lat": lat, "lon": lon, "severity": sev,
            "status": "closed" if e.get("closed") else "awake",
            "seen_at": g.get("date") or iso(now()),
            "extra": {"category": cats[0].get("title"), "magnitude": mv,
                      "magnitude_unit": g.get("magnitudeUnit"),
                      "source": (e.get("sources") or [{}])[0].get("url")},
        })
    return out


def parse_kp(data: list) -> list[dict]:
    """SWPC Kp product: list-of-lists with a header row, or list-of-dicts (newer format)."""
    if not data:
        return []
    last = data[-1]
    if isinstance(last, dict):
        kp = float(last.get("Kp", last.get("kp_index", last.get("kp", 0))))
        t = last.get("time_tag")
    else:
        hdr = data[0]
        kp = float(last[hdr.index("Kp")] if "Kp" in hdr else last[1])
        t = last[0]
    from .physics import aurora_boundary_lat
    blat = aurora_boundary_lat(kp)
    status = "awake" if kp >= 5 else "fading" if kp >= 4 else "closed"
    return [{
        "id": "aurora-north", "kind": "aurora",
        "title": f"Aurora watch (Kp {kp:.1f})",
        "lat": blat, "lon": -100.0,          # drawn over North America at the oval's edge
        "severity": max(0.1, min(1.0, kp / 9.0)), "status": status,
        "seen_at": t or iso(now()), "extra": {"kp": kp, "boundary_lat": blat},
    }]


def fetch_all(sample: bool = False) -> tuple[list[dict], list[str]]:
    """Return (events, errors). sample=True uses bundled offline data."""
    t_now = now()
    if sample:
        d = json.loads(SAMPLE.read_text())
        # shift sample quake times so they look fresh
        for f in d["usgs"]["features"]:
            f["properties"]["time"] = int((t_now.timestamp() - f["properties"]["age_h"] * 3600) * 1000)
        return parse_usgs(d["usgs"], t_now) + parse_eonet(d["eonet"]) + parse_kp(d["kp"]), []

    events, errors = [], []
    for name, url, parse in (
        ("USGS", USGS, lambda d: parse_usgs(d, t_now)),
        ("EONET", EONET, parse_eonet),
        ("SWPC", SWPC_KP, parse_kp),
    ):
        try:
            events += parse(_get(url))
        except Exception as exc:  # one bad feed must not stop the others
            errors.append(f"{name}: {exc}")
    return events, errors
