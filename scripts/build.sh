#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

echo "=== Thorpe Build Script ==="

# Install dependencies
if [ ! -d "node_modules" ]; then
  echo "Installing npm dependencies..."
  npm install
fi

# Generate icons
bash scripts/generate-icons.sh

# Build frontend
echo "Building frontend..."
npm run build

# Build Tauri app
echo "Building Tauri application..."
npm run tauri:build

echo "=== Build complete ==="
echo "Installers are in src-tauri/target/release/bundle/"
