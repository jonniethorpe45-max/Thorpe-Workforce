#!/usr/bin/env bash
# Build Thorpe patent attorney package: screenshots + combined HTML/PDF
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Installing puppeteer-core (screenshot script)..."
npm install --no-save puppeteer-core@23.11.1

echo "==> Building frontend..."
npm run build

SESSION_NAME="patent-preview"
PREVIEW_PORT="${PATENT_PREVIEW_PORT:-4173}"
PREVIEW_URL="http://127.0.0.1:${PREVIEW_PORT}"

# Start vite preview in tmux if not already serving
if ! curl -sf "$PREVIEW_URL" >/dev/null 2>&1; then
  tmux -f /exec-daemon/tmux.portal.conf has-session -t "=$SESSION_NAME" 2>/dev/null && \
    tmux -f /exec-daemon/tmux.portal.conf kill-session -t "=$SESSION_NAME" || true
  tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION_NAME" -c "$PWD" -- "${SHELL:-bash}" -l
  tmux -f /exec-daemon/tmux.portal.conf send-keys -t "$SESSION_NAME:0.0" \
    "npm run preview -- --host 127.0.0.1 --port ${PREVIEW_PORT}" C-m
  for i in $(seq 1 30); do
  if curl -sf "$PREVIEW_URL" >/dev/null 2>&1; then break; fi
    sleep 1
  done
fi

if ! curl -sf "$PREVIEW_URL" >/dev/null 2>&1; then
  echo "ERROR: Preview server not available at $PREVIEW_URL"
  exit 1
fi

echo "==> Capturing screenshots..."
PATENT_PREVIEW_URL="$PREVIEW_URL" node scripts/capture-patent-screenshots.mjs

echo "==> Exporting combined HTML/PDF..."
node scripts/export-patent-package.mjs

echo ""
echo "Patent package ready:"
echo "  docs/patents/dist/Thorpe-Desktop-Patent-Package.html"
echo "  docs/patents/dist/Thorpe-Desktop-Patent-Package.pdf (if Chrome PDF succeeded)"
echo "  docs/patents/screenshots/*.png"
echo ""
echo "Submit docs/patents/ folder + dist PDF to patent counsel."
