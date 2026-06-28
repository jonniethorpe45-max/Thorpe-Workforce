"""Shared license key helpers for the Thorpe license server."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets

SECRET = os.environ.get("THORPE_LICENSE_SIGNING_SECRET", "thorpe-license-signing-key-v1")
KEY_PATTERN = re.compile(r"^(PRO|ENT)-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]{4}$")


def license_checksum(body: str) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return digest[:2].hex().upper()


def generate_license_key(tier: str) -> str:
    prefix = "PRO" if tier == "professional" else "ENT"
    g1 = secrets.token_hex(2).upper()[:4]
    g2 = secrets.token_hex(2).upper()[:4]
    g3 = secrets.token_hex(2).upper()[:4]
    body = f"{prefix}-{g1}-{g2}-{g3}"
    return f"{body}-{license_checksum(body)}"


def validate_license_key(key: str) -> tuple[str, str]:
    normalized = key.strip().upper()
    parts = normalized.split("-")
    if len(parts) != 5:
        raise ValueError("Invalid license key format")

    tier_prefix = parts[0]
    if tier_prefix == "PRO":
        tier = "professional"
    elif tier_prefix == "ENT":
        tier = "enterprise"
    else:
        raise ValueError("Invalid license tier prefix")

    body = "-".join(parts[:4])
    expected = license_checksum(body)
    if parts[4] != expected:
        raise ValueError("Invalid license checksum")

    if os.environ.get("THORPE_LICENSE_ALLOW_DEMO", "").lower() not in ("1", "true", "yes"):
        if normalized in ("PRO-DEMO-1234-KEYS-B65C", "ENT-DEMO-5678-KEYS-F20C"):
            raise ValueError("Demo license keys are not accepted")

    if not KEY_PATTERN.match(normalized):
        raise ValueError("Invalid license key characters")

    return tier, normalized
