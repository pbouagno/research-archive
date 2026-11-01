#!/usr/bin/env bash
# Rebuild, (re)start the local static server and a public tunnel.tunnel.to quick tunnel.
set -e
cd "$(dirname "$0")"
.venv/bin/python build.py
PORT=$(cat .port 2>/dev/null || echo 45399)
if ! curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
  setsid nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$PWD/dist" > server.log 2>&1 < /dev/null &
  sleep 1
fi
if ! pgrep -f "tunnelto expose http://127.0.0.1:$PORT" >/dev/null; then
  setsid nohup tunnel-tools/tunnelto expose "http://127.0.0.1:$PORT" --host-header localhost > tunnelto.log 2>&1 < /dev/null &
  sleep 8
fi
grep -o 'https://[a-z0-9-]*\.tunnel\.to' tunnelto.log | tail -1
