"""Airport Watch: METAR/SIGMET physics for airports (aviationweather.gov, free) + nearby traffic
(OpenSky Network, free, rate-limited). Demo estimates, not for operational use."""
from __future__ import annotations

import math
import re

import requests

from .physics import haversine_km

AWC = "https://aviationweather.gov/api/data"
OPENSKY = "https://opensky-network.org/api/states/all"
UA = {"User-Agent": "HauntedEarth/0.1 (hackathon demo; GitHub GalacticBobster)"}

# ICAO: (name, lat, lon, elevation ft, approx. TRUE runway headings, coastal)
AIRPORTS = {
    "KSFO": ("San Francisco Intl", 37.619, -122.375, 13, [28, 208, 118, 298], True),
    "KSAN": ("San Diego Intl", 32.733, -117.190, 17, [100, 280], True),
    "KLAX": ("Los Angeles Intl", 33.942, -118.408, 125, [83, 263], True),
    "KSEA": ("Seattle-Tacoma", 47.449, -122.309, 433, [180, 360], True),
    "KDEN": ("Denver Intl", 39.856, -104.674, 5434, [0, 180, 90, 270], False),
    "KORD": ("Chicago O'Hare", 41.978, -87.905, 672, [90, 270, 40, 220], False),
    "KDTW": ("Detroit Metro", 42.212, -83.353, 645, [33, 213, 85, 265], False),
    "KJFK": ("New York JFK", 40.640, -73.779, 13, [31, 211, 121, 301], True),
    "KMIA": ("Miami Intl", 25.793, -80.291, 8, [85, 265, 115, 295], True),
    "PHNL": ("Honolulu", 21.319, -157.922, 13, [80, 260, 50, 230], True),
    "PANC": ("Anchorage", 61.174, -149.996, 152, [88, 268, 165, 345], True),
    "RJTT": ("Tokyo Haneda", 35.552, 139.780, 35, [150, 330, 33, 213], True),
    "RCTP": ("Taipei Taoyuan", 25.077, 121.233, 106, [53, 233], True),
    "RPLL": ("Manila NAIA", 14.509, 121.020, 75, [60, 240, 135, 315], True),
    "WSSS": ("Singapore Changi", 1.359, 103.989, 22, [22, 202], True),
    "VABB": ("Mumbai CSMIA", 19.089, 72.868, 39, [90, 270, 140, 320], True),
    "OMDB": ("Dubai Intl", 25.253, 55.364, 62, [122, 302], True),
    "EGLL": ("London Heathrow", 51.470, -0.454, 83, [90, 270], False),
    "YSSY": ("Sydney", -33.946, 151.177, 21, [167, 347, 77, 257], True),
}


def place_id(icao: str) -> str:
    return f"apt-{icao.lower()}"


def icao_of(pid: str) -> str | None:
    return pid[4:].upper() if pid.startswith("apt-") else None


# ------------------------------------------------------------------ fetch
def fetch_metars(icaos: list[str]) -> dict[str, dict]:
    r = requests.get(f"{AWC}/metar", params={"ids": ",".join(icaos), "format": "json"}, headers=UA, timeout=20)
    r.raise_for_status()
    out = {}
    for m in r.json() or []:
        out.setdefault(m.get("icaoId"), m)          # newest first
    return out


def fetch_sigmets() -> list[dict]:
    out = []
    for ep in ("airsigmet", "isigmet"):
        try:
            r = requests.get(f"{AWC}/{ep}", params={"format": "json"}, headers=UA, timeout=20)
            r.raise_for_status()
            out += r.json() or []
        except Exception:
            pass
    return out


def fetch_traffic(lat: float, lon: float, km: float = 60) -> dict:
    d_lat, d_lon = km / 110.57, km / (111.32 * max(0.2, math.cos(math.radians(lat))))
    r = requests.get(OPENSKY, params={"lamin": lat - d_lat, "lamax": lat + d_lat,
                                      "lomin": lon - d_lon, "lomax": lon + d_lon}, headers=UA, timeout=8)
    r.raise_for_status()
    st = (r.json() or {}).get("states") or []
    ground = sum(1 for s in st if s[8])
    return {"airborne": len(st) - ground, "on_ground": ground}


# ------------------------------------------------------------------ physics
def _num(x, default=None):
    try:
        return float(str(x).replace("+", ""))
    except (TypeError, ValueError):
        return default


def ceiling_ft(m: dict) -> float | None:
    """Lowest BKN/OVC/VV layer base (ft AGL)."""
    bases = [_num(c.get("base")) for c in (m.get("clouds") or [])
             if c.get("cover") in ("BKN", "OVC", "VV", "OVX") and _num(c.get("base")) is not None]
    vv = re.search(r"\bVV(\d{3})\b", m.get("rawOb") or "")
    if vv:
        bases.append(int(vv.group(1)) * 100)
    return min(bases) if bases else None


def flight_category(ceil: float | None, vis_sm: float | None) -> str:
    """FAA categories: LIFR <500 ft or <1 sm; IFR 500-<1000 ft or 1-<3 sm; MVFR 1000-3000 ft or 3-5 sm."""
    c = 1e9 if ceil is None else ceil
    v = 99 if vis_sm is None else vis_sm
    if c < 500 or v < 1:
        return "LIFR"
    if c < 1000 or v < 3:
        return "IFR"
    if c <= 3000 or v <= 5:
        return "MVFR"
    return "VFR"


def best_runway(wdir: float | None, wspd: float, runways: list[int]) -> tuple[int, float, float]:
    """(heading, crosswind kt, headwind kt) for the runway with the least crosswind and a headwind."""
    if wdir is None or not runways:
        return (runways[0] if runways else 0), wspd if wdir is None else 0.0, 0.0
    best = None
    for h in runways:
        ang = math.radians((wdir - h + 540) % 360 - 180)
        xw, hw = abs(wspd * math.sin(ang)), wspd * math.cos(ang)
        key = (xw, -hw)
        if best is None or key < best[0]:
            best = (key, h, xw, hw)
    return best[1], best[2], best[3]


def density_altitude(elev_ft: float, temp_c: float | None, altim_hpa: float | None) -> float | None:
    if temp_c is None:
        return None
    pa = elev_ft + (1013.25 - (altim_hpa or 1013.25)) * 27.0   # ~27 ft per hPa near sea level
    isa = 15.0 - 1.98 * pa / 1000.0
    return pa + 118.8 * (temp_c - isa)


def _flat_points(coords) -> list[tuple[float, float]]:
    """Accept {'lat','lon'} dicts, [lon, lat] pairs (GeoJSON order), or nested rings."""
    pts = []
    for c in coords or []:
        if isinstance(c, dict):
            la, lo = _num(c.get("lat")), _num(c.get("lon"))
            if la is not None and lo is not None:
                pts.append((la, lo))
        elif isinstance(c, (list, tuple)) and c and isinstance(c[0], (list, tuple, dict)):
            pts += _flat_points(c)
        elif isinstance(c, (list, tuple)) and len(c) >= 2:
            lo, la = _num(c[0]), _num(c[1])
            if la is not None and lo is not None:
                pts.append((la, lo))
    return pts


def point_in_poly(lat: float, lon: float, coords) -> bool:
    try:
        pts = _flat_points(coords)
    except Exception:
        return False
    inside, n = False, len(pts)
    if n < 3:
        return False
    for i in range(n):
        (y1, x1), (y2, x2) = pts[i], pts[(i + 1) % n]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-9) + x1:
            inside = not inside
    return inside


def snapshot(icao: str, m: dict | None, sigmets: list[dict], traffic: dict | None) -> dict:
    name, lat, lon, elev, rwys, _ = AIRPORTS.get(icao, (icao, 0, 0, 0, [], False))
    if not m:
        return {"icao": icao, "name": name, "cat": "?", "raw": "no METAR"}
    wdir = None if str(m.get("wdir")).upper() == "VRB" else _num(m.get("wdir"))
    wspd, wgst = _num(m.get("wspd"), 0.0), _num(m.get("wgst"))
    vis = _num(m.get("visib"))
    ceil = ceiling_ft(m)
    cat = flight_category(ceil, vis)
    h, xw, hw = best_runway(wdir, max(wspd, wgst or 0), rwys)
    da = density_altitude(elev, _num(m.get("temp")), _num(m.get("altim")))
    raw = m.get("rawOb") or ""
    hits = []
    for s in sigmets if isinstance(sigmets, list) else []:
        if not isinstance(s, dict):
            continue
        if point_in_poly(lat, lon, s.get("coords") or s.get("geometry") or []):
            hz = (s.get("hazard") or s.get("airSigmetType") or "SIGMET").upper()
            hits.append({"id": str(s.get("airSigmetId") or s.get("isigmetId") or s.get("seriesId") or hz),
                         "hazard": hz, "raw": (s.get("rawAirSigmet") or s.get("rawSigmet") or "")[:240]})
    return {"icao": icao, "name": name, "cat": cat, "ceiling_ft": ceil, "vis_sm": vis,
            "wind": f"{'VRB' if wdir is None else int(wdir):>03}° {int(wspd)} kt" + (f" G{int(wgst)}" if wgst else ""),
            "best_rwy": f"heading {h}° true", "xwind_kt": round(xw, 1),
            "headwind_kt": round(hw, 1), "density_alt_ft": None if da is None else int(da), "elev_ft": elev,
            "ts": bool(re.search(r"\b[+-]?(VC)?TS", raw)), "cb": bool(re.search(r"CB|TCU", raw)),
            "sigmets": hits, "traffic": traffic, "raw": raw}


def aviation_threats(s: dict) -> list[dict]:
    out = []
    if s.get("cat") in ("MVFR", "IFR", "LIFR"):
        lvl = {"MVFR": 1, "IFR": 2, "LIFR": 3}[s["cat"]]
        out.append({"key": "flightcat", "hazard": "flight category", "level": lvl,
                    "headline": f"{s['cat']}: ceiling {int(s['ceiling_ft']) if s.get('ceiling_ft') else 'none'} ft, "
                                f"visibility {s.get('vis_sm')} sm",
                    "detail": "FAA flight categories from METAR ceiling and visibility. IFR/LIFR cut arrival rates "
                              "(wider spacing, instrument approaches) and can trigger ground delays."})
    xw = s.get("xwind_kt") or 0
    if xw >= 20:
        lvl = 3 if xw >= 33 else 2 if xw >= 25 else 1
        out.append({"key": "xwind", "hazard": "crosswind", "level": lvl,
                    "headline": f"Crosswind {xw:.0f} kt even on the best runway ({s['best_rwy']})",
                    "detail": f"Wind {s['wind']}: crosswind = V·sin(θ), headwind = V·cos(θ) for each runway; "
                              "gusts used if present. Many airliners demonstrate ~30-38 kt crosswind limits."})
    if s.get("ts"):
        out.append({"key": "ts", "hazard": "thunderstorm", "level": 3,
                    "headline": "Thunderstorm at or near the field: ramp lightning holds likely",
                    "detail": f"METAR: {s['raw']}. Ground crews typically stop ramp work with lightning within ~8-10 km."})
    elif s.get("cb"):
        out.append({"key": "ts", "hazard": "thunderstorm", "level": 1,
                    "headline": "Cumulonimbus / towering cumulus reported", "detail": f"METAR: {s['raw']}"})
    da, elev = s.get("density_alt_ft"), s.get("elev_ft") or 0
    if da is not None and da - elev >= 3000:
        lvl = 2 if da - elev >= 5000 else 1
        out.append({"key": "da", "hazard": "density altitude", "level": lvl,
                    "headline": f"Density altitude {da:,} ft ({da - elev:+,} ft vs field)",
                    "detail": "Hot/low-pressure air: longer take-off rolls, reduced climb; possible payload limits."})
    for h in s.get("sigmets") or []:
        hz = h["hazard"]
        lvl = 3 if ("ASH" in hz or hz == "VA") else 2 if ("CONV" in hz or "TS" in hz) else 1
        out.append({"key": f"sigmet:{h['id']}", "hazard": "sigmet", "level": lvl,
                    "headline": f"Airport inside an active {hz} SIGMET/AIRMET area",
                    "detail": h["raw"] or "Official in-flight hazard advisory polygon contains the airport."})
    return out


def alternates(icao: str, km: float, metars: dict[str, dict]) -> list[dict]:
    """Other listed airports within km whose current METAR is VFR/MVFR with crosswind < 25 kt."""
    _, lat, lon, *_ = AIRPORTS[icao]
    out = []
    for other, (name, la, lo, *_r) in AIRPORTS.items():
        if other == icao:
            continue
        d = haversine_km(lat, lon, la, lo)
        if d > km:
            continue
        s = snapshot(other, metars.get(other), [], None)
        out.append({"icao": other, "name": name, "km": round(d), "cat": s["cat"], "xwind": s.get("xwind_kt"),
                    "usable": s["cat"] in ("VFR", "MVFR") and (s.get("xwind_kt") or 0) < 25})
    return sorted(out, key=lambda a: (not a["usable"], a["km"]))


OPS_CHECKLIST = {
    "flight category": ["Expect reduced arrival rate; consider ground delay program", "Check alternates' forecasts (TAF)",
                        "Extra fuel for holding/diversion"],
    "crosswind": ["Confirm runway in use vs crosswind limits per fleet", "Brief crews on gusts/wind shear",
                  "Consider single-runway ops capacity"],
    "thunderstorm": ["Ramp lightning hold procedures", "Plan arrival/departure gaps; expect diversions",
                     "Secure ground equipment against gust fronts"],
    "density altitude": ["Check take-off performance / payload limits", "Prefer cooler departure times"],
    "sigmet": ["Re-route around the SIGMET polygon", "Volcanic ash: avoid entirely; inspect engines after exposure"],
    "earthquake": ["Runway, taxiway and lighting inspection before reopening", "Check tower and navaid integrity",
                   "Coordinate with civil aviation authority NOTAMs"],
    "cyclone": ["Secure/evacuate aircraft per wind limits", "Plan last departures before tropical-storm-force winds"],
    "tsunami": ["Coastal airports: move people and aircraft to high ground if warned"],
}
