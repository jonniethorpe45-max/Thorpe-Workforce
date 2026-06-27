#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running Thorpe test suite..."

# Frontend tests
npm run test

# Rust tests (if cargo available)
if command -v cargo &>/dev/null; then
  echo "Running Rust tests..."
  cd src-tauri && cargo test && cd ..
fi

echo "All tests passed."
