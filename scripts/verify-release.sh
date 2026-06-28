#!/usr/bin/env bash
# Verify a GitHub Release has all expected Thorpe installer artifacts.
set -euo pipefail

TAG="${1:-}"
if [[ -z "$TAG" ]]; then
  echo "Usage: $0 <tag>   e.g. $0 v1.1.0" >&2
  exit 1
fi

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Tag must look like v1.1.0 (got: $TAG)" >&2
  exit 1
fi

VERSION="${TAG#v}"
REPO="${THORPE_GITHUB_REPO:-jonniethorpe45-max/Thorpe-Workforce}"
API="https://api.github.com/repos/${REPO}/releases/tags/${TAG}"

echo "Fetching release ${TAG} from ${REPO}..."

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required. Install jq and retry." >&2
  exit 1
fi

RESPONSE="$(curl -fsSL \
  -H "Accept: application/vnd.github+json" \
  -H "User-Agent: Thorpe-verify-release" \
  "${API}" 2>/dev/null || true)"

if [[ -z "$RESPONSE" ]] || echo "$RESPONSE" | jq -e '.message' >/dev/null 2>&1; then
  MSG="$(echo "$RESPONSE" | jq -r '.message // "unknown error"' 2>/dev/null || echo "request failed")"
  echo "Failed to fetch release: ${MSG}" >&2
  exit 1
fi

DRAFT="$(echo "$RESPONSE" | jq -r '.draft')"
if [[ "$DRAFT" == "true" ]]; then
  echo "Release ${TAG} is still a draft — publish before verifying." >&2
  exit 1
fi

EXPECTED=(
  "Thorpe_${VERSION}_x64-setup.exe"
  "Thorpe_${VERSION}_x64_en-US.msi"
  "Thorpe_${VERSION}_aarch64.dmg"
  "Thorpe_${VERSION}_amd64.AppImage"
  "Thorpe_${VERSION}_amd64.deb"
)

ASSET_NAMES="$(echo "$RESPONSE" | jq -r '.assets[].name')"
MISSING=0

for file in "${EXPECTED[@]}"; do
  if echo "$ASSET_NAMES" | grep -qxF "$file"; then
    echo "ok: $file"
  else
    echo "missing: $file" >&2
    MISSING=1
  fi
done

TAG_NAME="$(echo "$RESPONSE" | jq -r '.tag_name')"
HTML_URL="$(echo "$RESPONSE" | jq -r '.html_url')"

if [[ "$MISSING" -ne 0 ]]; then
  echo "" >&2
  echo "Release ${TAG_NAME} is incomplete. Assets found:" >&2
  echo "$ASSET_NAMES" | sed 's/^/  - /' >&2
  echo "URL: ${HTML_URL}" >&2
  exit 1
fi

echo ""
echo "Release ${TAG_NAME} has all ${#EXPECTED[@]} expected installers."
echo "${HTML_URL}"
