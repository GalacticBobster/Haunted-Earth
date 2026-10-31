#!/usr/bin/env bash
# Start scout, analyst, narrator in the background (logs in logs/).
cd "$(dirname "$0")"
mkdir -p logs
SAMPLE=""; [ "${1:-live}" = "sample" ] && SAMPLE="--sample"
LITE=""; [ "${2:-}" = "lite" ] && LITE=1   # lite: 7 agents for demos on a laptop
echo "Setting up Agent Relay agents and channels (once)..."
uv run python -c "from haunted import relay; relay.setup()" || { echo "Agent Relay setup failed: is it running? (agent-relay init --tools none)"; exit 1; }
nohup uv run python -m haunted.agents scout $SAMPLE > logs/scout.log 2>&1 &   echo $! > logs/scout.pid
nohup uv run python -m haunted.agents analyst       > logs/analyst.log 2>&1 & echo $! > logs/analyst.pid
[ -z "$LITE" ] && nohup uv run python -m haunted.agents narrator      > logs/narrator.log 2>&1 & echo $! > logs/narrator.pid
nohup uv run python -m haunted.agents herald $SAMPLE                 > logs/herald.log 2>&1 &        echo $! > logs/herald.pid
nohup uv run python -m haunted.agents checker --role seismologist  > logs/seismologist.log 2>&1 &  echo $! > logs/seismologist.pid
[ -z "$LITE" ] && nohup uv run python -m haunted.agents checker --role meteorologist > logs/meteorologist.log 2>&1 & echo $! > logs/meteorologist.pid
[ -z "$LITE" ] && nohup uv run python -m haunted.agents checker --role spaceweather  > logs/spaceweather.log 2>&1 &  echo $! > logs/spaceweather.pid
nohup uv run python -m haunted.agents judge                         > logs/judge.log 2>&1 &         echo $! > logs/judge.pid
[ -z "$LITE" ] && nohup uv run python -m haunted.agents corroborator $SAMPLE           > logs/corroborator.log 2>&1 &  echo $! > logs/corroborator.pid
[ -z "$LITE" ] && nohup uv run python -m haunted.agents sentinel $SAMPLE               > logs/sentinel.log 2>&1 &      echo $! > logs/sentinel.pid
nohup uv run python -m haunted.agents warden $SAMPLE                 > logs/warden.log 2>&1 &        echo $! > logs/warden.pid
nohup uv run python -m haunted.agents quartermaster $SAMPLE          > logs/quartermaster.log 2>&1 & echo $! > logs/quartermaster.pid
echo "12 agents started. Watch them: tail -f logs/*.log"
