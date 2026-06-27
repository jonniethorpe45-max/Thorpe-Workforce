#!/usr/bin/env bash
set -euo pipefail

# Generate minimal placeholder icons for Tauri builds
ICON_DIR="$(dirname "$0")/../src-tauri/icons"
mkdir -p "$ICON_DIR"

# Minimal 32x32 PNG (blue square) - base64 encoded
generate_png() {
  local size=$1
  local outfile=$2
  python3 -c "
import struct, zlib, sys

size = $size
# Create RGBA image data (blue #1364e1)
raw = b''
for y in range(size):
    raw += b'\x00'  # filter byte
    for x in range(size):
        # Simple shield-like pattern
        cx, cy = size//2, size//2
        dist = ((x-cx)**2 + (y-cy)**2)**0.5
        if dist < size*0.4:
            raw += bytes([0x13, 0x64, 0xe1, 0xff])
        elif dist < size*0.45:
            raw += bytes([0xff, 0xff, 0xff, 0xff])
        else:
            raw += bytes([0x13, 0x64, 0xe1, 0xff])

def chunk(ctype, data):
    c = ctype + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)
png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', ihdr)
png += chunk(b'IDAT', zlib.compress(raw))
png += chunk(b'IEND', b'')

with open('$outfile', 'wb') as f:
    f.write(png)
print(f'Generated $outfile ({size}x{size})')
"
}

generate_png 32 "$ICON_DIR/32x32.png"
generate_png 128 "$ICON_DIR/128x128.png"
cp "$ICON_DIR/128x128.png" "$ICON_DIR/128x128@2x.png"

# Generate ICO for Windows (use 32x32)
cp "$ICON_DIR/32x32.png" "$ICON_DIR/icon.png"
cp "$ICON_DIR/32x32.png" "$ICON_DIR/icon.ico" 2>/dev/null || cp "$ICON_DIR/32x32.png" "$ICON_DIR/icon.ico"

# ICNS placeholder - copy png (tauri may need proper icns for macOS build)
cp "$ICON_DIR/128x128.png" "$ICON_DIR/icon.icns" 2>/dev/null || true

echo "Icons generated in $ICON_DIR"
