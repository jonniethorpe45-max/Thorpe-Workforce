#!/usr/bin/env bash
# Create jonniethorpe45-max/ScoutAI on GitHub and push this folder as the new repo root.
# Requires: GitHub CLI authenticated as a user/PAT that can create repositories
# (the Cursor GitHub App install token cannot create repos).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER="${SCOUTAI_GITHUB_OWNER:-jonniethorpe45-max}"
REPO="${SCOUTAI_GITHUB_REPO:-ScoutAI}"
VISIBILITY="${SCOUTAI_VISIBILITY:-public}"
FULL_NAME="${OWNER}/${REPO}"

cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "error: GitHub CLI (gh) is required" >&2
  exit 1
fi

if gh repo view "$FULL_NAME" >/dev/null 2>&1; then
  echo "Repository already exists: https://github.com/${FULL_NAME}"
else
  echo "Creating https://github.com/${FULL_NAME} (${VISIBILITY})..."
  gh repo create "$FULL_NAME" "--${VISIBILITY}" \
    --description "ScoutAI — AI research and scouting assistant" \
    --disable-wiki
fi

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

# Fresh history whose root is this scoutai/ folder (not Thorpe-Workforce).
rsync -a \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '.venv' \
  --exclude 'frontend/.next' \
  --exclude 'frontend/node_modules' \
  --exclude '.env' \
  "$ROOT"/ "$TMP"/

cd "$TMP"
git init -b main
git add .
git commit -m "Initial commit: ScoutAI research scout scaffold"

if git remote get-url origin >/dev/null 2>&1; then
  git remote remove origin
fi
git remote add origin "https://github.com/${FULL_NAME}.git"

echo "Pushing main to origin..."
git push -u origin main

echo
echo "Done."
echo "  Repo: https://github.com/${FULL_NAME}"
echo "Next: connect this repo in Cursor Cloud Agents so ScoutAI is the primary workspace."
