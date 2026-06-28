#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Thorpe complete E2E =="
echo ""

echo ">> Version alignment"
bash scripts/check-versions.sh
echo ""

echo ">> Rust unit tests"
(cd src-tauri && cargo test)
echo ""

echo ">> License server smoke tests"
(cd tools/license-server && python3 test_server.py)
echo ""

echo ">> Frontend lint"
npm run lint
echo ""

echo ">> Frontend E2E (Vitest)"
npm run test:e2e
echo ""

echo "== All E2E checks passed =="
