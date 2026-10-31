# 🎃 Haunted Earth

**Every live earthquake, wildfire, volcano and storm on Earth becomes a persistent ghost: an eye that
opens on a globe.** A small factory of agents watches open hazard feeds, checks each event with real
physics, and narrates it, while durable actors remember every ghost's whole life.

Built for *Haunted Hacks: Real-Time AI Edition* (YC, Oct 31 2026).

## How it works

```
 USGS / NASA EONET / NOAA SWPC
            │  every 60 s
            ▼
        ┌────────┐  sight()   ┌──────────────────────────┐  mirror   ┌──────────┐
        │ Scout  │──────────▶ │ Haunt actor (one/event)  │─────────▶ │ Supabase │──▶ Streamlit globe
        └────────┘            │ Terse durable actor:     │           │ haunts,  │    (app.py)
            │ #sightings      │ state, history, verdict, │           │ chatter  │
            ▼                 │ story; 1 call at a time; │           └──────────┘
        ┌─────────┐           │ survives crashes         │
        │ Analyst │──verdict─▶│                          │
        └─────────┘           └──────────────────────────┘
            │ #verdicts               ▲
            ▼                         │ story
        ┌──────────┐──────────────────┘
        │ Narrator │──▶ #stories
        └──────────┘
   (agents talk over Agent Relay channels)
```

| Piece | Tool | Job |
|---|---|---|
| `src/actors.py` | **Terse durable actors** | `Haunt` per event (id = event id) holds status, severity history, verdict, story. `Globe("earth")` remembers every haunt ever seen. |
| `haunted/relay.py` | **Agent Relay** | Channels `#sightings` → `#verdicts` → `#stories` between the three agents. |
| `haunted/board.py` | **Supabase** | Tables `haunts` and `chatter`; the globe reads only from here. |
| `haunted/physics.py` | Science | Quake energy (log E = 1.5M + 4.8), Båth's law, Reasenberg-Jones aftershock odds, aurora oval edge from Kp, neighbours within 300 km. |
| `haunted/llm.py` | OpenAI / Ollama | Narrator rewrites the verdict as one spooky line. **Numbers come from physics, never from the LLM.** |
| `haunted/news.py`, `haunted/factcheck.py` | Newsroom | Headline search, claim extraction, specialist physics checks, Beta-binomial credibility. |
| `app.py` | Streamlit + Plotly | Orthographic globe of eyes, plus tabs: Spirits, Fact-check desk, Outlet ledger, Chatter. |

## The newsroom: physics fact-checks the news

| Agent | Job |
|---|---|
| **Herald** | For the 8 biggest live haunts, pulls headlines (GDELT + Google News RSS, no keys) every 15 min and extracts numeric claims (magnitude, depth, aftershock, tsunami, wind, Saffir-Simpson category, G-scale, Kp). Posts `#news`. |
| **Seismologist** | Checks quake claims against USGS. A wrong magnitude is reported as an **energy error** (M6.6 vs M6.1 = 5.6× the energy); an "aftershock M5.2" is tested with **Reasenberg-Jones odds** for the elapsed time; "tsunami" claims get a physical plausibility test (needs ~M7+, shallow). |
| **Meteorologist** | Converts mph / km/h to knots, compares to official sustained winds, tells **gusts from sustained winds**, and checks the Saffir-Simpson category. |
| **Space-weather** | Checks G-scale / Kp claims against NOAA SWPC, and separates **forecast watches** from current conditions. |
| **Judge** | Keeps a durable **credibility ledger per outlet** (one `Outlet` actor each): Beta-binomial mean ± 1σ, so one lucky headline doesn't make an outlet "100% reliable". |

Verdicts: ✅ CONFIRMED · 🟡 PLAUSIBLE · ❌ MISMATCH · 🚫 IMPLAUSIBLE · ❔ UNVERIFIABLE.
The LLM may help *find* claims, but **every verdict is physics**, never the LLM.

## More eyes: global agencies and county alerts

| Agent | Job |
|---|---|
| **Corroborator** | Polls **EMSC** (Europe/Africa/Mediterranean), **JMA** (Japan) and **GDACS** (UN/EU) on its own, matches each report to the same USGS quake (≤120 s, ≤150 km), and combines magnitudes by **inverse-variance weighting** with a **χ² consistency test**: it flags quakes where agencies disagree beyond their typical error (and notes JMA's Mj vs Mw). Quakes other agencies see but USGS hasn't listed become **new ghosts** (`xq-…`), e.g. Ethiopia's Afar rift. |
| **Sentinel** | US **county alert board** from NWS active alerts (county FIPS codes), and links any alert whose area is centred within 100 km of a live haunt, e.g. *Red Flag Warning in Ventura County near an active fire*. Links are stored once per haunt in its durable actor. |
| **Scout (extended)** | Adds **GDACS** global hazards (cyclones, floods, droughts, volcanoes with green/orange/red alert levels), deduplicated against NASA EONET. |

Not included: ECMWF (forecast model fields, not disaster reports), India IMD/NCS (no stable public API; GDACS covers India), NASA FIRMS (needs a free MAP_KEY).

## The warning system (Warden)

Add your places in the sidebar. The **Warden** gives each place its own durable `Place` actor and issues
**Advisory / Watch / Warning** levels, alerting only when something is *issued, upgraded, downgraded or
expired*, the way real warning systems avoid alert fatigue.

| Hazard | Physics at your place |
|---|---|
| Earthquake | Shaking intensity (MMI) from the Atkinson & Wald (2007) intensity prediction equation; **early-warning seconds** = S-wave arrival − (P at nearest stations + 4 s), with Vp 6.5 / Vs 3.75 km/s, or "blind zone". |
| Tsunami (coastal places) | For M ≥ 7, shallow quakes: arrival time from the shallow-water wave speed √(g·h), h = 4 km (~713 km/h). |
| Tropical cyclone | Storm motion from its last track segment → closest approach and arrival time; wind at your place from a modified Rankine vortex; NHC-style lead times (watch 48 h, warning 36 h). |
| Humid heat | Stull (2011) wet-bulb temperature from the Open-Meteo 48 h forecast; Advisory ≥ 27 °C, Watch ≥ 29 °C, Warning ≥ 31 °C. |
| Wind | Forecast gusts: Advisory ≥ 65, Watch ≥ 90, Warning ≥ 110 km/h. |
| Aurora | Your geomagnetic latitude (dipole) vs the auroral oval edge from Kp. |
| Official (US) | Active NWS alerts at your exact point. |

These are transparent demo estimates, **not official warnings**.

## Setup on a Mac

```bash
brew install uv node            # skip what you already have
npm install -g agent-relay
cd haunted-earth
cp .env.example .env            # then put your SUPABASE_URL and SUPABASE_KEY in it
uv sync                         # installs Python deps into .venv
```

Supabase tables (run once in the SQL Editor, "Run without RLS"): see `supabase.sql`
(`haunts`, `chatter`, the newsroom's `factchecks`, `outlets`, and v3's `county_alerts` + `haunts.consensus`).

## Run

```bash
./run_all.sh            # live open data
./run_all.sh sample     # offline sample data, if Wi-Fi is bad
```
Open http://localhost:8501. First scout pass takes ~30-60 s. Logs: `tail -f logs/*.log`.

Optional narrator LLM: put `OPENAI_API_KEY=...` in `.env`, or run Ollama (`ollama serve` + `ollama pull gpt-oss:20b`).
With neither, a template narrator is used so the demo never breaks.

## The crash demo (why durable actors)

```bash
./stop_agents.sh        # kill all three agents mid-run
./run_agents.sh         # bring them back
```
The scout log says `start #2; globe already remembers N haunts`: nothing is re-analyzed or lost,
because every haunt's state lives in its own durable actor, and each actor handles one call at a time,
so agents can never overwrite each other.

`./stop_all.sh` stops everything.

## Data sources
USGS Earthquake Hazards Program · NASA EONET v3 · NOAA SWPC K-index · GDACS · EMSC seismicportal FDSN · JMA quake list · NWS active alerts · GDELT DOC 2.0 · Google News RSS. All public, no keys.
Physics: Gutenberg-Richter energy relation; Båth (1965); Reasenberg & Jones (1989) generic California parameters;
NHC Saffir-Simpson scale; NOAA G-scale. Sample mode uses invented `.example` outlets and headlines for testing.
These are rough, illustrative estimates, not official forecasts.
