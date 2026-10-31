#!/usr/bin/env bash
# Start scout, analyst, narrator in the background (logs in logs/).
cd "$(dirname "$0")"
mkdir -p logs
SAMPLE=""; [ "${1:-live}" = "sample" ] && SAMPLE="--sample"
nohup uv run python -m haunted.agents scout $SAMPLE > logs/scout.log 2>&1 &   echo $! > logs/scout.pid
nohup uv run python -m haunted.agents analyst       > logs/analyst.log 2>&1 & echo $! > logs/analyst.pid
nohup uv run python -m haunted.agents narrator      > logs/narrator.log 2>&1 & echo $! > logs/narrator.pid
echo "agents started: tail -f logs/scout.log logs/analyst.log logs/narrator.log"
