#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

if [[ "${RUN_MIGRATIONS_ON_BOOT:-false}" == "true" ]]; then
  python -m alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
