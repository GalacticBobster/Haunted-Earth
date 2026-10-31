"""Physics fact-checkers. Each specialist checks only claims in its own field, against the
official measurement stored in the haunt's durable actor, and explains errors in physical units.

Verdicts: CONFIRMED · MISMATCH · PLAUSIBLE · IMPLAUSIBLE · UNVERIFIABLE
"""
from __future__ import annotations

import datetime as dt

from .physics import aftershock_probability, bath_largest_aftershock, pct

ROLES = {
    "seismologist": {"kinds": {"earthquake"}, "claims": {"magnitude", "depth_km", "aftershock", "tsunami"}},
    "meteorologist": {"kinds": {"storm"}, "claims": {"wind", "category"}},
    "spaceweather": {"kinds": {"aurora"}, "claims": {"gscale", "kp"}},
}

TO_KTS = {"mph": 0.868976, "km/h": 0.539957, "kph": 0.539957, "kmh": 0.539957,
          "knots": 1.0, "kts": 1.0, "kt": 1.0}


def saffir_simpson(kts: float) -> int:
    """0 = below hurricane strength. Sustained 1-minute winds in knots (NHC)."""
    for cat, lo in ((5, 137), (4, 113), (3, 96), (2, 83), (1, 64)):
        if kts >= lo:
            return cat
    return 0


def g_from_kp(kp: float) -> int:
    """NOAA G-scale: G1=Kp5, G2=Kp6, G3=Kp7, G4=Kp8, G5=Kp9."""
    return 0 if kp < 5 else min(5, int(kp) - 4)


def _hours_since(iso: str | None) -> float | None:
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600
    except Exception:
        return None


def check_seismology(c: dict, extra: dict) -> tuple[str, str]:
    M = extra.get("mag")
    if M is None:
        return "UNVERIFIABLE", "no official magnitude stored"
    if c["type"] == "magnitude":
        d = c["value"] - M
        if abs(d) <= 0.15:
            return "CONFIRMED", f"USGS M{M:.1f}; headline M{c['value']:.1f}"
        ratio = 10 ** (1.5 * d)
        word = "overstates" if d > 0 else "understates"
        return "MISMATCH", (f"headline M{c['value']:.1f} vs USGS M{M:.1f}: it {word} the radiated energy "
                            f"by {max(ratio, 1/ratio):.1f}× (log E = 1.5M + 4.8). Early estimates are often "
                            f"revised, so this may be an outdated first report.")
    if c["type"] == "depth_km":
        z = extra.get("depth_km")
        if z is None:
            return "UNVERIFIABLE", "no official depth"
        tol = max(5.0, 0.2 * z)
        if abs(c["value"] - z) <= tol:
            return "CONFIRMED", f"USGS depth {z} km; headline {c['value']:.0f} km"
        return "MISMATCH", (f"headline depth {c['value']:.0f} km vs USGS {z} km. Depth matters: "
                            f"{'shallow quakes shake the surface harder' if z < 70 else 'deep quakes are felt widely but gently'}.")
    if c["type"] == "aftershock":
        ma = c["value"]
        if ma >= M:
            return "IMPLAUSIBLE", (f"an 'aftershock' of M{ma:.1f} ≥ mainshock M{M:.1f} would make the first "
                                   f"quake a foreshock; check which event the story means")
        hrs = _hours_since(extra.get("event_time")) or 24.0
        p = aftershock_probability(M, ma, 0.0, max(hrs, 0.1) / 24)
        verdict = "PLAUSIBLE" if p >= 0.05 else "IMPLAUSIBLE"
        return verdict, (f"P(≥M{ma:.1f} aftershock within {hrs:.0f} h of an M{M:.1f}) = {pct(p)} "
                         f"(Reasenberg-Jones); Båth's law expects the largest near M{bath_largest_aftershock(M):.1f}")
    if c["type"] == "tsunami":
        z = extra.get("depth_km") or 0
        if M >= 7.0 and z < 70:
            return "PLAUSIBLE", f"M{M:.1f} at {z} km depth can displace the seafloor enough; follow official warning centers"
        if M < 6.5:
            return "IMPLAUSIBLE", f"M{M:.1f} rarely moves enough seafloor for a damaging tsunami (typically needs M≳7, shallow)"
        return "PLAUSIBLE", f"M{M:.1f} at {z} km: a small local tsunami is possible; ocean-wide is unlikely"
    return "UNVERIFIABLE", "not a seismology claim"


def check_meteorology(c: dict, extra: dict) -> tuple[str, str]:
    kts = extra.get("magnitude")
    if not kts or (extra.get("magnitude_unit") or "kts").lower() not in ("kts", "kt", "knots"):
        return "UNVERIFIABLE", "no official wind speed in the feed"
    kts = float(kts)
    if c["type"] == "wind":
        unit = (c.get("unit") or "kts").lower()
        claim_kts = c["value"] * TO_KTS.get(unit, 1.0)
        rel = (claim_kts - kts) / kts
        if abs(rel) <= 0.15:
            return "CONFIRMED", f"{c['value']:.0f} {unit} = {claim_kts:.0f} kt; official {kts:.0f} kt"
        if rel > 0.15 and claim_kts <= kts * 1.5:
            return "PLAUSIBLE", (f"{c['value']:.0f} {unit} = {claim_kts:.0f} kt vs official sustained {kts:.0f} kt: "
                                 f"likely a gust (gusts run ~20-40% above 1-minute sustained winds)")
        return "MISMATCH", f"{c['value']:.0f} {unit} = {claim_kts:.0f} kt vs official {kts:.0f} kt ({rel:+.0%})"
    if c["type"] == "category":
        cat = saffir_simpson(kts)
        if int(c["value"]) == cat:
            return "CONFIRMED", f"{kts:.0f} kt sustained = Category {cat} (Saffir-Simpson)"
        return "MISMATCH", (f"headline says Category {int(c['value'])}, but {kts:.0f} kt sustained is "
                            f"{'Category ' + str(cat) if cat else 'below hurricane strength'}. Wind damage "
                            f"scales roughly with speed cubed, so one category is a big difference.")
    return "UNVERIFIABLE", "not a meteorology claim"


def check_spaceweather(c: dict, extra: dict) -> tuple[str, str]:
    kp = extra.get("kp")
    if kp is None:
        return "UNVERIFIABLE", "no current Kp"
    g = g_from_kp(float(kp))
    if c["type"] == "gscale":
        claim = int(c["value"])
        if claim == g:
            return "CONFIRMED", f"current Kp {kp:.1f} = G{g}"
        if claim > g:
            return "PLAUSIBLE", (f"headline G{claim} vs current G{g} (Kp {kp:.1f}): may be a forecast/watch, "
                                 f"not current conditions")
        return "MISMATCH", f"headline G{claim} but current Kp {kp:.1f} is G{g}"
    if c["type"] == "kp":
        if abs(c["value"] - kp) <= 0.7:
            return "CONFIRMED", f"current Kp {kp:.1f}"
        return "PLAUSIBLE", f"headline Kp {c['value']:.1f} vs current {kp:.1f}: Kp changes every 3 h, likely a different window"
    return "UNVERIFIABLE", "not a space-weather claim"


CHECKERS = {"seismologist": check_seismology, "meteorologist": check_meteorology,
            "spaceweather": check_spaceweather}


def run_checks(role: str, kind: str, claims: list[dict], extra: dict) -> list[dict]:
    spec = ROLES[role]
    if kind not in spec["kinds"]:
        return []
    out = []
    for c in claims:
        if c["type"] in spec["claims"]:
            verdict, why = CHECKERS[role](c, extra)
            out.append({"role": role, "claim": c, "verdict": verdict, "explanation": why})
    return out


def credibility(confirmed: int, plausible: int, mismatched: int, implausible: int) -> tuple[float, float]:
    """Beta-binomial credibility of an outlet: mean and 1-sigma, Beta(1,1) prior.

    Successes = confirmed + 0.5*plausible; failures = mismatched + implausible.
    """
    a = 1 + confirmed + 0.5 * plausible
    b = 1 + mismatched + implausible + 0.5 * plausible
    mean = a / (a + b)
    sd = (a * b / ((a + b) ** 2 * (a + b + 1))) ** 0.5
    return mean, sd
