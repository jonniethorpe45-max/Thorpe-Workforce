#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OWNER="${SCOUTAI_GITHUB_OWNER:-jonniethorpe45-max}"
REPO="${SCOUTAI_GITHUB_REPO:-ScoutAI}"
BRANCH="${SCOUTAI_PUSH_BRANCH:-cursor/scoutai-stage3-foundation-834e}"
cd "$ROOT"
if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI required" >&2
  exit 1
fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
tar -C "$ROOT" \
  --exclude='.git' --exclude='node_modules' --exclude='*/node_modules' \
  --exclude='dist' --exclude='*/dist' --exclude='.next' --exclude='*/.next' \
  --exclude='.turbo' --exclude='.env' --exclude='apps/web/.env.local' \
  -cf - . | tar -C "$TMP" -xf -
cd "$TMP"
git init -b "$BRANCH"
git add .
git -c user.email="scoutai-builder@local" -c user.name="ScoutAI Builder" commit -m "feat(stage3): repository foundation and build bootstrap"
git remote add origin "https://github.com/${OWNER}/${REPO}.git"
git push -u origin "$BRANCH"
echo "Pushed ${BRANCH} to https://github.com/${OWNER}/${REPO}"
