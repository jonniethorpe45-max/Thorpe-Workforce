#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}/backend"

if [[ ! -d ".venv" ]]; then
  echo "backend/.venv not found; running install script once."
  bash "${ROOT_DIR}/.cursor/scripts/install_backend_env.sh"
fi

source .venv/bin/activate
export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"

echo "Backend cloud agent environment ready."
python --version
python -m pytest --version
echo "Working directory: $(pwd)"
echo "Try: python -m pytest"
