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

st.set_page_config(page_title="Haunted Earth", page_icon="🎃", layout="wide")

COLORS = {
    "earthquake": "#ff7a1a", "wildfire": "#ff3b3b", "volcano": "#ffb000", "storm": "#9b5cff",
    "flood": "#3fa9ff", "aurora": "#39ff88", "ice": "#c8e8ff",
}
OPACITY = {"awake": 1.0, "fading": 0.45, "closed": 0.12}

st.markdown(
    """
    <style>
      .stApp { background: radial-gradient(circle at 50% 0%, #1b1030 0%, #07050d 60%); }
      h1, h2, h3, p, label, .stMarkdown { color: #f3e9ff !important; }
      .story { font-size: 1.05rem; font-style: italic; color: #ffd8a8; }
      .chat  { font-family: ui-monospace, monospace; font-size: 0.8rem; color: #cbb8e6;
               border-left: 2px solid #ff7a1a33; padding-left: 8px; margin: 4px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎃 Haunted Earth")
st.caption("Every live quake, fire, volcano and storm is a persistent ghost. "
           "Agents watch the feeds, physics checks the facts, the narrator tells the tale.")

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    look = st.selectbox("Look at", ["Pacific", "Americas", "Europe/Africa", "Asia", "North Pole"])
with c2:
    show_closed = st.toggle("Show closed eyes", value=False)
with c3:
    kinds_filter = st.multiselect("Kinds", list(COLORS), default=[])

CENTER = {"Pacific": (10, -160), "Americas": (20, -95), "Europe/Africa": (20, 15),
          "Asia": (25, 105), "North Pole": (75, -100)}


def globe(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
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


@st.fragment(run_every=5)
def live():
    try:
        rows = board.load_haunts()
        chatter = board.load_chatter(20)
    except Exception as exc:
        st.error(f"Board unreachable: {exc}")
        return
    if not rows:
        st.info("No haunts yet. Start the agents (./run_all.sh) and wait for the first scout pass.")
        return
    df = pd.DataFrame(rows)
    for c in ("story", "verdict"):
        df[c] = df.get(c, pd.Series(dtype=str)).fillna("")
    if not show_closed:
        df = df[df.status != "closed"]
    if kinds_filter:
        df = df[df.kind.isin(kinds_filter)]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👁 Eyes open", int((df.status == "awake").sum()))
    m2.metric("🌫 Fading", int((df.status == "fading").sum()))
    m3.metric("🧪 Verdicts", int((df.verdict != "").sum()))
    m4.metric("📜 Stories", int((df.story != "").sum()))

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(globe(df), use_container_width=True, key="globe")
    with right:
        st.subheader("Most restless spirits")
        top = df[df.story != ""].sort_values("severity", ascending=False).head(4)
        for _, r in top.iterrows():
            st.markdown(f"**{r.title}**  \n<span class='story'>{r.story}</span>", unsafe_allow_html=True)
            with st.expander("Analyst's verdict (physics)"):
                st.write(r.verdict)
        st.subheader("Agent chatter (via Agent Relay)")
        for c in chatter[:12]:
            msg = c.get("message", "")
            msg = msg.split("] ", 1)[-1] if msg.startswith("[id=") else msg
            st.markdown(f"<div class='chat'><b>{c.get('sender')}</b>: {msg[:180]}</div>",
                        unsafe_allow_html=True)
    st.caption(f"Board: {board.mode()} · {len(rows)} haunts remembered · refreshes every 5 s · "
               "Data: USGS, NASA EONET, NOAA SWPC")


live()
