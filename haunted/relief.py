"""Quartermaster's toolbox: nearby help from OpenStreetMap, 72-hour needs (Sphere standards),
and hazard checklists. Free, no keys. Guidance only, never a substitute for local authorities.
"""
from __future__ import annotations

import requests

from .physics import haversine_km

OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "HauntedEarth/0.1 (hackathon demo; GitHub GalacticBobster)"}

KINDS = {  # OSM tag -> label
    ("amenity", "hospital"): "hospital",
    ("amenity", "clinic"): "clinic",
    ("amenity", "shelter"): "shelter",
    ("social_facility", "shelter"): "shelter",
    ("emergency", "assembly_point"): "assembly point",
    ("amenity", "fire_station"): "fire station",
    ("amenity", "pharmacy"): "pharmacy",
    ("amenity", "drinking_water"): "drinking water",
}
NOT_SHELTERS = {"public_transport", "picnic_shelter", "lean_to", "gazebo", "field_shelter"}


def fetch_resources(lat: float, lon: float, radius_km: float = 15.0) -> list[dict]:
    r = int(radius_km * 1000)
    parts = "".join(f'nwr(around:{r},{lat},{lon})["{k}"="{v}"];' for k, v in KINDS)
    q = f"[out:json][timeout:25];({parts});out center 300;"
    resp = requests.post(OVERPASS, data={"data": q}, headers=UA, timeout=40)
    resp.raise_for_status()
    return parse_resources(resp.json(), lat, lon)


def parse_resources(data: dict, lat: float, lon: float) -> list[dict]:
    out, seen = [], set()
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        kind = next((lab for (k, v), lab in KINDS.items() if tags.get(k) == v), None)
        if not kind or (kind == "shelter" and tags.get("shelter_type") in NOT_SHELTERS):
            continue
        la = el.get("lat") or (el.get("center") or {}).get("lat")
        lo = el.get("lon") or (el.get("center") or {}).get("lon")
        if la is None or lo is None:
            continue
        name = tags.get("name") or tags.get("name:en") or f"unnamed {kind}"
        key = (kind, name, round(la, 3), round(lo, 3))
        if key in seen:
            continue
        seen.add(key)
        out.append({"kind": kind, "name": name, "lat": la, "lon": lo,
                    "km": round(haversine_km(lat, lon, la, lo), 1),
                    "phone": tags.get("phone") or tags.get("contact:phone"),
                    "directions": f"https://www.google.com/maps/dir/?api=1&destination={la},{lo}"})
    out.sort(key=lambda r: r["km"])
    return out


def summarize(res: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in res:
        counts[r["kind"]] = counts.get(r["kind"], 0) + 1
    return counts


# Sphere Handbook (2018) minimums, per person per day
WATER_L = 15          # drinking + cooking + basic hygiene
FOOD_KCAL = 2100
SHELTER_M2 = 3.5      # covered living space per person


def needs_72h(people: int = 1000) -> dict:
    d = 3
    return {"people": people, "days": d,
            "water_litres": WATER_L * people * d,
            "food_kcal": FOOD_KCAL * people * d,
            "shelter_m2": SHELTER_M2 * people,
            "water_trucks_10k_L": round(WATER_L * people * d / 10000, 1)}


CHECKLIST = {
    "earthquake": ["Drop, cover, hold on during aftershocks", "Check gas lines; don't use open flames",
                   "Expect aftershocks (see the outlook)", "Keep shoes and a torch by the bed"],
    "tsunami": ["Move to high ground or inland now if you felt strong shaking near the coast",
                "Don't wait for an official warning near the coast", "Stay away until officials give the all-clear"],
    "cyclone": ["Secure loose objects; charge phones and power banks", "Store 3 days of water (15 L/person/day)",
                "Know your evacuation route and nearest shelter", "Stay indoors away from windows during landfall"],
    "heat": ["Drink water regularly; avoid alcohol", "Check on elderly neighbours twice a day",
             "Use cooling centres / shaded public buildings", "Avoid outdoor work in the hottest hours"],
    "wind": ["Bring in loose outdoor items", "Avoid parking under trees", "Charge devices in case of power cuts"],
    "official": ["Follow the official instructions in the alert", "Monitor local radio / authority channels"],
    "aurora": ["Look away from city lights after dark", "Expect possible GPS/HF radio disruption"],
}
