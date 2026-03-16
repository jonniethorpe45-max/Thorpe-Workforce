#!/usr/bin/env bash
set -euo pipefail

# Allow toggling migration/seed behavior from Railway variables.
RUN_MIGRATIONS_ON_START="${RUN_MIGRATIONS_ON_START:-true}"
RUN_SEEDS_ON_START="${RUN_SEEDS_ON_START:-false}"
PORT="${PORT:-8000}"
# Railway private networking is IPv6-aware; default to dual-stack bind.
UVICORN_HOST="${UVICORN_HOST:-::}"

if [[ "${RUN_MIGRATIONS_ON_START}" == "true" ]]; then
  alembic upgrade head
fi

if [[ "${RUN_SEEDS_ON_START}" == "true" ]]; then
  python scripts/seed_worker_system.py
  python scripts/seed_demo.py
fi

exec uvicorn app.main:app --host "${UVICORN_HOST}" --port "${PORT}" --proxy-headers --forwarded-allow-ips="*"
