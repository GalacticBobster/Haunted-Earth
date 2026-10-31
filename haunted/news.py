"""Herald's eyes: news + social posts about each haunt (GDELT, Google News RSS, Mastodon; no keys)
and claim extraction.

Claims are pulled out with deterministic patterns first (reliable, testable); if an LLM is
configured it can add more, but every claim is then checked by physics, never by the LLM.
"""
from __future__ import annotations

import hashlib
import os
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

import requests

UA = {"User-Agent": "HauntedEarth/0.1 (hackathon demo)"}
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
GNEWS = "https://news.google.com/rss/search"

KIND_WORD = {"earthquake": "earthquake", "storm": "storm", "wildfire": "wildfire",
             "volcano": "volcano", "flood": "flood", "aurora": "aurora geomagnetic storm"}


def place_of(title: str) -> str:
    """'M6.1 38 km SE of Hualien City, Taiwan' -> 'Hualien City'."""
    t = re.sub(r"^M\d\.\d\s+", "", title)
    t = t.split(" of ", 1)[-1]
    t = re.sub(r"^(Sample|Tropical Storm|Typhoon|Hurricane|Cyclone|Wildfire|Volcano Activity)\s+", "", t)
    return t.split(",")[0].strip()


def query_for(h: dict) -> str:
    if h["kind"] == "aurora":
        return "aurora geomagnetic storm"
    if h["kind"] == "storm":
        return place_of(h["title"]).split(" in ")[0]
    return f"{place_of(h['title'])} {KIND_WORD.get(h['kind'], h['kind'])}"


def art_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def domain(url: str) -> str:
    d = urllib.parse.urlparse(url).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def fetch_gdelt(q: str, n: int = 8) -> list[dict]:
    r = requests.get(GDELT, headers=UA, timeout=15, params={
        "query": q, "mode": "artlist", "format": "json", "maxrecords": n,
        "timespan": "3d", "sort": "datedesc"})
    r.raise_for_status()
    out = []
    for a in (r.json() or {}).get("articles", []):
        if a.get("language", "English") != "English":
            continue
        out.append({"url": a["url"], "title": a.get("title", ""), "outlet": a.get("domain") or domain(a["url"]),
                    "published": a.get("seendate", "")})
    return out


def fetch_gnews(q: str, n: int = 8) -> list[dict]:
    r = requests.get(GNEWS, headers=UA, timeout=15,
                     params={"q": f"{q} when:3d", "hl": "en-US", "gl": "US", "ceid": "US:en"})
    r.raise_for_status()
    out = []
    for it in ET.fromstring(r.content).iter("item"):
        title = it.findtext("title") or ""
        src = it.find("source")
        outlet = (src.get("url") if src is not None else "") or ""
        if " - " in title:  # Google appends " - Outlet"
            title = title.rsplit(" - ", 1)[0]
        out.append({"url": it.findtext("link") or "", "title": title,
                    "outlet": domain(outlet) if outlet else (src.text if src is not None else "news"),
                    "published": it.findtext("pubDate") or ""})
        if len(out) >= n:
            break
    return out


MASTODON = "https://mastodon.social/api/v1/timelines/tag/{tag}"
MASTO_TAGS = {"earthquake": ["earthquake"], "storm": ["typhoon", "hurricane", "cyclone"],
              "aurora": ["aurora"], "volcano": ["volcano"], "wildfire": ["wildfire"]}


def fetch_mastodon(h: dict, n: int = 6) -> list[dict]:
    """Public Mastodon hashtag posts (no key) that mention this haunt's place."""
    place = place_of(h["title"]).split()[0].lower() if h["kind"] != "aurora" else ""
    out = []
    for tag in MASTO_TAGS.get(h["kind"], []):
        r = requests.get(MASTODON.format(tag=tag), headers=UA, timeout=15, params={"limit": 40})
        r.raise_for_status()
        for post in r.json():
            text = re.sub(r"<[^>]+>", " ", post.get("content") or "")
            text = re.sub(r"\s+", " ", text).strip()
            if place and place not in text.lower():
                continue
            acct = (post.get("account") or {}).get("acct", "someone")
            out.append({"url": post.get("url") or post.get("uri"), "title": text[:220],
                        "outlet": f"@{acct}" if "@" in acct else f"@{acct}@mastodon.social",
                        "published": post.get("created_at", ""), "social": True})
            if len(out) >= n:
                return out
    return out


# extra sites to search, e.g. NEWS_SITES=reuters.com,apnews.com,factcheck.afp.com
SITES = [x.strip() for x in os.getenv("NEWS_SITES", "").split(",") if x.strip()]


# Outlet RSS feeds scanned every cycle (add more with NEWS_FEEDS=url1,url2 in .env)
RSS_FEEDS = {
    "bbc.co.uk": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "theguardian.com": "https://www.theguardian.com/world/rss",
    "aljazeera.com": "https://www.aljazeera.com/xml/rss/all.xml",
    "npr.org": "https://feeds.npr.org/1004/rss.xml",
    "dw.com": "https://rss.dw.com/rdf/rss-en-world",
    "france24.com": "https://www.france24.com/en/rss",
    "cbc.ca": "https://www.cbc.ca/webfeed/rss/rss-world",
    "timesofindia.com": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "nhk.or.jp": "https://www3.nhk.or.jp/rss/news/cat0.xml",
}
HAZARD_WORDS = {"earthquake": r"quake|seismic|tremor|aftershock|magnitude|tsunami",
                "storm": r"typhoon|hurricane|cyclone|tropical storm",
                "volcano": r"volcan|erupt|ash cloud", "wildfire": r"wildfire|bushfire|forest fire",
                "flood": r"flood", "aurora": r"aurora|geomagnetic|solar storm|northern lights"}
_rss_cache: dict = {"t": 0.0, "items": []}


def fetch_rss_all(max_age_s: int = 600) -> list[dict]:
    """All hazard-related items from outlet RSS feeds (cached ~10 min)."""
    import time as _t
    if _t.time() - _rss_cache["t"] < max_age_s:
        return _rss_cache["items"]
    feeds = dict(RSS_FEEDS)
    for i, url in enumerate(x.strip() for x in os.getenv("NEWS_FEEDS", "").split(",") if x.strip()):
        feeds[domain(url) or f"feed{i}"] = url
    any_hazard = re.compile("|".join(HAZARD_WORDS.values()), re.I)
    items = []
    for outlet, url in feeds.items():
        try:
            r = requests.get(url, headers=UA, timeout=12)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for it in root.iter():
                if not it.tag.endswith("item") and not it.tag.endswith("entry"):
                    continue
                title = (it.findtext("title") or it.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                desc = re.sub(r"<[^>]+>", " ", it.findtext("description") or it.findtext(
                    "{http://www.w3.org/2005/Atom}summary") or "")
                link = it.findtext("link") or ""
                if not link:
                    le = it.find("{http://www.w3.org/2005/Atom}link")
                    link = le.get("href") if le is not None else ""
                if title and any_hazard.search(title + " " + desc):
                    items.append({"url": link.strip(), "title": title, "summary": desc.strip()[:400],
                                  "outlet": outlet, "published": it.findtext("pubDate") or ""})
        except Exception:
            continue
    _rss_cache.update(t=_t.time(), items=items)
    return items


def rss_for(h: dict) -> list[dict]:
    """RSS items that mention this haunt's place (or, for aurora/storms, its hazard)."""
    rx = re.compile(HAZARD_WORDS.get(h["kind"], h["kind"]), re.I)
    place = place_of(h["title"]).split(",")[0].lower()
    stop = {"near", "north", "south", "east", "west", "northern", "southern", "eastern", "western", "region",
            "island", "islands", "coast", "city", "sample", "offshore", "central", "province", "state", "ridge",
            "drill", "the", "of", "and"}
    words = [w for w in re.split(r"[\s/,()-]+", re.sub(r"^m\d(\.\d)?\s+", "", place)) if len(w) > 3 and w not in stop]
    out = []
    for it in fetch_rss_all():
        text = (it["title"] + " " + it.get("summary", "")).lower()
        if not rx.search(text):
            continue
        if h["kind"] in ("aurora",) or any(w in text for w in words):
            out.append(it)
    return out[:8]


def fetch_news(h: dict) -> tuple[list[dict], list[str]]:
    q, arts, errs = query_for(h), [], []
    for name, fn in (("RSS", lambda: rss_for(h)), ("GDELT", lambda: fetch_gdelt(q)),
                     ("GoogleNews", lambda: fetch_gnews(q)), ("Mastodon", lambda: fetch_mastodon(h))) + tuple(
            (f"site:{d}", (lambda d=d: fetch_gnews(f"{q} site:{d}", 4))) for d in SITES):
        try:
            arts += fn()
        except Exception as exc:
            errs.append(f"{name}: {exc}")
    seen, uniq = set(), []
    for a in arts:
        key = re.sub(r"\W+", " ", a["title"].lower()).strip()[:80]
        if a["url"] and key and key not in seen:
            seen.add(key)
            uniq.append({**a, "id": art_id(a["url"])})
    return uniq[:20], errs


# ------------------------------------------------------------------ claims
NUM = r"(\d+(?:\.\d+)?)"
PATTERNS = [
    ("magnitude", re.compile(r"\b(?:magnitude|mag\.?)[\s-]*(\d\.\d)\b", re.I)),
    ("magnitude", re.compile(r"\b(\d\.\d)[\s-]*magnitude\b", re.I)),
    ("magnitude", re.compile(r"\bM\s?(\d\.\d)\b")),
    ("depth_km", re.compile(r"\bdepth of (?:about |around )?" + NUM + r"\s?(?:km|kilomet)", re.I)),
    ("depth_km", re.compile(NUM + r"\s?(?:km|kilomet\w*)[\s-]+deep\b", re.I)),
    ("aftershock", re.compile(r"aftershocks?\b[^.]{0,40}?(\d\.\d)", re.I)),
    ("wind", re.compile(NUM + r"\s?(mph|km/h|kph|kmh|knots|kts|kt)\b", re.I)),
    ("category", re.compile(r"\bcategory[\s-]*([1-5])\b", re.I)),
    ("gscale", re.compile(r"\bG([1-5])\b(?:[\s-]*(?:storm|geomagnetic|watch|warning))?", re.I)),
    ("kp", re.compile(r"\bKp(?:[\s-]*index)?[\s=of]*(\d(?:\.\d+)?)", re.I)),
]


def extract_claims(text: str) -> list[dict]:
    claims, seen = [], set()
    for typ, rx in PATTERNS:
        for m in rx.finditer(text):
            val = m.group(1)
            unit = m.group(2).lower() if typ == "wind" else None
            key = (typ, val, unit)
            if typ == "aftershock" and ("magnitude", val, None) in seen:
                seen.discard(("magnitude", val, None))
                claims = [c for c in claims if not (c["type"] == "magnitude" and c["value"] == float(val))]
            if key in seen:
                continue
            seen.add(key)
            claims.append({"type": typ, "value": float(val), "unit": unit,
                           "quote": text[max(0, m.start() - 30): m.end() + 30].strip()})
    if re.search(r"\btsunami\b", text, re.I) and not re.search(r"\bno tsunami|tsunami (?:threat|warning) (?:lifted|cancel)", text, re.I):
        claims.append({"type": "tsunami", "value": 1.0, "unit": None, "quote": text[:120]})
    return claims


def llm_claims(text: str) -> list[dict]:
    """Optional: ask the LLM for extra numeric claims. Returns [] on any failure."""
    try:
        from .llm import _client
        client, model = _client()
        r = client.chat.completions.create(model=model, messages=[
            {"role": "system", "content": "Extract numeric physical claims from a news headline. "
             "Return ONLY a JSON list of objects {type, value, unit} where type is one of "
             "magnitude, depth_km, aftershock, wind, category, gscale, kp, tsunami. "
             "Return [] if none."},
            {"role": "user", "content": text}])
        data = json.loads(re.search(r"\[.*\]", r.choices[0].message.content or "[]", re.S).group(0))
        ok = {"magnitude", "depth_km", "aftershock", "wind", "category", "gscale", "kp", "tsunami"}
        return [{"type": d["type"], "value": float(d.get("value") or 1), "unit": d.get("unit"),
                 "quote": text[:120]} for d in data if d.get("type") in ok]
    except Exception:
        return []


# ------------------------------------------------------------------ check any story (URL or text)
def fetch_story(url: str) -> tuple[str, str]:
    """(title, text) from a news page: og:title/<title> plus paragraph text."""
    r = requests.get(url, headers={**UA, "Accept": "text/html"}, timeout=15)
    r.raise_for_status()
    html = r.text[:2_000_000]
    import html as _h
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.I) or \
        re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = _h.unescape(m.group(1).strip()) if m else url
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.I | re.S)
    text = " ".join(_h.unescape(re.sub(r"<[^>]+>", " ", p)) for p in paras)
    return title, re.sub(r"\s+", " ", text).strip()[:6000]


USGS_WEEK = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson"


def official_matches(text: str) -> list[dict]:
    """Find official events this story is probably about (quakes by place name; storms by name; Kp)."""
    import datetime as _dt
    low = text.lower()
    out = []
    if re.search(r"quake|seismic|tremor|aftershock|magnitude", low):
        feats = requests.get(USGS_WEEK, headers=UA, timeout=20).json().get("features", [])
        for f in feats:
            p, g = f["properties"], f["geometry"]["coordinates"]
            place = (p.get("place") or "")
            words = [w.strip().lower() for w in re.split(r"[,]| of ", place) if len(w.strip()) > 3]
            if any(w in low for w in words[-2:]):
                out.append({"kind": "earthquake", "title": f"M{p['mag']:.1f} {place}", "url": p.get("url"),
                            "extra": {"mag": p["mag"], "depth_km": round(g[2], 1),
                                      "event_time": _dt.datetime.fromtimestamp(p["time"] / 1000, _dt.timezone.utc).isoformat()}})
        out.sort(key=lambda e: -e["extra"]["mag"])
        out = out[:1]
    if re.search(r"typhoon|hurricane|cyclone|tropical storm", low):
        ev = requests.get("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&category=severeStorms",
                          headers=UA, timeout=20).json().get("events", [])
        for e in ev:
            name = re.sub(r"^(Tropical Storm|Typhoon|Hurricane|Cyclone|Super Typhoon)\s+", "", e.get("title", ""),
                          flags=re.I).split()[0].lower()
            if len(name) > 2 and name in low:
                g = (e.get("geometry") or [{}])[-1]
                out.append({"kind": "storm", "title": e["title"], "url": (e.get("sources") or [{}])[0].get("url"),
                            "extra": {"magnitude": g.get("magnitudeValue"), "magnitude_unit": g.get("magnitudeUnit")}})
                break
    if re.search(r"aurora|geomagnetic|northern lights|solar storm|\bkp\b|\bg[1-5]\b", low):
        kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                          headers=UA, timeout=20).json()
        last = kp[-1]
        val = float(last.get("Kp", last.get("kp_index", 0))) if isinstance(last, dict) else float(last[1])
        out.append({"kind": "aurora", "title": f"NOAA SWPC current Kp {val:.1f}", "url": "https://www.swpc.noaa.gov/",
                    "extra": {"kp": val}})
    return out
