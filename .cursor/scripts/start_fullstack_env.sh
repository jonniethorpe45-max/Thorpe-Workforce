#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f "${ROOT_DIR}/backend/.venv/bin/activate" || ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo "Missing backend/frontend dependencies; running full-stack install once."
  bash "${ROOT_DIR}/.cursor/scripts/install_fullstack_env.sh"
fi

PYTHON_CMD="python3"
if [[ -f "${ROOT_DIR}/backend/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/backend/.venv/bin/activate"
  PYTHON_CMD="python"
fi

export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"

echo "Full-stack cloud agent environment ready."
echo "Repository root: ${ROOT_DIR}"
${PYTHON_CMD} --version
${PYTHON_CMD} -m pytest --version
node --version
npm --version

echo "Quick verify commands:"
echo "  Backend tests: cd backend && ${PYTHON_CMD} -m pytest"
echo "  Frontend lint: cd frontend && npm run lint"
echo "  Frontend build: cd frontend && npm run build"
