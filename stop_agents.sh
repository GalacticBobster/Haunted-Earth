#!/usr/bin/env bash
# Kill the three agents (the crash demo). Actors and globe keep running.
cd "$(dirname "$0")"
for a in scout analyst narrator; do
  [ -f logs/$a.pid ] && kill "$(cat logs/$a.pid)" 2>/dev/null && echo "killed $a"
  rm -f logs/$a.pid
done
