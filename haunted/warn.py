"""Warden's physics: turn live hazards into place-specific Advisory / Watch / Warning levels.

Every number here is a rough, transparent estimate meant for a demo, NOT an official warning.
Official sources (NWS, JMA, tsunami warning centers, national agencies) always take precedence.
"""
from __future__ import annotations

import datetime as dt
import math

from .physics import aurora_boundary_lat, haversine_km

LEVELS = {0: "None", 1: "Advisory", 2: "Watch", 3: "Warning"}
G = 9.81

# ------------------------------------------------------------------ earthquakes
VP, VS = 6.5, 3.75          # crustal P and S wave speeds, km/s
ALERT_LATENCY_S = 4.0       # detection + processing after P reaches the nearest stations
NEAR_STATION_KM = 10.0      # assumed epicentral distance of the first stations


def mmi_atkinson_wald(mag: float, dist_km: float) -> float:
    """Modified Mercalli Intensity from the Atkinson & Wald (2007) California intensity
    prediction equation. R = sqrt(D^2 + 14^2) km."""
    c1, c2, c3, c4, c5, c6, c7 = 12.27, 2.270, 0.1304, -1.30, -0.0007070, 1.95, -0.577
    R = math.sqrt(dist_km ** 2 + 14.0 ** 2)
    B = max(0.0, math.log10(R / 50.0))
    m = mag - 6.0
    return (c1 + c2 * m + c3 * m * m + c4 * math.log10(R) + c5 * R + c6 * B
            + c7 * mag * math.log10(R))


MMI_WORD = {1: "not felt", 2: "weak", 3: "weak", 4: "light", 5: "moderate", 6: "strong",
            7: "very strong", 8: "severe", 9: "violent", 10: "extreme"}
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def eew_seconds(dist_km: float, depth_km: float) -> float:
    """Seconds between an early-warning alert and S-wave (strong shaking) arrival at the place.
    Alert is issued when P reaches stations ~10 km from the epicentre, plus processing latency."""
    r_place = math.hypot(dist_km, depth_km)
    r_station = math.hypot(NEAR_STATION_KM, depth_km)
    return r_place / VS - (r_station / VP + ALERT_LATENCY_S)


def quake_threat(q: dict, place: dict) -> dict | None:
    mag, depth = float(q["mag"]), float(q.get("depth_km") or 10)
    d = haversine_km(q["lat"], q["lon"], place["lat"], place["lon"])
    if d > 1500:
        return None
    mmi = max(1.0, min(10.0, mmi_atkinson_wald(mag, d)))
    level = 3 if mmi >= 6 else 2 if mmi >= 5 else 1 if mmi >= 4 else 0
    out = None
    if level:
        w = eew_seconds(d, depth)
        lead = (f"an early-warning system would give ~{w:.0f} s before strong shaking" if w > 0
                else "inside the early-warning blind zone (shaking arrives before an alert)")
        out = {"key": f"quake:{q['id']}", "hazard": "earthquake", "level": level,
               "headline": f"M{mag:.1f} quake {d:.0f} km away: shaking ~MMI {ROMAN[round(mmi)]} "
                           f"({MMI_WORD[round(mmi)]})",
               "detail": f"Atkinson-Wald (2007) intensity estimate at {d:.0f} km; {lead} "
                         f"(P {VP} km/s, S {VS} km/s, {ALERT_LATENCY_S:.0f} s latency)."}
    # tsunami: big, shallow quakes; only for places marked coastal
    if place.get("coastal") and mag >= 7.0 and depth <= 70:
        c = math.sqrt(G * 4000.0)                 # deep-ocean shallow-water wave speed, m/s
        eta_h = d * 1000 / c / 3600
        tl = 3 if (mag >= 7.5 and d <= 1000) else 2
        t = {"key": f"tsunami:{q['id']}", "hazard": "tsunami", "level": tl,
             "headline": f"Possible tsunami: first waves could arrive in ~{eta_h:.1f} h if one was generated",
             "detail": f"M{mag:.1f}, depth {depth:.0f} km, {d:.0f} km away. Shallow-water wave speed "
                       f"√(g·h) with h = 4 km ≈ {c * 3.6:.0f} km/h along a straight line. "
                       f"Follow your national tsunami warning center."}
        return t if not out or tl > out["level"] else out
    return out


# ------------------------------------------------------------------ tropical cyclones
def _xy(lat0: float, lon0: float, lat: float, lon: float) -> tuple[float, float]:
    """Local flat projection (km) around (lat0, lon0)."""
    return ((lon - lon0) * 111.32 * math.cos(math.radians(lat0)), (lat - lat0) * 110.57)


def rankine_wind(vmax_kt: float, r_km: float, rmax_km: float = 40.0, alpha: float = 0.6) -> float:
    """Modified Rankine vortex: V = Vmax (r/Rmax) inside, Vmax (Rmax/r)^alpha outside."""
    if r_km <= rmax_km:
        return vmax_kt * r_km / rmax_km
    return vmax_kt * (rmax_km / r_km) ** alpha


def cyclone_threat(s: dict, place: dict) -> dict | None:
    track = (s.get("extra") or {}).get("track") or []
    vmax = (s.get("extra") or {}).get("magnitude")
    if len(track) < 2 or not vmax:
        return None
    (la1, lo1, t1), (la2, lo2, t2) = track[-2], track[-1]
    try:
        dt_h = (dt.datetime.fromisoformat(t2.replace("Z", "+00:00")) -
                dt.datetime.fromisoformat(t1.replace("Z", "+00:00"))).total_seconds() / 3600
    except Exception:
        dt_h = 6.0
    if dt_h <= 0:
        return None
    vx, vy = _xy(la2, lo2, la1, lo1)
    vx, vy = -vx / dt_h, -vy / dt_h                 # storm velocity, km/h
    speed = math.hypot(vx, vy)
    px, py = _xy(la2, lo2, place["lat"], place["lon"])
    if speed < 1:
        return None
    along = (px * vx + py * vy) / speed             # km ahead along the track
    cross = abs(px * vy - py * vx) / speed          # closest-approach distance, km
    if along <= 0:
        return None                                 # storm moving away
    eta_h = along / speed
    if eta_h > 96:
        return None
    # if the eye passes within Rmax, the place is crossed by the eyewall (peak winds)
    wind = float(vmax) if cross <= 40.0 else rankine_wind(float(vmax), cross)
    # NHC practice: warnings ~36 h ahead, watches ~48 h ahead of tropical-storm-force winds
    if wind < 34:
        return None
    level = 3 if eta_h <= 36 else 2 if eta_h <= 48 else 1
    return {"key": f"cyclone:{s['id']}", "hazard": "cyclone", "level": level,
            "headline": f"{s['title']}: closest approach ~{cross:.0f} km in ~{eta_h:.0f} h, "
                        f"winds ~{wind:.0f} kt at your place",
            "detail": f"Straight-line extrapolation of the last track segment ({speed:.0f} km/h); "
                      f"modified Rankine vortex (Vmax {float(vmax):.0f} kt, Rmax 40 km, α 0.6). "
                      f"≥34 kt = tropical-storm force, ≥64 kt = hurricane force. Levels follow NHC lead times "
                      f"(watch ~48 h, warning ~36 h)."}


# ------------------------------------------------------------------ heat and wind (forecast)
def wet_bulb_stull(t_c: float, rh: float) -> float:
    """Stull (2011) wet-bulb temperature (°C) from air temperature (°C) and RH (%)."""
    return (t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659)) + math.atan(t_c + rh)
            - math.atan(rh - 1.676331) + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh) - 4.686035)


def weather_threats(place: dict, wx: dict) -> list[dict]:
    out = []
    temps, rhs, gusts = wx.get("temp") or [], wx.get("rh") or [], wx.get("gust") or []
    if temps and rhs:
        tw = max(wet_bulb_stull(t, r) for t, r in zip(temps, rhs) if t is not None and r is not None)
        level = 3 if tw >= 31 else 2 if tw >= 29 else 1 if tw >= 27 else 0
        if level:
            out.append({"key": "heat", "hazard": "heat", "level": level,
                        "headline": f"{'Dangerous' if level >= 2 else 'Oppressive'} humid heat: wet-bulb up to {tw:.1f} °C in the next 48 h",
                        "detail": "Stull (2011) wet-bulb from forecast T and RH. Sweat stops cooling the "
                                  "body effectively as wet-bulb nears ~31 °C for many healthy adults "
                                  "(lab studies), and lower for older people. Shade, water, cooling."})
    if gusts:
        g = max(x for x in gusts if x is not None)
        level = 3 if g >= 110 else 2 if g >= 90 else 1 if g >= 65 else 0
        if level:
            out.append({"key": "wind", "hazard": "wind", "level": level,
                        "headline": f"{'Damaging' if level >= 2 else 'Strong'} wind gusts up to {g:.0f} km/h in the next 48 h",
                        "detail": "Open-Meteo forecast gusts. Wind load on structures grows with speed squared."})
    return out


# ------------------------------------------------------------------ aurora
POLE_LAT, POLE_LON = 80.8, -72.7   # approximate geomagnetic (dipole) north pole


def geomag_lat(lat: float, lon: float) -> float:
    p, l = math.radians(POLE_LAT), math.radians(POLE_LON)
    a, b = math.radians(lat), math.radians(lon)
    return math.degrees(math.asin(math.sin(a) * math.sin(p) + math.cos(a) * math.cos(p) * math.cos(b - l)))


def aurora_threat(kp: float, place: dict) -> dict | None:
    mlat = abs(geomag_lat(place["lat"], place["lon"]))
    edge = aurora_boundary_lat(kp)
    if mlat < edge - 3:          # aurora overhead at the edge is often visible ~3° further away, low on the horizon
        return None
    return {"key": "aurora", "hazard": "aurora", "level": 1,
            "headline": f"Aurora possible tonight (Kp {kp:.1f}); look {'north' if place['lat'] >= 0 else 'south'}",
            "detail": f"Your geomagnetic latitude ≈ {mlat:.0f}°, auroral oval edge ≈ {edge:.0f}° "
                      f"(dipole approximation). Also: strong storms can disturb GPS and HF radio."}


# ------------------------------------------------------------------ official NWS point alerts
def nws_threats(features: list[dict]) -> list[dict]:
    out = []
    for f in features:
        p = f.get("properties", {})
        ev = p.get("event") or "Alert"
        level = 3 if "Warning" in ev else 2 if "Watch" in ev else 1
        out.append({"key": f"nws:{ev}", "hazard": "official", "level": level,
                    "headline": f"Official NWS {ev}",
                    "detail": (p.get("headline") or "")[:300] + " (National Weather Service)"})
    return out
