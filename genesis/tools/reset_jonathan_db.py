#!/usr/bin/env python3
"""Reset Jonathan Core SQLite database."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "services" / "jonathan-core" / "jonathan_core.sqlite3"

if DB.exists():
    DB.unlink()
    print(f"Deleted {DB}")
else:
    print(f"No database at {DB}")
