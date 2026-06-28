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
RUN_SMOKE_CHECKS_ON_START="${RUN_SMOKE_CHECKS_ON_START:-true}"
SMOKE_BACKEND_TEST_PATH="${SMOKE_BACKEND_TEST_PATH:-tests/test_options_bot.py}"

echo "Full-stack cloud agent environment ready."
echo "Repository root: ${ROOT_DIR}"
${PYTHON_CMD} --version
${PYTHON_CMD} -m pytest --version
node --version
npm --version

if [[ "${RUN_SMOKE_CHECKS_ON_START}" == "true" ]]; then
  echo "Running startup smoke checks..."
  (
    cd "${ROOT_DIR}/backend"
    ${PYTHON_CMD} -m pytest "${SMOKE_BACKEND_TEST_PATH}"
  )
  (
    cd "${ROOT_DIR}/frontend"
    npm run lint
  )
  echo "Startup smoke checks passed."
else
  echo "Startup smoke checks skipped (RUN_SMOKE_CHECKS_ON_START=false)."
fi

echo "Manual verify commands:"
echo "  Backend tests: cd backend && ${PYTHON_CMD} -m pytest"
echo "  Frontend lint: cd frontend && npm run lint"
echo "  Frontend build: cd frontend && npm run build"
