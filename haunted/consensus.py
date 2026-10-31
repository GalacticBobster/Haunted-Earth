"""Corroborator's science: match the same earthquake across agencies and combine their magnitudes.

Different agencies use different stations, methods and even magnitude types (USGS often Mw,
JMA uses its own Mj), so independent reports scatter. We take an inverse-variance weighted
mean and run a chi-square consistency test: if the spread is larger than each agency's typical
uncertainty explains, the agencies genuinely disagree and the event is flagged.
"""
from __future__ import annotations

import datetime as dt
import math

from .physics import haversine_km

# Nominal 1-sigma magnitude uncertainty per agency (illustrative, order of typical scatter)
SIGMA = {"USGS": 0.10, "EMSC": 0.15, "JMA": 0.15, "GDACS": 0.20}
MATCH_KM, MATCH_S = 150.0, 120.0


def _t(s) -> dt.datetime | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return dt.datetime.fromtimestamp(s / 1000, dt.timezone.utc)
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def same_quake(a: dict, b: dict) -> bool:
    ta, tb = _t(a.get("time")), _t(b.get("time"))
    if ta is None or tb is None:
        return False
    return (abs((ta - tb).total_seconds()) <= MATCH_S
            and haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]) <= MATCH_KM
            and abs(a["mag"] - b["mag"]) <= 1.0)


def chi2_sf(x: float, k: int) -> float:
    """Chi-square survival function for small integer dof (exact closed forms)."""
    if k <= 0:
        return 1.0
    if k % 2 == 0:  # Q = exp(-x/2) * sum_{i<k/2} (x/2)^i / i!
        s, term = 0.0, 1.0
        for i in range(k // 2):
            if i:
                term *= (x / 2) / i
            s += term
        return math.exp(-x / 2) * s
    # odd k: Q = erfc(sqrt(x/2)) + exp(-x/2) * sum_{i=1}^{(k-1)/2} (x/2)^{i-1/2} / Gamma(i+1/2)
    s = math.erfc(math.sqrt(x / 2))
    for i in range(1, (k - 1) // 2 + 1):
        s += math.exp(-x / 2) * (x / 2) ** (i - 0.5) / math.gamma(i + 0.5)
    return s


def combine(reports: list[dict]) -> dict:
    """Inverse-variance consensus + chi-square consistency."""
    w = [(r, 1 / SIGMA.get(r["agency"], 0.2) ** 2) for r in reports]
    W = sum(wi for _, wi in w)
    m = sum(r["mag"] * wi for r, wi in w) / W
    sd = 1 / math.sqrt(W)
    chi2 = sum(((r["mag"] - m) / SIGMA.get(r["agency"], 0.2)) ** 2 for r in reports)
    dof = len(reports) - 1
    p = chi2_sf(chi2, dof) if dof else 1.0
    outlier = max(reports, key=lambda r: abs(r["mag"] - m) / SIGMA.get(r["agency"], 0.2))
    return {"mag": m, "sd": sd, "chi2": chi2, "dof": dof, "p": p, "n": len(reports),
            "agree": p >= 0.05, "outlier": outlier["agency"]}


def describe(c: dict, reports: list[dict]) -> str:
    parts = ", ".join(f"{r['agency']} M{r['mag']:.1f}" for r in sorted(reports, key=lambda r: r["agency"]))
    if c["n"] == 1:
        return f"Single source so far ({parts}); waiting for other agencies."
    s = f"{parts} → consensus M{c['mag']:.2f} ± {c['sd']:.2f} (χ² = {c['chi2']:.1f}, {c['dof']} dof, p = {c['p']:.2f})"
    if c["agree"]:
        return s + ": agencies agree."
    note = " (JMA's Mj scale can differ systematically from Mw)" if c["outlier"] == "JMA" else ""
    return s + f": agencies DISAGREE beyond typical error; {c['outlier']} is the outlier{note}."
