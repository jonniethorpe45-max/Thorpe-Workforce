#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found on PATH." >&2
  exit 1
fi

PYTHON_CMD="python3"
PIP_CMD="python3 -m pip"
VENV_CREATED="false"

if python3 -m venv backend/.venv >/tmp/cursor_venv_setup.log 2>&1; then
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
  PYTHON_CMD="python"
  PIP_CMD="python -m pip"
  VENV_CREATED="true"
else
  rm -rf backend/.venv || true
  echo "python3-venv unavailable; using system Python environment fallback."
fi

${PIP_CMD} install --upgrade pip setuptools wheel
${PIP_CMD} install -r backend/requirements.txt

# Explicitly ensure common test/runtime tools are available.
${PIP_CMD} install --upgrade pytest fastapi "uvicorn[standard]"

if [[ "${VENV_CREATED}" == "true" ]]; then
  echo "Cloud agent backend dependencies installed in backend/.venv."
else
  echo "Cloud agent backend dependencies installed in system Python fallback."
fi

${PYTHON_CMD} --version
