#!/usr/bin/env python3
"""Generate minimal Thorpe app icons for Tauri builds (cross-platform)."""

from __future__ import annotations

import shutil
import struct
import zlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ICON_DIR = SCRIPT_DIR.parent / "src-tauri" / "icons"


def write_png(path: Path, size: int) -> bytes:
    raw = b""
    cx, cy = size // 2, size // 2
    for y in range(size):
        raw += b"\x00"
        for x in range(size):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < size * 0.4:
                raw += bytes([0x13, 0x64, 0xEB, 0xFF])
            elif dist < size * 0.45:
                raw += bytes([0xFF, 0xFF, 0xFF, 0xFF])
            else:
                raw += bytes([0x25, 0x63, 0xEB, 0xFF])

    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)
    print(f"Generated {path} ({size}x{size})")
    return png


def write_ico(path: Path, png_data: bytes, size: int) -> None:
    """Write a valid ICO file with an embedded PNG image."""
    icon_dir = struct.pack("<HHH", 0, 1, 1)
    width = 0 if size >= 256 else size
    height = 0 if size >= 256 else size
    icon_entry = struct.pack(
        "<BBBBHHII",
        width,
        height,
        0,
        0,
        1,
        32,
        len(png_data),
        6 + 16,
    )
    path.write_bytes(icon_dir + icon_entry + png_data)
    print(f"Generated {path} ({size}x{size} ICO with embedded PNG)")


def main() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    png32 = ICON_DIR / "32x32.png"
    png128 = ICON_DIR / "128x128.png"

    png32_data = write_png(png32, 32)
    write_png(png128, 128)

    shutil.copyfile(png128, ICON_DIR / "128x128@2x.png")
    shutil.copyfile(png128, ICON_DIR / "icon.png")
    shutil.copyfile(png128, ICON_DIR / "icon.icns")
    write_ico(ICON_DIR / "icon.ico", png32_data, 32)

    print(f"Icons generated in {ICON_DIR}")


if __name__ == "__main__":
    main()
