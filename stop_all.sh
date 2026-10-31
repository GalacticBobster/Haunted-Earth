#!/usr/bin/env bash
cd "$(dirname "$0")"
./stop_agents.sh
[ -f logs/actors.pid ] && kill "$(cat logs/actors.pid)" 2>/dev/null && echo "stopped actor server"
rm -f logs/actors.pid
agent-relay init --stop >/dev/null 2>&1 && echo "stopped Agent Relay"
