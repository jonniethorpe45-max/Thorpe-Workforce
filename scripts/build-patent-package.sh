#!/usr/bin/env bash
# Thin wrapper — use Node build for cross-platform support (Windows/macOS/Linux).
set -euo pipefail
cd "$(dirname "$0")/.."
exec node scripts/build-patent-package.mjs
