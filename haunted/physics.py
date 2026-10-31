"""The Analyst's toolbox: small, checkable physics. LLMs narrate; these numbers decide."""
from __future__ import annotations

import math

HIROSHIMA_J = 6.3e13          # ~15 kt TNT
TON_TNT_J = 4.184e9

# Generic California aftershock parameters (Reasenberg & Jones 1989)
RJ_A, RJ_B, RJ_P, RJ_C = -1.67, 0.91, 1.08, 0.05   # c in days


def quake_energy_joules(mag: float) -> float:
    """Radiated seismic energy, Gutenberg-Richter: log10 E[J] = 1.5 M + 4.8."""
    return 10 ** (1.5 * mag + 4.8)


def hiroshimas(energy_j: float) -> float:
    return energy_j / HIROSHIMA_J


def tons_tnt(energy_j: float) -> float:
    return energy_j / TON_TNT_J


def bath_largest_aftershock(mag: float) -> float:
    """Båth's law: largest aftershock is ~1.2 magnitude units below the mainshock."""
    return mag - 1.2


def aftershock_count(mag: float, m_min: float, t1_days: float, t2_days: float) -> float:
    """Expected number of aftershocks >= m_min between t1 and t2 days after the mainshock.

    Reasenberg & Jones (1989): rate(t, M) = 10^(a + b (Mm - M)) * (t + c)^-p
    """
    if t2_days <= t1_days:
        return 0.0
    k = 10 ** (RJ_A + RJ_B * (mag - m_min))
    q = 1.0 - RJ_P
    return max(0.0, k * ((t2_days + RJ_C) ** q - (t1_days + RJ_C) ** q) / q)


def aftershock_probability(mag: float, m_min: float, t1_days: float, t2_days: float) -> float:
    """P(at least one aftershock >= m_min in the window), Poisson."""
    return 1.0 - math.exp(-aftershock_count(mag, m_min, t1_days, t2_days))


def pct(p: float) -> str:
    return ">99%" if p > 0.99 else "<1%" if p < 0.01 else f"{p:.0%}"


def aurora_boundary_lat(kp: float) -> float:
    """Approximate equatorward edge of the auroral oval (geomagnetic latitude, deg).

    Rule of thumb: ~66° at Kp 0, moving ~2° equatorward per Kp unit (~48° at Kp 9).
    """
    return 66.0 - 2.0 * max(0.0, min(kp, 9.0))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def sci(x: float) -> str:
    """Compact scientific notation, e.g. 2.0e13."""
    if x == 0:
        return "0"
    e = int(math.floor(math.log10(abs(x))))
    return f"{x / 10**e:.1f}e{e}"


def analyze(h: dict, others: list[dict]) -> dict:
    """Return {'verdict': str, 'facts': dict} for one haunt, plus neighbours within 300 km."""
    kind, extra = h.get("kind"), h.get("extra") or {}
    facts: dict = {}
    parts: list[str] = []

    if kind == "earthquake":
        mag = float(extra.get("mag", 0))
        e = quake_energy_joules(mag)
        facts.update(
            energy_j=e,
            hiroshimas=hiroshimas(e),
            largest_aftershock=bath_largest_aftershock(mag),
            p_m3_next_day=aftershock_probability(mag, 3.0, 0.0, 1.0) if mag >= 4 else None,
            n_m3_next_day=aftershock_count(mag, 3.0, 0.0, 1.0) if mag >= 4 else None,
        )
        parts.append(f"M{mag:.1f}, depth {extra.get('depth_km', '?')} km")
        parts.append(f"energy {sci(e)} J (≈{facts['hiroshimas']:.2g} Hiroshima)")
        parts.append(f"largest aftershock ~M{facts['largest_aftershock']:.1f} (Båth)")
        if facts["p_m3_next_day"] is not None:
            parts.append(f"P(M3+ aftershock, first 24 h) {pct(facts['p_m3_next_day'])}, "
                         f"~{facts['n_m3_next_day']:.1f} expected (Reasenberg-Jones generic CA)")
    elif kind == "aurora":
        kp = float(extra.get("kp", 0))
        lat = aurora_boundary_lat(kp)
        facts.update(kp=kp, boundary_lat=lat)
        parts.append(f"Kp {kp:.1f}: aurora may reach ~{lat:.0f}° geomagnetic latitude")
    else:
        if extra.get("magnitude"):
            parts.append(f"{extra['magnitude']} {extra.get('magnitude_unit', '')}".strip())
        parts.append(f"category {extra.get('category', kind)}")

    near = []
    for o in others:
        if o.get("id") == h.get("id") or o.get("status") == "closed" or o.get("kind") == "aurora":
            continue
        d = haversine_km(h["lat"], h["lon"], o["lat"], o["lon"])
        if d <= 300:
            near.append((d, o))
    near.sort(key=lambda x: x[0])
    if near:
        d, o = near[0]
        facts["neighbour"] = {"id": o["id"], "title": o.get("title"), "km": round(d)}
        parts.append(f"{len(near)} other haunt(s) within 300 km; nearest: {o.get('title')} ({d:.0f} km)")

    return {"verdict": "; ".join(parts), "facts": facts}


# ---------------------------------------------------------------- aftershock outlook
def aftershock_outlook(mag: float, hours_since: float) -> dict:
    """USGS-style aftershock forecast with generic (Reasenberg & Jones 1989) parameters.

    Returns expected counts and probabilities for windows starting now, plus how long the
    sequence stays active (Omori decay of the rate).
    """
    t0 = max(hours_since, 0.05) / 24.0                 # days since mainshock
    windows = {"next 24 h": 1.0, "next 7 days": 7.0, "next 30 days": 30.0, "next year": 365.0}
    mags = [m for m in (3.0, 4.0, 5.0, 6.0, 7.0) if m < mag + 0.05] or [mag - 1]
    table = []
    for m in mags:
        row = {"magnitude": f"M{m:.0f}+"}
        for label, span in windows.items():
            n = aftershock_count(mag, m, t0, t0 + span)
            row[label] = f"{pct(1 - math.exp(-n))} (~{n:.1f})" if n >= 0.05 else pct(1 - math.exp(-n))
        table.append(row)

    def daily_rate(t_days: float, m_min: float = 3.0) -> float:
        return 10 ** (RJ_A + RJ_B * (mag - m_min)) * (t_days + RJ_C) ** (-RJ_P)

    rate_now = daily_rate(t0)
    # days until the M3+ rate falls below one per day / one per 10 days (Omori decay)
    def until(target: float) -> float:
        k = 10 ** (RJ_A + RJ_B * (mag - 3.0))
        return max(0.0, (k / target) ** (1 / RJ_P) - RJ_C)
    return {
        "table": table,
        "rate_now_per_day": rate_now,
        "rate_vs_day1": rate_now / daily_rate(1.0),
        "days_to_1_per_day": until(1.0),
        "days_to_1_per_10_days": until(0.1),
        "largest_expected": bath_largest_aftershock(mag),
    }
