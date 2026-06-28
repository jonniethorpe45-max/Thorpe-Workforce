#!/usr/bin/env python3
"""Minimal Thorpe license activation server for production pilots.

Matches the desktop client's `THORPE_LICENSE_API_URL` contract:
  POST /activate  ->  { tier, expires_at?, organization? }

Run:
  THORPE_LICENSE_SIGNING_SECRET=your-secret python3 server.py
  THORPE_LICENSE_API_URL=http://127.0.0.1:8787/activate
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

HOST = os.environ.get("THORPE_LICENSE_SERVER_HOST", "127.0.0.1")
PORT = int(os.environ.get("THORPE_LICENSE_SERVER_PORT", "8787"))
SECRET = os.environ.get("THORPE_LICENSE_SIGNING_SECRET", "thorpe-license-signing-key-v1")
DEFAULT_TERM_DAYS = int(os.environ.get("THORPE_LICENSE_TERM_DAYS", "365"))
API_TOKEN = os.environ.get("THORPE_LICENSE_API_TOKEN", "").strip()

KEY_PATTERN = re.compile(r"^(PRO|ENT)-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]{4}$")


def license_checksum(body: str) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return digest[:2].hex().upper()


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

    # Block well-known demo keys in production server mode
    if os.environ.get("THORPE_LICENSE_ALLOW_DEMO", "").lower() not in ("1", "true", "yes"):
        if normalized in ("PRO-DEMO-1234-KEYS-B65C", "ENT-DEMO-5678-KEYS-F20C"):
            raise ValueError("Demo license keys are not accepted")

    if not KEY_PATTERN.match(normalized):
        raise ValueError("Invalid license key characters")

    return tier, normalized


def activation_response(tier: str, organization: str | None) -> dict[str, Any]:
    expires_at = (datetime.now(timezone.utc) + timedelta(days=DEFAULT_TERM_DAYS)).isoformat()
    return {
        "tier": tier,
        "expires_at": expires_at,
        "organization": organization,
    }


class LicenseHandler(BaseHTTPRequestHandler):
    server_version = "ThorpeLicenseServer/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[license-server] {self.address_string()} - {fmt % args}")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/activate":
            self._send_json(404, {"error": "Not found"})
            return

        if API_TOKEN:
            auth = self.headers.get("Authorization", "")
            if auth != f"Bearer {API_TOKEN}":
                self._send_json(401, {"error": "Unauthorized"})
                return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        license_key = str(payload.get("license_key", "")).strip()
        organization = payload.get("organization")
        if organization is not None:
            organization = str(organization).strip() or None

        try:
            tier, _ = validate_license_key(license_key)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_json(200, activation_response(tier, organization))

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "Not found"})


def main() -> None:
    if SECRET == "thorpe-license-signing-key-v1":
        print(
            "[license-server] warning: using default signing secret. "
            "Set THORPE_LICENSE_SIGNING_SECRET in production."
        )
    httpd = HTTPServer((HOST, PORT), LicenseHandler)
    print(f"[license-server] listening on http://{HOST}:{PORT}/activate")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
