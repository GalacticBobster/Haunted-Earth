#!/usr/bin/env bash
# Start everything: Agent Relay, durable actors, the 3 agents, and the globe.
#   ./run_all.sh          live open data
#   ./run_all.sh sample   offline sample data (if venue Wi-Fi is down)
set -e
cd "$(dirname "$0")"
MODE="${1:-live}"
mkdir -p logs
[ -f .env ] || { echo "Missing .env (copy .env.example and fill in Supabase)"; exit 1; }
export DURABLE_ACTORS_CONTROL_PLANE_URL="${DURABLE_ACTORS_CONTROL_PLANE_URL:-http://127.0.0.1:7100}"

echo "1/5 Agent Relay (local server on :8787)"
agent-relay telemetry disable >/dev/null 2>&1 || true
agent-relay init --tools none > logs/relay.log 2>&1 || { echo "agent-relay failed, see logs/relay.log"; exit 1; }

echo "2/5 Durable actors server (:7100)"
if ! curl -s -o /dev/null "$DURABLE_ACTORS_CONTROL_PLANE_URL"; then
  nohup uv run durable-actors dev --port 7100 > logs/actors.log 2>&1 &
  echo $! > logs/actors.pid
  for i in $(seq 1 60); do curl -s -o /dev/null "$DURABLE_ACTORS_CONTROL_PLANE_URL" && break; sleep 1; done
fi

echo "3/5 Generating typed actor client"
uv run durable-actors generate > logs/generate.log 2>&1

echo "4/5 Starting agents ($MODE)"
./run_agents.sh "$MODE"

echo "5/5 Opening the globe at http://localhost:8501  (Ctrl+C stops the globe only; ./stop_all.sh stops everything)"
uv run streamlit run app.py
