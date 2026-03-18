#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found on PATH." >&2
  exit 1
fi

echo "Installing backend Python dependencies..."
bash "${ROOT_DIR}/.cursor/scripts/install_backend_env.sh"

echo "Installing frontend npm dependencies..."
cd "${ROOT_DIR}/frontend"
if [[ -f "package-lock.json" ]]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi

echo "Frontend dependencies installed."
node --version
npm --version
