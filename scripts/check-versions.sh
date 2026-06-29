#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PKG_VERSION="$(node -p "require('./package.json').version")"
CARGO_VERSION="$(grep '^version' src-tauri/Cargo.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')"
TAURI_VERSION="$(node -p "require('./src-tauri/tauri.conf.json').version")"
TS_VERSION="$(grep 'THORPE_VERSION' src/config/version.ts | sed 's/.*"\(.*\)".*/\1/')"

fail=0
check() {
  local name="$1"
  local value="$2"
  if [[ "$value" != "$PKG_VERSION" ]]; then
    echo "version mismatch: $name is $value (expected $PKG_VERSION)" >&2
    fail=1
  else
    echo "ok: $name = $value"
  fi
}

check "package.json" "$PKG_VERSION"
check "Cargo.toml" "$CARGO_VERSION"
check "tauri.conf.json" "$TAURI_VERSION"
check "src/config/version.ts" "$TS_VERSION"

if ! grep -q "THORPE_RELEASES_PAGE\|getReleaseDownloads\|get_release_downloads" src/config/downloads.ts src/services/tauri.ts 2>/dev/null; then
  if ! grep -q "THORPE_VERSION" src/config/downloads.ts; then
    echo "version mismatch: downloads.ts must expose release download resolution" >&2
    fail=1
  else
    echo "ok: downloads.ts uses THORPE_VERSION"
  fi
else
  echo "ok: release downloads resolved via GitHub API"
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi

echo "All version sources aligned at ${PKG_VERSION}"
