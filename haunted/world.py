"""More eyes on the world: GDACS (UN/EU global alerts), JMA (Japan), EMSC (Europe/Africa/Med),
and NWS county-level alerts (US). All public, no keys.
"""
from __future__ import annotations

import datetime as dt
import re

import requests

UA = {"User-Agent": "HauntedEarth/0.1 (hackathon demo; contact via GitHub GalacticBobster)",
      "Accept": "application/geo+json, application/json"}
GDACS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP"
JMA = "https://www.jma.go.jp/bosai/quake/data/list.json"
EMSC = "https://www.seismicportal.eu/fdsnws/event/1/query"
NWS = "https://api.weather.gov/alerts/active"

GDACS_KIND = {"EQ": "earthquake", "TC": "storm", "FL": "flood", "VO": "volcano",
              "DR": "drought", "WF": "wildfire"}
ALERT_SEV = {"green": 0.3, "orange": 0.6, "red": 0.9}

# US state FIPS -> postal code (for SAME county codes 0SSCCC)
FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
        "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
        "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
        "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
        "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
        "54": "WV", "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI"}
NWS_SEV = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}


def _get(url: str, **params):
    r = requests.get(url, headers=UA, params=params or None, timeout=20)
    r.raise_for_status()
    return r.json()


def _iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def _parse_time(s: str) -> dt.datetime | None:
    if not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def _centroid(geom: dict | None) -> tuple[float, float] | None:
    if not geom:
        return None
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Point":
        return c[1], c[0]
    if t == "Polygon":
        ring = c[0]
    elif t == "MultiPolygon":
        ring = c[0][0]
    else:
        return None
    return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)


# ------------------------------------------------------------------ GDACS
def parse_gdacs(data: dict) -> tuple[list[dict], list[dict]]:
    """Returns (haunt_events for non-quake hazards, quake_reports for the Corroborator)."""
    events, quakes = [], []
    for f in data.get("features", []):
        p = f.get("properties", {})
        if str(p.get("iscurrent", "true")).lower() == "false":
            continue
        last = _parse_time(p.get("todate") or p.get("fromdate") or "")
        if last and (dt.datetime.now(dt.timezone.utc) - last).days > int(__import__("os").getenv("HAUNT_MAX_DAYS", "2")):
            continue
        g = f.get("geometry") or {}
        if g.get("type") != "Point":
            continue                      # GDACS also ships footprint polygons; points are enough
        lat, lon = g["coordinates"][1], g["coordinates"][0]
        kind = GDACS_KIND.get(p.get("eventtype"), "event")
        level = (p.get("alertlevel") or "green").lower()
        sev = p.get("severitydata") or {}
        if kind == "earthquake":
            quakes.append({"agency": "GDACS", "mag": float(sev.get("severity") or 0),
                           "lat": lat, "lon": lon, "depth_km": None,
                           "time": p.get("fromdate"), "ref": f"GDACS {p.get('eventid')}",
                           "place": p.get("name") or p.get("country")})
            continue
        events.append({
            "id": f"gd-{p.get('eventtype')}{p.get('eventid')}", "kind": kind,
            "title": p.get("name") or f"{kind} in {p.get('country', '?')}",
            "lat": lat, "lon": lon, "severity": ALERT_SEV.get(level, 0.3),
            "status": "awake", "seen_at": p.get("fromdate") or _iso(dt.datetime.now(dt.timezone.utc)),
            "extra": {"category": kind, "gdacs_alert": level, "country": p.get("country"),
                      "magnitude": sev.get("severity"), "magnitude_unit": sev.get("severityunit"),
                      "severity_text": sev.get("severitytext"),
                      "source": (p.get("url") or {}).get("report") if isinstance(p.get("url"), dict) else None},
        })
    return events, quakes


# ------------------------------------------------------------------ JMA
COD = re.compile(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)([+-]\d+)?/")


def parse_jma(data: list) -> list[dict]:
    out, seen = [], set()
    for q in data[:80]:
        m = COD.match(q.get("cod") or "")
        mag = q.get("mag")
        if not m or not mag or q.get("eid") in seen:
            continue
        try:
            mag = float(mag)
        except ValueError:
            continue
        seen.add(q.get("eid"))
        depth_m = abs(float(m.group(3))) if m.group(3) else None
        out.append({"agency": "JMA", "mag": mag, "lat": float(m.group(1)), "lon": float(m.group(2)),
                    "depth_km": depth_m / 1000 if depth_m is not None else None,
                    "time": q.get("at"), "ref": f"JMA {q.get('eid')}", "place": q.get("en_anm") or q.get("anm")})
    return out


# ------------------------------------------------------------------ EMSC
def parse_emsc(data: dict) -> list[dict]:
    out = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        if p.get("mag") is None:
            continue
        out.append({"agency": "EMSC", "mag": float(p["mag"]), "lat": float(p["lat"]), "lon": float(p["lon"]),
                    "depth_km": p.get("depth"), "time": p.get("time"), "ref": f"EMSC {p.get('unid')}",
                    "place": (p.get("flynn_region") or "").title()})
    return out


def fetch_quake_reports() -> tuple[list[dict], list[str]]:
    reps, errs = [], []
    since = _iso(dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2))[:19]
    for name, fn in (
        ("EMSC", lambda: parse_emsc(_get(EMSC, format="json", limit=100, minmag=4, start=since))),
        ("JMA", lambda: parse_jma(_get(JMA))),
        ("GDACS", lambda: parse_gdacs(_get(GDACS))[1]),
    ):
        try:
            reps += fn()
        except Exception as exc:
            errs.append(f"{name}: {exc}")
    return reps, errs


def fetch_gdacs_events() -> list[dict]:
    return parse_gdacs(_get(GDACS))[0]


# ------------------------------------------------------------------ NWS county alerts
def parse_nws(data: dict) -> list[dict]:
    """One row per (alert, county)."""
    rows = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        same = (p.get("geocode") or {}).get("SAME") or []
        names = [n.strip() for n in (p.get("areaDesc") or "").split(";")]
        c = _centroid(f.get("geometry"))
        for i, code in enumerate(same):
            code = str(code).zfill(6)
            state = FIPS.get(code[1:3], code[1:3])
            county = names[i] if i < len(names) and len(names) == len(same) else f"county {code[3:]}"
            rows.append({
                "id": f"{p.get('id', '')[-40:]}|{code}", "fips": code[1:], "state": state, "county": county,
                "event": p.get("event"), "severity": p.get("severity") or "Unknown",
                "sev_rank": NWS_SEV.get(p.get("severity"), 0), "headline": (p.get("headline") or "")[:300],
                "expires": p.get("expires") or p.get("ends"),
                "lat": c[0] if c else None, "lon": c[1] if c else None,
            })
    return rows


def fetch_county_alerts() -> list[dict]:
    return parse_nws(_get(NWS, status="actual", message_type="alert"))


# ------------------------------------------------------------------ point forecasts / alerts (Warden)
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def fetch_open_meteo(lat: float, lon: float) -> dict:
    d = _get(OPEN_METEO, latitude=lat, longitude=lon, forecast_days=2, wind_speed_unit="kmh",
             hourly="temperature_2m,relative_humidity_2m,wind_gusts_10m")
    h = d.get("hourly", {})
    return {"temp": h.get("temperature_2m") or [], "rh": h.get("relative_humidity_2m") or [],
            "gust": h.get("wind_gusts_10m") or []}


def is_us(lat: float, lon: float) -> bool:
    return (18 <= lat <= 72 and -180 <= lon <= -64) or (13 <= lat <= 21 and 144 <= lon <= 146)


def fetch_nws_point(lat: float, lon: float) -> list[dict]:
    return _get(NWS, point=f"{lat:.4f},{lon:.4f}").get("features", [])


# ------------------------------------------------------------------ satellite view (NASA GIBS, no key)
GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
POLAR_TRUE = ["VIIRS_NOAA20_CorrectedReflectance_TrueColor", "VIIRS_SNPP_CorrectedReflectance_TrueColor",
              "MODIS_Terra_CorrectedReflectance_TrueColor", "MODIS_Aqua_CorrectedReflectance_TrueColor"]

# channel -> (what it's good for, candidate layers per family; first that returns data wins)
SAT_CHANNELS = {
    "GeoColor (true colour by day, IR by night)": (
        "Best overview: what your eye would see by day; infrared clouds at night.",
        {"GOES": ["{sat}_ABI_GeoColor", "{sat}_ABI_Band2_Red_Visible_1km"],
         "Himawari": ["Himawari_AHI_Band3_Red_Visible_1km", "Himawari_AHI_Band13_Clean_Infrared"],
         "POLAR": POLAR_TRUE}),
    "Visible 0.64 µm": (
        "Daytime only. Finest detail (~0.5-1 km): cloud texture, overshooting tops, smoke, dust, snow.",
        {"GOES": ["{sat}_ABI_Band2_Red_Visible_1km"], "Himawari": ["Himawari_AHI_Band3_Red_Visible_1km"],
         "POLAR": POLAR_TRUE}),
    "Clean infrared 10.3 µm": (
        "Day and night. Cloud-top temperature: brighter = colder = taller storms; cyclone eye and intensity.",
        {"GOES": ["{sat}_ABI_Band13_Clean_Infrared"], "Himawari": ["Himawari_AHI_Band13_Clean_Infrared"],
         "POLAR": ["VIIRS_SNPP_Brightness_Temp_BandI5_Night", "MODIS_Terra_Brightness_Temp_Band31_Day"]}),
    "Water vapour 6.2 µm": (
        "Moisture in the upper troposphere: jet streams, dry slots, troughs steering storms.",
        {"GOES": ["{sat}_ABI_Band8_Upper_Level_Water_Vapor", "{sat}_ABI_Band9_Mid_Level_Water_Vapor",
                  "{sat}_ABI_Air_Mass"],
         "Himawari": ["Himawari_AHI_Band8_Upper_Level_Water_Vapor", "Himawari_AHI_Air_Mass"],
         "POLAR": ["AIRS_L2_Total_Precipitable_Water_Vapor_Day"]}),
    "Air Mass RGB": (
        "Separates warm/moist from cold/dry air: cyclone structure, dry-air intrusions, jet streaks.",
        {"GOES": ["{sat}_ABI_Air_Mass", "{sat}_ABI_Band13_Clean_Infrared"],
         "Himawari": ["Himawari_AHI_Air_Mass", "Himawari_AHI_Band13_Clean_Infrared"],
         "POLAR": POLAR_TRUE}),
    "Fire hotspots (VIIRS, daily)": (
        "Active fires detected by VIIRS (375 m) over true colour.",
        {"ANY": [f"{POLAR_TRUE[0]},VIIRS_NOAA20_Thermal_Anomalies_375m_All",
                 f"{POLAR_TRUE[1]},VIIRS_SNPP_Thermal_Anomalies_375m_All",
                 f"{POLAR_TRUE[2]},MODIS_Combined_Thermal_Anomalies_All"]}),
    "True colour (VIIRS, daily)": (
        "Once-a-day high-resolution natural colour: floods, smoke, ash plumes, snow.",
        {"ANY": POLAR_TRUE}),
    "Rain rate (IMERG, 30 min)": (
        "Satellite-estimated precipitation rate (GPM IMERG).",
        {"ANY": ["IMERG_Precipitation_Rate", "IMERG_Precipitation_Rate_30min"]}),
}

# which channels best show each disaster type
RECOMMENDED = {
    "storm": ["Clean infrared 10.3 µm", "Air Mass RGB"],
    "wildfire": ["Fire hotspots (VIIRS, daily)", "GeoColor (true colour by day, IR by night)"],
    "volcano": ["True colour (VIIRS, daily)", "Clean infrared 10.3 µm"],
    "flood": ["True colour (VIIRS, daily)", "Rain rate (IMERG, 30 min)"],
    "earthquake": ["GeoColor (true colour by day, IR by night)", "True colour (VIIRS, daily)"],
    "aurora": ["Clean infrared 10.3 µm"],
    "drought": ["True colour (VIIRS, daily)"],
    "default": ["GeoColor (true colour by day, IR by night)", "Clean infrared 10.3 µm"],
}


def geo_family(lon: float) -> tuple[str, str] | None:
    if -180 <= lon < -105:
        return "GOES", "GOES-West"
    if -105 <= lon < -25:
        return "GOES", "GOES-East"
    if 75 <= lon <= 180:
        return "Himawari", "Himawari"
    return None


def geo_layer(lon: float) -> tuple[str, str] | None:      # kept for older callers
    fam = geo_family(lon)
    return (f"{fam[1]}_ABI_Band13_Clean_Infrared" if fam[0] == "GOES" else "Himawari_AHI_Band13_Clean_Infrared",
            f"{fam[1]} infrared") if fam else None


def satellite_images(lat: float, lon: float, channel: str = "Clean infrared 10.3 µm",
                     half_deg: float = 5.0) -> list[tuple[str, bytes | None, str]]:
    """Try each candidate layer (default/latest time first, then explicit recent times) until one has data."""
    now_utc = dt.datetime.now(dt.timezone.utc)
    s, n = max(-90, lat - half_deg), min(90, lat + half_deg)
    w, e = max(-180, lon - half_deg * 1.3), min(180, lon + half_deg * 1.3)
    base = {"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.3.0", "CRS": "EPSG:4326",
            "BBOX": f"{s},{w},{n},{e}", "WIDTH": 760, "HEIGHT": int(760 * (n - s) / (e - w))}
    why, fams = SAT_CHANNELS.get(channel, SAT_CHANNELS["Clean infrared 10.3 µm"])
    fam = geo_family(lon)
    cands = list(fams.get("ANY", []))
    if fam and fam[0] in fams:
        cands += [c.format(sat=fam[1]) for c in fams[fam[0]]]
    cands += fams.get("POLAR", []) if not fams.get("ANY") else []
    times = [None]
    for lag in (20, 40, 70):
        t = now_utc - dt.timedelta(minutes=lag)
        times.append(t.replace(minute=t.minute - t.minute % 10, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"))
    times += [now_utc.date().isoformat(), (now_utc - dt.timedelta(days=1)).date().isoformat()]
    last_err = "no candidate layer"
    for layer in cands:
        for t in times:
            params = {**base, "LAYERS": f"{layer},Coastlines_15m", "FORMAT": "image/png" if "IMERG" in layer else "image/jpeg"}
            if t:
                params["TIME"] = t
            cap, img, err = _gibs(params, f"{channel} · {layer.split(',')[-1]}" + (f" · {t}" if t else " · latest") + f": {why}")
            if img:
                return [(cap, img, "")]
            last_err = err
    return [(channel, None, last_err)]


def _gibs(params: dict, caption: str) -> tuple[str, bytes | None, str]:
    try:
        r = requests.get(GIBS_WMS, params=params, headers={"User-Agent": UA["User-Agent"]}, timeout=20)
        if r.ok and r.headers.get("content-type", "").startswith("image") and len(r.content) > 6000:
            return caption, r.content, ""
        return caption, None, f"HTTP {r.status_code} ({len(r.content)} bytes)"
    except Exception as exc:
        return caption, None, str(exc)
