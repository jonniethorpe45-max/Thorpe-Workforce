#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must be run on macOS (requires hdiutil)."
  exit 1
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found. Please run this on macOS."
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_SCRIPT="$ROOT_DIR/scripts/macos/ThorpeWorkforceLaunchAssistant.command"
PROFILE_EXAMPLE="$ROOT_DIR/scripts/macos/launch-assistant.profile.example"
OUTPUT_DMG="$ROOT_DIR/ThorpeWorkforceLaunchAssistant.dmg"
VOL_NAME="Thorpe Workforce Launch Assistant"
TMP_DIR="$(mktemp -d)"
PAYLOAD_DIR="$TMP_DIR/payload"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$PAYLOAD_DIR"
cp "$SOURCE_SCRIPT" "$PAYLOAD_DIR/ThorpeWorkforceLaunchAssistant.command"
cp "$PROFILE_EXAMPLE" "$PAYLOAD_DIR/launch-assistant.profile.example"
chmod +x "$PAYLOAD_DIR/ThorpeWorkforceLaunchAssistant.command"

cat >"$PAYLOAD_DIR/README.txt" <<'TXT'
Thorpe Workforce Launch Assistant
=================================

1) Double-click ThorpeWorkforceLaunchAssistant.command
2) (Optional) copy launch-assistant.profile.example to launch-assistant.profile and set your domains
3) Choose menu options to complete:
   - preflight checks
   - env template creation
   - deployment env var generation
   - local stack startup
   - deployed smoke checks
   - opening deployment dashboards

Tip:
- If your repo is not at ~/Thorpe-Workforce, choose menu option 1 first.
TXT

hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$PAYLOAD_DIR" \
  -ov \
  -format UDZO \
  "$OUTPUT_DMG"

echo "Created: $OUTPUT_DMG"
