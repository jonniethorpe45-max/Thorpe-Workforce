#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/.dev-logs"
mkdir -p "$LOG_DIR"

if [[ -x "$ROOT/.venv/bin/uvicorn" ]]; then
  UVICORN="$ROOT/.venv/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
  UVICORN="$(command -v uvicorn)"
else
  echo "uvicorn not found. Create a venv first:"
  echo "  cd genesis && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

start() {
  local name="$1"
  local dir="$2"
  local port="$3"
  echo "Starting $name on :$port"
  (
    cd "$ROOT/$dir"
    "$UVICORN" app.main:app --host 127.0.0.1 --port "$port" >"$LOG_DIR/$name.log" 2>&1
  ) &
  echo $! >"$LOG_DIR/$name.pid"
}

start knowledge-graph services/knowledge-graph 8001
start identity services/identity 8002
start capability-registry services/capability-registry 8003
start mock-calendar services/mock-calendar 8004
start model-router services/model-router 8005
start jonathan-core services/jonathan-core 8000
start api-gateway services/api-gateway 7999

echo "Services starting. Logs in $LOG_DIR"
echo "Gateway: http://127.0.0.1:7999/health"
