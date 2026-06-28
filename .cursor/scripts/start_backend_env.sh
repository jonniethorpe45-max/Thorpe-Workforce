#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}/backend"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "backend/.venv not found; running install script once."
  bash "${ROOT_DIR}/.cursor/scripts/install_backend_env.sh"
fi

PYTHON_CMD="python3"
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  PYTHON_CMD="python"
fi

export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"

echo "Backend cloud agent environment ready."
${PYTHON_CMD} --version
${PYTHON_CMD} -m pytest --version
echo "Working directory: $(pwd)"
echo "Try: ${PYTHON_CMD} -m pytest"
