#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH." >&2
  exit 1
fi

python3 -m venv backend/.venv
source backend/.venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend/requirements.txt

# Explicitly ensure common test/runtime tools are available.
python -m pip install --upgrade pytest fastapi "uvicorn[standard]"

echo "Cloud agent backend dependencies installed."
