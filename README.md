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
| `app.py` | Streamlit + Plotly | Orthographic globe of eyes (size = severity, fades as events die), stories, live agent chatter. |

## Setup on a Mac

```bash
brew install uv node            # skip what you already have
npm install -g agent-relay
cd haunted-earth
cp .env.example .env            # then put your SUPABASE_URL and SUPABASE_KEY in it
uv sync                         # installs Python deps into .venv
```

Supabase tables (run once in the SQL Editor, "Run without RLS"): see `supabase.sql`.

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
USGS Earthquake Hazards Program feeds · NASA EONET v3 · NOAA SWPC planetary K-index. All public, no keys.
Physics: Gutenberg-Richter energy relation; Båth (1965); Reasenberg & Jones (1989) generic California parameters.
These are rough, illustrative estimates, not official forecasts.
