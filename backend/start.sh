#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ -z "$PORT" ]; then
  export PORT=8000
fi

export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting Yaqidh API on port $PORT..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
