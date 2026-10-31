"""Haunted Earth: the globe. Reads only from Supabase (or the local board file).

    streamlit run app.py
"""
import json
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from haunted import board  # noqa: E402


@st.cache_data(ttl=12, show_spinner=False)
def _cached_board(name: str):
    return getattr(board, name)()

st.set_page_config(page_title="Haunted Earth", page_icon="🎃", layout="wide")

COLORS = {
    "earthquake": "#ff7a1a", "wildfire": "#ff3b3b", "volcano": "#ffb000", "storm": "#9b5cff",
    "flood": "#3fa9ff", "aurora": "#39ff88", "ice": "#c8e8ff", "drought": "#c9a26b",
}
ALERT_COLOR = {4: "#ff2d55", 3: "#ff9f0a", 2: "#ffd60a", 1: "#8e8e93", 0: "#8e8e93"}
OPACITY = {"awake": 1.0, "fading": 0.45, "closed": 0.12}
VERDICT_BADGE = {"CONFIRMED": "✅", "PLAUSIBLE": "🟡", "MISMATCH": "❌", "IMPLAUSIBLE": "🚫", "UNVERIFIABLE": "❔"}


def relay_clean(msg: str) -> str:
    """Drop the [tag=value] routing prefixes agents use on Agent Relay."""
    import re
    return re.sub(r"\[\w+=[^\]]*\]\s*", "", msg)

st.markdown(
    """
    <style>
      .stApp { background: radial-gradient(circle at 50% 0%, #1b1030 0%, #07050d 60%); }
      h1, h2, h3, p, label, .stMarkdown { color: #f3e9ff !important; }
      .story { font-size: 1.05rem; font-style: italic; color: #ffd8a8; }
      .fc    { border-left: 3px solid #ff7a1a55; padding: 4px 10px; margin: 8px 0; font-size: 0.85rem; }
      .fc .hl  { color: #f3e9ff; }
      .fc .why { color: #b9a6d6; font-size: 0.8rem; }
      .why   { color: #b9a6d6; font-size: 0.82rem; }
      .chat  { font-family: ui-monospace, monospace; font-size: 0.8rem; color: #cbb8e6;
               border-left: 2px solid #ff7a1a33; padding-left: 8px; margin: 4px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

import io  # noqa: E402
import re  # noqa: E402
import secrets  # noqa: E402
import urllib.parse  # noqa: E402

APP_URL = (os.getenv("APP_URL") or "http://localhost:8501").rstrip("/")
JOIN_URL = f"{APP_URL}/?join=1"
QP = st.query_params


def qr_png(url: str) -> bytes:
    import qrcode
    img = qrcode.make(url, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def share_links(url: str, text: str) -> str:
    wa = "https://wa.me/?text=" + urllib.parse.quote(f"{text} {url}")
    mail = "mailto:?subject=" + urllib.parse.quote("Haunted Earth warnings") + "&body=" + urllib.parse.quote(f"{text}\n{url}")
    return f"[📱 Share on WhatsApp]({wa}) · [✉️ Email it]({mail})"


LEVEL_BOX = {3: st.error, 2: st.warning, 1: st.info}
LEVEL_WORD = {3: "WARNING", 2: "WATCH", 1: "ADVISORY"}


def page_unsub(pid: str) -> None:
    board.clear_email(pid)
    st.title("👻 Unsubscribed")
    st.write("You won't get more emails. Your live page still works: "
             f"[open it]({APP_URL}/?me={pid}). You can delete your location there.")


def page_join() -> None:
    from streamlit_js_eval import get_geolocation
    st.title("👻 Haunted Earth: warnings for where you are")
    st.write("Share your **approximate** location and Haunted Earth's Warden agent will watch it for "
             "earthquakes, tsunamis, cyclones, dangerous humid heat, strong wind, aurora and (in the US) "
             "official alerts, with the physics behind each warning.")
    name = st.text_input("Name (optional)", placeholder="e.g. Grandma in Kolkata")
    email = st.text_input("Email for alerts (optional)", placeholder="you@example.com")
    coastal = st.checkbox("I'm near the coast (include tsunami estimates)")
    consent = st.checkbox("I agree to share my location, rounded to ~1 km, so warnings can be computed. "
                          "I can delete it any time from my page.")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        st.caption("⚠️ That email doesn't look right; leave it empty to skip emails.")
    if st.button("📍 Share my location", type="primary", disabled=not consent):
        st.session_state.ask_geo = True
    if st.session_state.get("ask_geo"):
        loc = get_geolocation()
        if loc is None:
            st.info("Waiting for your browser… tap **Allow** when it asks for your location.")
        elif "coords" in loc:
            lat, lon = round(loc["coords"]["latitude"], 2), round(loc["coords"]["longitude"], 2)
            pid = "s-" + secrets.token_hex(5)
            em = email.strip() if email and "@" in email else None
            board.add_place((name or "Shared location").strip()[:60], lat, lon, coastal, em, pid=pid, shared=True)
            st.session_state.ask_geo = False
            st.query_params.clear()
            st.query_params["me"] = pid
            st.rerun()
        else:
            st.error("Location access was blocked. Allow it in your browser settings, or enter coordinates below.")
    with st.expander("No GPS? Enter coordinates instead"):
        la = st.number_input("Latitude", -90.0, 90.0, 0.0, format="%.2f")
        lo = st.number_input("Longitude", -180.0, 180.0, 0.0, format="%.2f")
        if st.button("Watch these coordinates", disabled=not consent):
            pid = "s-" + secrets.token_hex(5)
            em = email.strip() if email and "@" in email else None
            board.add_place((name or "Shared location").strip()[:60], round(la, 2), round(lo, 2), coastal, em,
                            pid=pid, shared=True)
            st.query_params.clear()
            st.query_params["me"] = pid
            st.rerun()
    st.caption("Demo estimates only, not official warnings. Always follow your local authorities.")


def page_me(pid: str) -> None:
    from haunted.physics import haversine_km
    place = board.get_place(pid)
    if not place:
        st.title("👻 This watch has ended")
        st.write(f"The location was deleted. [Start a new one]({JOIN_URL}).")
        return
    st.title(f"👻 {place['name']}")
    st.caption(f"Watching ~{place['lat']:.2f}, {place['lon']:.2f}"
               + (" · email alerts on" if place.get("email") else "")
               + " · checked every minute · demo estimates, not official warnings")

    @st.fragment(run_every=10)
    def live_me():
        ws = sorted([w for w in _cached_board('load_warnings') if w["place_id"] == pid], key=lambda w: -int(w["level"]))
        if not ws:
            st.success("All quiet near you. No active warnings. 👻 (New places get their first check within ~1 minute.)")
        for w in ws:
            LEVEL_BOX[int(w["level"])](f"**{LEVEL_WORD[int(w['level'])]} · {w['hazard']}**: {w['headline']}")
            with st.expander("Why? (the physics)"):
                st.write(w["detail"])
        near = []
        for h in _cached_board('load_haunts'):
            if h.get("status") == "closed":
                continue
            d = haversine_km(place["lat"], place["lon"], h["lat"], h["lon"])
            if d <= 3000:
                near.append((d, h))
        near.sort(key=lambda x: x[0])
        if near:
            st.subheader("Nearest restless spirits")
            for d, h in near[:5]:
                st.markdown(f"- **{h['title']}** · {d:,.0f} km" + (f"  \n  <span class='story'>{h['story']}</span>"
                            if h.get("story") else ""), unsafe_allow_html=True)
        fig = go.Figure(go.Scattergeo(lat=[place["lat"]], lon=[place["lon"]], mode="markers",
                                      marker=dict(symbol="star", size=16, color="#ffffff")))
        if near:
            nd = pd.DataFrame([h for _, h in near[:30]])
            fig.add_trace(go.Scattergeo(lat=nd.lat, lon=nd.lon, mode="markers", text=nd.title, hoverinfo="text",
                                        marker=dict(size=9 + 20 * nd.severity.clip(0, 1),
                                                    color=nd.kind.map(lambda k: COLORS.get(k, "#ddd")))))
        fig.update_geos(projection_type="orthographic",
                        projection_rotation=dict(lat=place["lat"], lon=place["lon"]),
                        showocean=True, oceancolor="#0b0716", showland=True, landcolor="#1d1430",
                        showcountries=True, countrycolor="#3a2a55", bgcolor="rgba(0,0,0,0)")
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="me_globe")
        st.caption(f"Updated {pd.Timestamp.now(tz='UTC'):%H:%M:%S} UTC")

    live_me()
    quakes_near = []
    for h in _cached_board('load_haunts'):
        if h.get("kind") == "earthquake" and h.get("status") != "closed":
            mm = re.match(r"M(\d+(?:\.\d+)?)", h.get("title") or "")
            if mm and float(mm.group(1)) >= 4.0 and haversine_km(place["lat"], place["lon"], h["lat"], h["lon"]) <= 300:
                quakes_near.append((float(mm.group(1)), h))
    if quakes_near:
        mag, h = max(quakes_near, key=lambda x: x[0])
        with st.expander(f"🌋 Aftershock outlook: {h['title']}", expanded=True):
            try:
                hrs = max(0.1, (pd.Timestamp.now(tz="UTC") - pd.Timestamp(h["first_seen"])).total_seconds() / 3600)
            except Exception:
                hrs = 1.0
            show_outlook(mag, hrs)
    try:
        mine = [m for m in _cached_board('load_missions') if m.get("place_id") == pid and m.get("status") == "active"]
    except Exception:
        mine = []
    for mi in mine:
        with st.expander(f"🆘 Help near you ({mi['hazard']})", expanded=True):
            render_mission(mi, compact=True)
    with st.expander("🛰 See the sky over you now"):
        from haunted.world import SAT_CHANNELS
        chan_me = st.selectbox("Channel", list(SAT_CHANNELS), index=0, key="chan_me")
        st.caption(SAT_CHANNELS[chan_me][0])
        if st.button("Load satellite view"):
            show_satellite(place["lat"], place["lon"], chan_me)
    st.markdown("**Invite someone else:** " + share_links(JOIN_URL, "Get live hazard warnings for where you are:"))
    if st.button("🗑 Stop watching and delete my location"):
        board.remove_place(pid)
        st.success("Deleted. Nothing about this location is kept.")
        st.rerun()


@st.cache_data(ttl=600, show_spinner=False)
def sat_images(lat: float, lon: float, channel: str):
    from haunted.world import satellite_images
    return satellite_images(lat, lon, channel)


def show_satellite(lat: float, lon: float, channel: str = "Clean infrared 10.3 µm") -> None:
    with st.spinner("Fetching NASA imagery…"):
        imgs = sat_images(round(lat, 1), round(lon, 1), channel)
    for cap, img, err in imgs:
        if img:
            st.image(img, caption=cap, width="stretch")
        else:
            st.caption(f"{cap}: not available right now ({err[:80]})")
    st.caption("Imagery: NASA GIBS / Worldview (GOES, Himawari, VIIRS). Geostationary infrared refreshes ~10 min.")


def show_outlook(mag: float, hours: float) -> None:
    from haunted.physics import aftershock_outlook
    o = aftershock_outlook(mag, hours)
    c1, c2, c3 = st.columns(3)
    c1.metric("M3+ aftershocks per day now", f"{o['rate_now_per_day']:.1f}")
    c2.metric("Busy (≥1 M3+/day) until", f"~{o['days_to_1_per_day']:.0f} days" if o['days_to_1_per_day'] >= 1
              else "already quieter")
    c3.metric("Largest aftershock, typical", f"M{o['largest_expected']:.1f}")
    st.dataframe(pd.DataFrame(o["table"]), hide_index=True, width="stretch")
    st.caption(f"Chance of at least one aftershock (expected number). Rates fall off with time (Omori's law): "
               f"aftershocks of M3+ become rarer than one per 10 days after ~{o['days_to_1_per_10_days']:.0f} days. "
               "Generic Reasenberg & Jones (1989) parameters; real sequences vary. Official forecasts come "
               "from your national seismic agency (e.g. USGS).")



ROLE_ICON = {"scout": "🧭", "logistics": "📦", "medic": "🩺", "comms": "📣"}


def render_mission(mi: dict, compact: bool = False) -> None:
    lvl = int(mi.get("level") or 1)
    icon = {3: "🔴", 2: "🟠", 1: "🟡"}.get(lvl, "⚪")
    active = mi.get("status") == "active"
    st.markdown(f"#### {icon} {mi['place_name']}: {mi['hazard']} "
                + ("" if active else "· <span class='why'>stood down</span>"), unsafe_allow_html=True)
    tasks = json.loads(mi.get("tasks_json") or "[]")
    if not compact:
        for t in tasks:
            mark = "✅" if t["status"] == "done" else "⏳"
            pad = "&nbsp;" * 6 * int(t["depth"])
            st.markdown(f"<div class='why'>{pad}{mark} {ROLE_ICON.get(t['role'], '•')} <b>{t['title']}</b>"
                        + (f"<br>{pad}&nbsp;&nbsp;&nbsp;&nbsp;{t['result'][:220]}" if t.get("result") else "")
                        + "</div>", unsafe_allow_html=True)
    show_nearest(mi)
    call = next((t["result"] for t in tasks if t["title"] == "Draft volunteer & donation call" and t.get("result")), "")
    if call and not compact:
        st.markdown("**Volunteer / donation call:** " + call)
        st.markdown(share_links(f"{APP_URL}/?join=1", call[:300]))


def show_nearest(mi: dict) -> None:
    near = json.loads(mi.get("nearest_json") or "[]")
    if near:
        st.markdown("**Nearest help** (OpenStreetMap)")
        for r in near:
            st.markdown(f"- {r['kind']}: **{r['name']}**, {r['km']} km · [directions]({r['directions']})"
                        + (f" · ☎ {r['phone']}" if r.get("phone") else ""))
    chk = json.loads(mi.get("checklist_json") or "[]")
    if chk:
        st.markdown("**Do now:** " + " · ".join(chk))


@st.cache_data(ttl=300, show_spinner=False)
def live_airports() -> list[dict]:
    """Fallback: fetch METARs + SIGMETs directly (agents not needed)."""
    from haunted.aviation import AIRPORTS, fetch_metars, fetch_sigmets, snapshot
    try:
        mets, sigs = fetch_metars(list(AIRPORTS)), fetch_sigmets()
    except Exception:
        return []
    return [snapshot(ic, mets.get(ic), sigs, None) for ic in AIRPORTS]


def compose_message(place_name: str, w: dict, link: str = "") -> str:
    """The exact text people receive (WhatsApp / SMS / email body)."""
    from haunted.relief import CHECKLIST
    from haunted.aviation import OPS_CHECKLIST
    lvl = {3: "WARNING", 2: "WATCH", 1: "ADVISORY"}.get(int(w["level"]), "ALERT")
    todo = (OPS_CHECKLIST if place_name[:4].isupper() and place_name[:4].isalpha() else CHECKLIST).get(
        w["hazard"], CHECKLIST.get(w["hazard"], ["Follow local authorities"]))
    return (f"🔔 [{lvl}] {w['hazard'].upper()} · {place_name}\n{w['headline']}\n"
            f"Do now: " + "; ".join(todo[:3]) + "\n"
            + (f"Live page: {link}\n" if link else "")
            + "(Haunted Earth demo estimate, not an official warning)")


CREW = ["scout", "analyst", "narrator", "herald", "seismologist", "meteorologist", "spaceweather", "judge",
        "corroborator", "sentinel", "warden", "quartermaster"]
CREW_EVERY = {"scout": 60, "corroborator": 90, "sentinel": 120, "warden": 20, "quartermaster": 30, "herald": 30}
CREW_JOB = {"scout": "watches USGS/NASA/GDACS/SWPC feeds", "analyst": "physics on every event",
            "narrator": "tells the story (numbers from physics)", "herald": "finds news & posts about events",
            "seismologist": "fact-checks quake claims", "meteorologist": "fact-checks storm claims",
            "spaceweather": "fact-checks aurora/Kp claims", "judge": "credibility ledger per outlet",
            "corroborator": "cross-checks USGS vs EMSC/JMA/GDACS", "sentinel": "US county alerts",
            "warden": "warnings per place & airport", "quartermaster": "relief missions & resource plan"}


def _pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def _agent_cmd(name: str) -> list[str]:
    if name in ("seismologist", "meteorologist", "spaceweather"):
        return ["uv", "run", "python", "-m", "haunted.agents", "checker", "--role", name]
    return ["uv", "run", "python", "-m", "haunted.agents", name]


def render_crew() -> None:
    import pathlib
    import subprocess
    rows = {r["name"]: r for r in _cached_board("load_agents")} if "_cached_board" in globals() else \
        {r["name"]: r for r in board.load_agents()}
    now_ts = pd.Timestamp.now(tz="UTC")
    table = []
    for n in CREW:
        r = rows.get(n, {})
        pidf = pathlib.Path("logs") / f"{n}.pid"
        local_alive = pidf.exists() and _pid_alive(pidf.read_text().strip() or 0)
        try:
            age = (now_ts - pd.Timestamp(r["last_seen"])).total_seconds()
        except Exception:
            age = 1e9
        alive = local_alive or age < max(90, 3 * CREW_EVERY.get(n, 5) + 30)
        table.append({"agent": n, "status": "🟢 working" if alive else ("🔴 down" if r else "⚪ not started"),
                      "job": CREW_JOB[n], "restarts": max(0, int(r.get("runs") or 0) - 1),
                      "cycles (all time)": int(r.get("cycles") or 0),
                      "last seen": f"{age:.0f}s ago" if age < 1e8 else "—",
                      "last action": (r.get("last_action") or "")[:90]})
    st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch", height=460)
    st.caption("Each agent has a durable **Crew** actor: its restart count and total cycles survive crashes. "
               "Kill one below: status turns 🔴, revive it, it comes back with `start #N` and its cycle count "
               "continues, while the Haunt/Place/Mission actors make sure nothing is redone or re-alerted.")
    c1, c2, c3 = st.columns([2, 1, 1])
    who = c1.selectbox("Crash test", CREW, index=CREW.index("warden"), label_visibility="collapsed")
    pidf = pathlib.Path("logs") / f"{who}.pid"
    if c2.button("💀 Kill -9"):
        try:
            pid = pidf.read_text().strip()
            subprocess.run(["pkill", "-9", "-P", pid])
            subprocess.run(["kill", "-9", pid])
            st.warning(f"{who} killed (kill -9). Watch its status turn 🔴, then revive it.")
        except Exception as exc:
            st.error(f"Couldn't kill {who} from here ({exc}). Only works on the laptop running the agents.")
    if c3.button("♻️ Revive"):
        try:
            log = open(pathlib.Path("logs") / f"{who}.log", "a")
            proc = subprocess.Popen(_agent_cmd(who), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            pidf.write_text(str(proc.pid))
            st.success(f"{who} restarted (pid {proc.pid}). It reports 'start #N, M cycles remembered' in a few seconds.")
        except Exception as exc:
            st.error(f"Couldn't revive {who} ({exc}). Run ./run_agents.sh instead.")

if "unsub" in QP:
    page_unsub(QP["unsub"])
    st.stop()
if "join" in QP:
    page_join()
    st.stop()
if "me" in QP:
    page_me(QP["me"])
    st.stop()

st.title("🎃 Haunted Earth")
st.caption("Every live quake, fire, volcano and storm is a persistent ghost. Agents watch the feeds, "
           "physics checks the facts (and the news), the narrator tells the tale.")

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    look = st.selectbox("Look at", ["Pacific", "Americas", "Europe/Africa", "Asia", "North Pole"])
with c2:
    show_closed = st.toggle("Show closed eyes", value=False)
with c3:
    kinds_filter = st.multiselect("Kinds", list(COLORS), default=[])

LEVEL_STYLE = {3: ("🔴", "Warning", "#ff2d55"), 2: ("🟠", "Watch", "#ff9f0a"), 1: ("🟡", "Advisory", "#ffd60a")}

with st.sidebar:
    st.header("📲 Share live warnings")
    st.caption("Anyone who scans this gets warnings for *their* location (with consent), optionally by email.")
    st.image(qr_png(JOIN_URL), width=180)
    st.markdown(share_links(JOIN_URL, "Get live hazard warnings for where you are:"))
    if "localhost" in APP_URL:
        st.caption("⚠️ This QR points to localhost. Deploy to Streamlit Cloud and set `APP_URL` in Secrets "
                   "so phones elsewhere can open it.")
    st.divider()
    st.header("📍 My places")
    if st.button("✈️ Watch major airports"):
        from haunted.aviation import AIRPORTS, place_id
        for ic, (nm, la, lo, el, rw, co) in AIRPORTS.items():
            board.add_place(f"{ic} {nm}", la, lo, co, pid=place_id(ic))
        st.success(f"Watching {len(AIRPORTS)} airports. First METAR pass within ~1 minute.")
    if st.button("⭐ Watch big cities near live events"):
        from haunted.cities import nearest, slug
        added = []
        try:
            live_rows = [r for r in _cached_board('load_haunts') if r.get("status") == "awake"
                         and (r.get("severity") or 0) >= 0.35 and r.get("kind") != "aurora"]
        except Exception:
            live_rows = []
        for r in sorted(live_rows, key=lambda r: -(r.get("severity") or 0))[:12]:
            for km, cty in nearest(r["lat"], r["lon"], km=400, k=2):
                board.add_place(cty[0], cty[1], cty[2], cty[4], pid=slug(cty[0]))
                added.append(cty[0].split(",")[0])
        st.success(("Now watching: " + ", ".join(sorted(set(added)))) if added else
                   "No big cities within 400 km of strong live events right now. Try a 🎯 Drill.")
    st.caption("The Warden watches these places and issues Advisory / Watch / Warning levels from physics "
               "and official alerts. Demo estimates only: always follow official warnings.")
    with st.form("add_place", clear_on_submit=True):
        nm = st.text_input("Name", placeholder="e.g. Home, Mountain View")
        c_a, c_b = st.columns(2)
        la = c_a.number_input("Latitude", -90.0, 90.0, 37.39, format="%.4f")
        lo = c_b.number_input("Longitude", -180.0, 180.0, -122.08, format="%.4f")
        co = st.checkbox("Coastal (check tsunami)", value=False)
        if st.form_submit_button("Watch this place") and nm.strip():
            board.add_place(nm.strip(), la, lo, co)
            st.success(f"Watching {nm.strip()}. First warnings within ~1 minute.")
    try:
        _places = [p for p in _cached_board('load_places') if not p.get("shared")]
    except Exception:
        _places = []
    for _p in _places:
        c_n, c_x = st.columns([5, 1])
        c_n.write(f"{_p['name']}" + (" 🌊" if _p.get("coastal") else ""))
        if c_x.button("🗑", key=f"rm_{_p['id']}", help="Stop watching"):
            board.remove_place(_p["id"])
            st.rerun()

CENTER = {"Pacific": (10, -160), "Americas": (20, -95), "Europe/Africa": (20, 15),
          "Asia": (25, 105), "North Pole": (75, -100)}


def globe(df: pd.DataFrame, alerts: list[dict] | None = None, places: list[dict] | None = None,
          warns: list[dict] | None = None) -> go.Figure:
    fig = go.Figure()
    if places:
        worst = {}
        for w in warns or []:
            worst[w["place_id"]] = max(worst.get(w["place_id"], 0), int(w["level"]))
        pdf = pd.DataFrame(places)
        pdf["lvl"] = pdf.id.map(lambda i: worst.get(i, 0))
        fig.add_trace(go.Scattergeo(
            lat=pdf.lat, lon=pdf.lon, mode="markers+text", name="my places",
            text=pdf.name.str.split(",").str[0], textposition="top center",
            textfont=dict(color="#f3e9ff", size=10), hoverinfo="text",
            hovertext=pdf.name + " · " + pdf.lvl.map(lambda l: LEVEL_STYLE.get(l, ("", "no warnings"))[1]),
            marker=dict(symbol="star", size=13, color=pdf.lvl.map(lambda l: LEVEL_STYLE.get(l, ("", "", "#ffffff"))[2]),
                        line=dict(width=1, color="#000"))))
    pts = [a for a in (alerts or []) if a.get("lat") is not None]
    if pts:  # NWS county alerts with a polygon: small warning diamonds
        ad = pd.DataFrame(pts).drop_duplicates(subset=["event", "lat", "lon"])
        fig.add_trace(go.Scattergeo(
            lat=ad.lat, lon=ad.lon, mode="markers", name="US alert",
            text=ad.event + " (" + ad.severity + ")<br>" + ad.county + ", " + ad.state, hoverinfo="text",
            marker=dict(symbol="diamond", size=7, color=ad.sev_rank.map(ALERT_COLOR), opacity=0.8,
                        line=dict(width=0.5, color="#000"))))
    for status in ("closed", "fading", "awake"):
        d = df[df.status == status]
        if d.empty:
            continue
        col = d.kind.map(lambda k: COLORS.get(k, "#e0e0e0"))
        size = 10 + 34 * d.severity.clip(0, 1)
        hover = d.title + "<br>" + d.kind + " · " + d.status + "<br><i>" + d.story.fillna("").str[:140] + "</i>"
        # glow, iris, pupil = an eye
        fig.add_trace(go.Scattergeo(lat=d.lat, lon=d.lon, mode="markers", hoverinfo="skip",
                                    marker=dict(size=size * 2.0, color=col, opacity=0.12 * OPACITY[status]),
                                    showlegend=False))
        fig.add_trace(go.Scattergeo(lat=d.lat, lon=d.lon, mode="markers", text=hover, hoverinfo="text",
                                    marker=dict(size=size, color=col, opacity=0.9 * OPACITY[status],
                                                line=dict(width=1, color="#000")),
                                    showlegend=False))
        if status != "closed":
            fig.add_trace(go.Scattergeo(lat=d.lat, lon=d.lon, mode="markers", hoverinfo="skip",
                                        marker=dict(size=size * 0.38, color="#050208", opacity=OPACITY[status]),
                                        showlegend=False))
    for k, c in COLORS.items():  # legend
        if k in set(df.kind):
            fig.add_trace(go.Scattergeo(lat=[None], lon=[None], mode="markers", name=k,
                                        marker=dict(size=10, color=c)))
    lat0, lon0 = CENTER[look]
    fig.update_geos(projection_type="orthographic", projection_rotation=dict(lat=lat0, lon=lon0),
                    showocean=True, oceancolor="#0b0716", showland=True, landcolor="#1d1430",
                    showcountries=True, countrycolor="#3a2a55", coastlinecolor="#5a4380",
                    showframe=False, bgcolor="rgba(0,0,0,0)", lataxis_showgrid=True,
                    lonaxis_showgrid=True, lataxis_gridcolor="#24183a", lonaxis_gridcolor="#24183a")
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(font=dict(color="#f3e9ff"), bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
                      uirevision="keep")
    return fig


@st.fragment(run_every=15)
def live():
    try:
        rows = _cached_board('load_haunts')
        chatter = board.load_chatter(20)
        try:
            county = _cached_board('load_county_alerts')
        except Exception:
            county = []   # table not created yet
        try:
            all_places, all_warns = _cached_board('load_places'), _cached_board('load_warnings')
        except Exception:
            all_places, all_warns = [], []
        # privacy: people who joined via the QR link are never shown on the public dashboard
        places = [p for p in all_places if not p.get("shared")]
        pub = {p["id"] for p in places}
        warns = [w for w in all_warns if w["place_id"] in pub]
        n_shared = len(all_places) - len(places)
    except Exception as exc:
        st.error(f"Board unreachable: {exc}")
        return
    if not rows:
        st.info("No haunts yet. Start the agents (./run_all.sh) and wait for the first scout pass.")
        return
    df = pd.DataFrame(rows)
    for c in ("story", "verdict", "consensus"):
        df[c] = df[c].fillna("").astype(str) if c in df.columns else ""
    if not show_closed:
        df = df[df.status != "closed"]
    if kinds_filter:
        df = df[df.kind.isin(kinds_filter)]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👁 Eyes open", int((df.status == "awake").sum()))
    m2.metric("🌫 Fading", int((df.status == "fading").sum()))
    m3.metric("🧪 Verdicts", int((df.verdict != "").sum()))
    m4.metric("📜 Stories", int((df.story != "").sum()))

    top = sorted(warns, key=lambda w: -int(w["level"]))
    if top and int(top[0]["level"]) >= 2:
        names = {p["id"]: p["name"] for p in places}
        lines = [f"**{names.get(w['place_id'], w['place_id'])}**: {LEVEL_STYLE[int(w['level'])][1].upper()}, "
                 f"{w['headline']}" for w in top if int(w["level"]) >= 2][:3]
        (st.error if int(top[0]["level"]) == 3 else st.warning)("🔔 " + "  \n".join(lines))

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(globe(df, county, places, warns), use_container_width=True, key="globe")
    with right:
        t9, t8, t0, t7, t1, t2, t3, t5, t6, t4 = st.tabs(["🤖 Crew", "✈️ Airports", "🔔 Warnings", "🆘 Relief",
                                                          "📜 Spirits", "🗞 Fact-check", "⚖️ Ledger", "🚨 County",
                                                          "🛰 Agencies", "💬 Chatter"])
        with t9:
            render_crew()
        with t8:
            try:
                apts = _cached_board('load_airports')
            except Exception:
                apts = []
            if not apts:
                apts = live_airports()
            if not apts:
                st.caption("No airports watched yet: click **✈️ Watch major airports** in the sidebar.")
            else:
                CAT_ICON = {"VFR": "🟢", "MVFR": "🔵", "IFR": "🔴", "LIFR": "🟣", "?": "⚪"}
                worst = {}
                for w in all_warns:
                    if w["place_id"].startswith("apt-"):
                        worst[w["place_id"][4:].upper()] = max(worst.get(w["place_id"][4:].upper(), 0), int(w["level"]))
                ad = pd.DataFrame([{
                    "airport": f"{a['icao']} {a.get('name', '')}", "cat": f"{CAT_ICON.get(a.get('cat'), '⚪')} {a.get('cat')}",
                    "alert": {3: "🔴 Warning", 2: "🟠 Watch", 1: "🟡 Advisory"}.get(worst.get(a["icao"], 0), ""),
                    "wind": a.get("wind", ""), "best runway": a.get("best_rwy", ""),
                    "crosswind kt": a.get("xwind_kt"), "density alt ft": a.get("density_alt_ft"),
                    "SIGMETs": ", ".join(h["hazard"] for h in a.get("sigmets") or []),
                    "traffic (air/ground)": (f"{a['traffic']['airborne']}/{a['traffic']['on_ground']}"
                                             if a.get("traffic") else "")} for a in apts])
                ad["_o"] = ad.alert.map({"🔴 Warning": 0, "🟠 Watch": 1, "🟡 Advisory": 2}).fillna(3)
                st.dataframe(ad.sort_values("_o").drop(columns="_o"), hide_index=True, width="stretch")
                pick_a = st.selectbox("METAR", [a["icao"] for a in apts], key="apt_pick")
                a = next(x for x in apts if x["icao"] == pick_a)
                st.code(a.get("raw", ""), language=None)
                st.caption("Flight category = FAA ceiling/visibility rules; crosswind = V·sin(θ) on each runway "
                           "(approx. true headings); density altitude from temperature and pressure; SIGMET = point in "
                           "official polygon. Data: aviationweather.gov, OpenSky Network. Not for operational use.")
        with t7:
            st.caption("Quartermaster opens a relief mission for every Watch/Warning. Finished tasks spawn "
                       "follow-ups (max depth 3): the plan grows itself. Resources: OpenStreetMap; needs: Sphere standards.")
            try:
                missions = [m for m in _cached_board('load_missions') if m.get("place_id") in pub]
            except Exception:
                missions = []
            missions.sort(key=lambda m: (m.get("status") != "active", -int(m.get("level") or 0)))
            try:
                alloc = next((m for m in _cached_board('load_missions') if m["id"] == "allocation"), None)
            except Exception:
                alloc = None
            if alloc and missions:
                plan = json.loads(alloc.get("tasks_json") or "{}")
                pool = plan.get("pool", {})
                st.markdown(f"##### 🧮 Quartermaster's plan: {pool.get('water_trucks')} water trucks (10,000 L) · "
                            f"{pool.get('med_teams')} medical teams")
                ad = pd.DataFrame(plan.get("rows", []))
                if not ad.empty:
                    ad = ad[["place", "hazard", "level", "people_at_risk", "trucks", "trucks_need",
                             "water_coverage", "teams", "teams_need", "medical_coverage"]]
                    st.dataframe(ad, hide_index=True, width="stretch", column_config={
                        "water_coverage": st.column_config.ProgressColumn("water %", min_value=0, max_value=100, format="%d%%"),
                        "medical_coverage": st.column_config.ProgressColumn("medical %", min_value=0, max_value=100, format="%d%%"),
                        "people_at_risk": st.column_config.NumberColumn("people at risk", format="%d")})
                    st.caption(f"Unmet: {plan.get('unmet_trucks')} trucks, {plan.get('unmet_teams')} teams. Greedy "
                               "marginal-coverage allocation weighted by warning level² (optimal for this concave "
                               "objective). People at risk = metro population × 1/5/15% for Advisory/Watch/Warning "
                               "(illustrative). Water: Sphere 15 L/person/day × 3 days.")
            if not missions:
                st.caption("No relief missions open.")
            for mi in missions[:6]:
                render_mission(mi)
        with t0:
            if not warns:
                st.caption("No active warnings for your places. Add places in the sidebar.")
            names = {p["id"]: p["name"] for p in places}
            order = sorted({w["place_id"] for w in warns},
                           key=lambda pid: -max(int(w["level"]) for w in warns if w["place_id"] == pid))
            for pid in order:
                ws = sorted([w for w in warns if w["place_id"] == pid], key=lambda w: -int(w["level"]))
                icon, word, _ = LEVEL_STYLE[int(ws[0]["level"])]
                st.markdown(f"#### {icon} {names.get(pid, pid)}")
                for w in ws:
                    i2, w2, _ = LEVEL_STYLE[int(w["level"])]
                    with st.expander(f"{i2} {w2.upper()} · {w['hazard']}: {w['headline']}"):
                        st.write(w["detail"])
                        st.markdown("**📣 What people receive:**")
                        st.code(compose_message(names.get(pid, pid), w, f"{APP_URL}/?join=1"), language=None)
        with t1:
            top = df[df.story != ""].sort_values("severity", ascending=False).head(5)
            if top.empty:
                st.caption("The narrator is still writing…")
            for _, r in top.iterrows():
                st.markdown(f"**{r.title}**  \n<span class='story'>{r.story}</span>", unsafe_allow_html=True)
                with st.expander("Analyst's verdict (physics)"):
                    st.write(r.verdict)
                    if r.get("consensus"):
                        st.caption("Agencies: " + r.consensus)
        with t2:
            st.caption("Headlines about live haunts, checked by specialist physics agents against the official data.")
            checks = board.load_factchecks(40)
            if not checks:
                st.caption("The herald is gathering news…")
            for c in checks[:15]:
                badge = VERDICT_BADGE.get(c.get("verdict"), "❔")
                st.markdown(
                    f"<div class='fc'>{badge} <b>{c.get('verdict')}</b> · <i>{c.get('checker')}</i> · "
                    f"{c.get('outlet')}<br><span class='hl'>“{(c.get('headline') or '')[:140]}”</span><br>"
                    f"<span class='why'>{c.get('claim')}: {c.get('explanation')}</span></div>",
                    unsafe_allow_html=True)
        with t3:
            st.caption("Durable credibility per outlet: Beta-binomial mean ± 1σ from physics-checked claims "
                       "(confirmed = 1, plausible = ½, contradicted = 0; prior Beta(1,1)).")
            outlets = _cached_board('load_outlets')
            if outlets:
                od = pd.DataFrame(outlets)
                od["checked"] = od[["confirmed", "plausible", "mismatched", "implausible"]].sum(axis=1)
                od = od.sort_values(["score", "checked"], ascending=[False, False])
                st.dataframe(
                    od[["outlet", "score", "score_sd", "checked", "confirmed", "mismatched", "implausible"]],
                    hide_index=True, use_container_width=True,
                    column_config={"score": st.column_config.ProgressColumn("credibility", min_value=0, max_value=1, format="%.2f"),
                                   "score_sd": st.column_config.NumberColumn("± 1σ", format="%.2f")})
            else:
                st.caption("No outlets judged yet.")
        with t5:
            st.caption("US county alert board (NWS). ⚠ links = an alert area centred within 100 km of a live haunt.")
            if county:
                cd = pd.DataFrame(county)
                cd["linked_haunt"] = cd.get("linked_haunt", pd.Series(dtype=str)).fillna("")
                g = (cd.groupby(["state", "county"])
                     .agg(alerts=("event", "count"), worst=("sev_rank", "max"),
                          events=("event", lambda e: ", ".join(sorted(set(e)))),
                          near_haunt=("linked_haunt", lambda x: "⚠" if any(x) else ""))
                     .reset_index().sort_values(["worst", "alerts"], ascending=False))
                g["worst"] = g.worst.map({4: "Extreme", 3: "Severe", 2: "Moderate", 1: "Minor", 0: "Unknown"})
                c1, c2 = st.columns(2)
                c1.metric("Counties under alert", len(g))
                c2.metric("Linked to haunts", int((g.near_haunt == "⚠").sum()))
                states = ["All"] + sorted(g.state.unique())
                pick = st.selectbox("State", states, key="state_pick")
                if pick != "All":
                    g = g[g.state == pick]
                st.dataframe(g, hide_index=True, use_container_width=True, height=330)
            else:
                st.caption("Sentinel hasn't reported yet.")
        with t6:
            st.caption("Corroborator: the same quake as seen by USGS, EMSC (Europe/Africa), JMA (Japan) and "
                       "GDACS (UN/EU), combined by inverse-variance weighting with a χ² consistency test.")
            cons = df[df.consensus != ""]
            if cons.empty:
                st.caption("No multi-agency reports yet.")
            for _, r in cons.sort_values("severity", ascending=False).head(8).iterrows():
                flag = "⚠️" if "DISAGREE" in r.consensus else "✅" if "agree" in r.consensus else "⏳"
                st.markdown(f"{flag} **{r.title}**  \n<span class='why'>{r.consensus}</span>",
                            unsafe_allow_html=True)
            spawned = df[df.id.str.startswith("xq-")]
            if not spawned.empty:
                st.markdown(f"**{len(spawned)} quake(s) found by other agencies but not in the USGS feed:** "
                            + ", ".join(spawned.title.head(6)))
        with t4:
            for c in chatter[:15]:
                msg = c.get("message", "")
                msg = relay_clean(msg)
                st.markdown(f"<div class='chat'><b>{c.get('sender')}</b>: {msg[:200]}</div>",
                            unsafe_allow_html=True)
    st.caption(f"Board: {board.mode()} · {len(rows)} haunts remembered · 👥 {n_shared} people watching "
               f"via shared links (private) · refreshes every 15 s · "
               "Data: USGS, NASA EONET, NOAA SWPC, GDACS, EMSC, JMA, NWS, GDELT, Google News")


live()


# ---------------------------------------------------------------- tools (not auto-refreshed)
st.divider()
st.header("🧰 Tools")
tool0, tool1, tool2, tool3 = st.tabs(["🎯 Drill", "🔎 Check a story", "🌋 Aftershock outlook", "🛰 Satellite view"])

with tool0:
    from haunted.cities import CITIES, nearest, slug
    from haunted.drills import start_position
    st.caption("Run a clearly-labelled DRILL through the real pipeline: Warden issues warnings for big cities "
               "nearby, Quartermaster opens relief missions and optimises scarce water trucks and medical teams.")
    d_kind = st.radio("Scenario", ["Earthquake", "Typhoon / hurricane"], horizontal=True)
    names = [c[0] for c in CITIES]
    d_city = st.selectbox("Near city", names, index=names.index("Tokyo, Japan"))
    c = CITIES[names.index(d_city)]
    if d_kind == "Earthquake":
        c1, c2, c3 = st.columns(3)
        d_mag = c1.slider("Magnitude", 5.0, 9.0, 7.4, 0.1)
        d_dep = c2.slider("Depth (km)", 5, 100, 15)
        d_off = c3.slider("Epicentre offset (km)", 0, 150, 40)
        d_lat, d_lon = c[1] - d_off / 110.57 * 0.6, c[2] + d_off / (111.32 * max(0.2, __import__("math").cos(__import__("math").radians(c[1])))) * 0.8
    else:
        c1, c2, c3 = st.columns(3)
        d_v = c1.slider("Max sustained wind (kt)", 64, 160, 125, 5)
        d_hrs = c2.slider("Hours until landfall", 12, 60, 30)
        d_hdg = c3.slider("Heading (° from north)", 0, 359, 290)
        d_lat, d_lon = start_position(c[1], c[2], d_hrs, d_hdg, 20)
    cc1, cc2 = st.columns(2)
    if cc1.button("🚨 Start drill", type="primary"):
        did = secrets.token_hex(4)
        row = {"id": did, "kind": "earthquake" if d_kind == "Earthquake" else "storm",
               "label": d_city.split(",")[0], "lat": round(d_lat, 3), "lon": round(d_lon, 3)}
        if d_kind == "Earthquake":
            row.update(mag=d_mag, depth_km=d_dep)
        else:
            row.update(vmax_kt=d_v, heading_deg=d_hdg, speed_kmh=20)
        board.add_drill(row)
        from types import SimpleNamespace
        from haunted.drills import drill_events
        for ev in drill_events([{**row, "active": True}]):
            board.mirror_many([SimpleNamespace(id=ev["id"], kind=ev["kind"], title=ev["title"], lat=ev["lat"],
                                               lon=ev["lon"], severity=ev["severity"], status="awake",
                                               verdict="", story="", first_seen=ev["seen_at"], consensus="")])
        watched = []
        for km, cty in nearest(c[1], c[2], km=700, k=6):
            board.add_place(cty[0], cty[1], cty[2], cty[4], pid=slug(cty[0]))
            watched.append(f"{cty[0].split(',')[0]} ({km:.0f} km)")
        st.success("Drill started. Watching: " + ", ".join(watched) + ". Agents pick it up within ~30 s; "
                   "the instant assessment is below.")
        # ---- instant assessment (same physics the agents use)
        from haunted.aviation import AIRPORTS, place_id as apt_id
        from haunted.cities import population
        from haunted.drills import allocate
        from haunted.physics import haversine_km
        from haunted.warn import LEVELS, cyclone_threat, quake_threat
        ev = drill_events([{**row, "active": True}])[0]
        targets = [{"id": slug(cty[0]), "name": cty[0], "lat": cty[1], "lon": cty[2], "coastal": cty[4]}
                   for km, cty in nearest(c[1], c[2], km=700, k=6)]
        targets += [{"id": apt_id(ic), "name": f"{ic} {a[0]}", "lat": a[1], "lon": a[2], "coastal": a[5]}
                    for ic, a in AIRPORTS.items() if haversine_km(c[1], c[2], a[1], a[2]) <= 700]
        issued = []
        for t in targets:
            if ev["kind"] == "earthquake":
                th = quake_threat({"id": ev["id"], "lat": ev["lat"], "lon": ev["lon"],
                                   "mag": ev["extra"]["mag"], "depth_km": ev["extra"]["depth_km"]}, t)
            else:
                th = cyclone_threat({"id": ev["id"], "title": ev["title"], "extra": ev["extra"]}, t)
            if th:
                issued.append((t, th))
        missions = [{"id": f"{t['id']}--{th['hazard']}", "place_id": t["id"], "place_name": t["name"],
                     "hazard": th["hazard"], "level": th["level"], "tasks_json": "[]"}
                    for t, th in issued if th["level"] >= 2 and not t["id"].startswith("apt-")]
        plan = allocate(missions, {m["place_id"]: population({"id": m["place_id"], "name": m["place_name"]})
                                   for m in missions}) if missions else None
        st.session_state["drill_result"] = {"event": ev["title"], "issued": [
            {"place": t["name"], "level": th["level"], "hazard": th["hazard"], "headline": th["headline"],
             "detail": th["detail"]} for t, th in sorted(issued, key=lambda x: -x[1]["level"])], "plan": plan}
    res = st.session_state.get("drill_result")
    if res:
        st.markdown(f"### 🚨 {res['event']}")
        st.markdown(f"**🔔 Warnings issued: {len(res['issued'])}**")
        st.dataframe(pd.DataFrame([{"place": i["place"],
                                    "level": {3: "🔴 Warning", 2: "🟠 Watch", 1: "🟡 Advisory"}[i["level"]],
                                    "hazard": i["hazard"], "what it means": i["headline"]} for i in res["issued"]]),
                     hide_index=True, width="stretch")
        if res["issued"]:
            top = res["issued"][0]
            st.markdown(f"**📣 What people in {top['place']} receive (WhatsApp / SMS / email):**")
            st.code(compose_message(top["place"], top, f"{APP_URL}/?join=1"), language=None)
            with st.expander("Why? (physics)"):
                for i in res["issued"][:6]:
                    st.markdown(f"- **{i['place']}**: {i['detail']}")
        if res.get("plan"):
            pl = res["plan"]
            st.markdown(f"**🧮 Relief plan: {pl['pool']['water_trucks']} water trucks · "
                        f"{pl['pool']['med_teams']} medical teams, optimally shared**")
            st.dataframe(pd.DataFrame(pl["rows"])[["place", "hazard", "level", "people_at_risk", "trucks",
                                                   "trucks_need", "water_coverage", "teams", "teams_need",
                                                   "medical_coverage"]], hide_index=True, width="stretch",
                         column_config={
                             "water_coverage": st.column_config.ProgressColumn("water %", min_value=0, max_value=100, format="%d%%"),
                             "medical_coverage": st.column_config.ProgressColumn("medical %", min_value=0, max_value=100, format="%d%%")})
            st.caption(f"Unmet: {pl['unmet_trucks']} trucks, {pl['unmet_teams']} teams. Greedy marginal-coverage "
                       "allocation weighted by warning level². People at risk = metro population × 5/15% "
                       "(Watch/Warning, illustrative); water 15 L/person/day × 3 days (Sphere).")
    if cc2.button("End all drills"):
        board.end_drills()
        st.info("Drills ended. Their warnings expire and missions stand down on the next agent pass.")


with tool1:
    st.caption("Paste a link from any news site (or the text of a post). Herald's claim extractor pulls out the "
               "numbers; the physics checkers compare them with the official data (USGS, NASA EONET, NOAA SWPC).")
    s_url = st.text_input("News link", placeholder="https://…")
    s_txt = st.text_area("…or paste the text", height=90)
    if st.button("Check it", type="primary") and (s_url.strip() or s_txt.strip()):
        from haunted.factcheck import ROLES, run_checks
        from haunted.news import domain, extract_claims, fetch_story, official_matches
        try:
            if s_url.strip():
                title, body = fetch_story(s_url.strip())
                outlet = domain(s_url.strip())
            else:
                title, body, outlet = s_txt.strip()[:140], s_txt.strip(), "pasted text"
            st.markdown(f"**{title}** · _{outlet}_")
            claims = extract_claims(title + ". " + body[:4000])[:12]
            matches = official_matches(title + " " + body[:4000])
        except Exception as exc:
            st.error(f"Couldn't read that page ({exc}). Try pasting the text instead.")
            claims, matches = [], []
        if not claims:
            st.info("No checkable physical numbers found (magnitude, depth, aftershock, tsunami, wind, category, G-scale, Kp).")
        elif not matches:
            st.warning("Found claims, but couldn't match the story to a current official event (last 7 days).")
            st.json([{"claim": c["type"], "value": c["value"], "unit": c["unit"]} for c in claims])
        for m in matches:
            st.markdown(f"Matched official record: [{m['title']}]({m.get('url') or '#'})")
            n = 0
            for role in ROLES:
                for c in run_checks(role, m["kind"], claims, m["extra"]):
                    n += 1
                    cl = c["claim"]
                    claim_txt = f"{cl['type']}={cl['value']:g}{(' ' + cl['unit']) if cl.get('unit') else ''}"
                    st.markdown(f"<div class='fc'>{VERDICT_BADGE.get(c['verdict'], '❔')} <b>{c['verdict']}</b> · "
                                f"<i>{role}</i> · {claim_txt}<br><span class='why'>{c['explanation']}</span></div>",
                                unsafe_allow_html=True)
                    try:
                        board.log_factcheck({"haunt_id": None, "article_url": s_url or None, "headline": title[:300],
                                             "outlet": outlet, "checker": role, "claim": claim_txt,
                                             "verdict": c["verdict"], "explanation": c["explanation"]})
                    except Exception:
                        pass
            if not n:
                st.caption("None of the claims are about this kind of event.")

with tool2:
    st.caption("How many aftershocks to expect, and for how long, after any earthquake.")
    try:
        qrows = [r for r in _cached_board('load_haunts') if r.get("kind") == "earthquake" and r.get("status") != "closed"]
    except Exception:
        qrows = []
    def _mag(t):
        mm = re.match(r"M(\d+(?:\.\d+)?)", t or "")
        return float(mm.group(1)) if mm else 0.0
    qrows = sorted(qrows, key=lambda r: -_mag(r.get("title")))[:40]
    labels = ["(enter my own)"] + [r["title"] for r in qrows]
    pick = st.selectbox("Earthquake", labels, index=1 if len(labels) > 1 else 0)
    if pick == "(enter my own)":
        c_m, c_h = st.columns(2)
        q_mag = c_m.number_input("Magnitude", 3.0, 9.5, 6.0, 0.1)
        q_hrs = c_h.number_input("Hours since the quake", 0.1, 8760.0, 1.0)
    else:
        r = next(r for r in qrows if r["title"] == pick)
        q_mag = _mag(pick)
        try:
            q_hrs = max(0.1, (pd.Timestamp.now(tz="UTC") - pd.Timestamp(r["first_seen"])).total_seconds() / 3600)
        except Exception:
            q_hrs = 1.0
        st.caption(f"{q_hrs:.1f} h since the mainshock")
    if q_mag < 4.0:
        st.info("Below M4 the aftershock sequence is usually small; numbers will be tiny.")
    show_outlook(q_mag, q_hrs)

with tool3:
    st.caption("Latest satellite view over any live event or place.")
    try:
        srows = sorted([r for r in _cached_board('load_haunts') if r.get("status") != "closed"],
                       key=lambda r: -(r.get("severity") or 0))[:40]
        splaces = [p for p in _cached_board('load_places') if not p.get("shared")]
    except Exception:
        srows, splaces = [], []
    opts = {f"👁 {r['title']}": (r["lat"], r["lon"]) for r in srows}
    opts.update({f"⭐ {p['name']}": (p["lat"], p["lon"]) for p in splaces})
    opts["(enter coordinates)"] = None
    where = st.selectbox("Where", list(opts))
    if opts[where] is None:
        c_a, c_b = st.columns(2)
        s_lat = c_a.number_input("Lat", -90.0, 90.0, 37.4)
        s_lon = c_b.number_input("Lon", -180.0, 180.0, -122.1)
    else:
        s_lat, s_lon = opts[where]
    from haunted.world import RECOMMENDED, SAT_CHANNELS
    kind_of = {f"👁 {r['title']}": r.get("kind") for r in srows}
    rec = RECOMMENDED.get(kind_of.get(where) or "default", RECOMMENDED["default"])
    chans = st.multiselect("Channels (recommended for this disaster pre-selected)", list(SAT_CHANNELS), default=rec)
    for ch in chans:
        st.caption(f"**{ch}**: {SAT_CHANNELS[ch][0]}")
    if st.button("🛰 Show satellite view"):
        for ch in chans:
            show_satellite(s_lat, s_lon, ch)
