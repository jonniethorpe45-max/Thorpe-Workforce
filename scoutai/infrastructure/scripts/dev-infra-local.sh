#!/usr/bin/env bash
# Fallback when Docker is unavailable: ensure local PostgreSQL + Redis are running.
set -euo pipefail

echo "[dev-infra-local] Ensuring local PostgreSQL and Redis..."

if command -v pg_isready >/dev/null 2>&1; then
  if ! pg_isready -q; then
    if command -v service >/dev/null 2>&1; then
      sudo service postgresql start || true
    fi
  fi
  pg_isready
else
  echo "PostgreSQL client tools not found" >&2
  exit 1
fi

if ! redis-cli ping >/dev/null 2>&1; then
  if command -v service >/dev/null 2>&1; then
    sudo service redis-server start || true
  fi
fi
redis-cli ping

echo "[dev-infra-local] Ready."
echo "DATABASE_URL=postgresql://scoutai:scoutai@127.0.0.1:5432/scoutai?schema=public"
echo "REDIS_URL=redis://127.0.0.1:6379"
