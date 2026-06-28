#!/usr/bin/env python3
"""Thorpe license + billing server for desktop activation and Stripe checkout."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from license_keys import generate_license_key, validate_license_key
from stripe_checkout import (
    create_checkout_session,
    retrieve_checkout_session,
    stripe_configured,
    verify_webhook_signature,
)

HOST = os.environ.get("THORPE_LICENSE_SERVER_HOST", "127.0.0.1")
PORT = int(os.environ.get("THORPE_LICENSE_SERVER_PORT", "8787"))
API_TOKEN = os.environ.get("THORPE_LICENSE_API_TOKEN", "").strip()
DEFAULT_TERM_DAYS = int(os.environ.get("THORPE_LICENSE_TERM_DAYS", "365"))
SESSION_STORE = Path(os.environ.get("THORPE_LICENSE_SESSION_STORE", "checkout_sessions.json"))
_store_lock = threading.Lock()


def _load_sessions() -> dict[str, Any]:
    if not SESSION_STORE.exists():
        return {}
    return json.loads(SESSION_STORE.read_text(encoding="utf-8"))


def _save_sessions(data: dict[str, Any]) -> None:
    SESSION_STORE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _upsert_session(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with _store_lock:
        sessions = _load_sessions()
        existing = sessions.get(session_id, {})
        existing.update(payload)
        sessions[session_id] = existing
        _save_sessions(sessions)
        return existing


def _get_session(session_id: str) -> dict[str, Any] | None:
    with _store_lock:
        return _load_sessions().get(session_id)


def _authorize(handler: BaseHTTPRequestHandler) -> bool:
    if not API_TOKEN:
        return True
    auth = handler.headers.get("Authorization", "")
    return auth == f"Bearer {API_TOKEN}"


def _activation_response(tier: str, organization: str | None) -> dict[str, Any]:
    expires_at = (datetime.now(timezone.utc) + timedelta(days=DEFAULT_TERM_DAYS)).isoformat()
    return {
        "tier": tier,
        "expires_at": expires_at,
        "organization": organization,
    }


def _fulfill_checkout(session_id: str, tier: str, customer_email: str | None = None) -> dict[str, Any]:
    existing = _get_session(session_id) or {}
    if existing.get("license_key"):
        return existing

    license_key = generate_license_key(tier)
    payload = {
        "session_id": session_id,
        "tier": tier,
        "status": "complete",
        "license_key": license_key,
        "customer_email": customer_email,
        "fulfilled_at": datetime.now(timezone.utc).isoformat(),
    }
    return _upsert_session(session_id, payload)


class LicenseHandler(BaseHTTPRequestHandler):
    server_version = "ThorpeLicenseServer/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[license-server] {self.address_string()} - {fmt % args}")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "stripe_configured": stripe_configured(),
                },
            )
            return

        if path.startswith("/checkout/") and path.endswith("/status"):
            session_id = path.removeprefix("/checkout/").removesuffix("/status")
            session = _get_session(session_id)
            if not session:
                if stripe_configured():
                    try:
                        stripe_session = retrieve_checkout_session(session_id)
                        if stripe_session.get("payment_status") == "paid":
                            tier = stripe_session.get("metadata", {}).get("tier", "professional")
                            session = _fulfill_checkout(
                                session_id,
                                tier,
                                stripe_session.get("customer_details", {}).get("email"),
                            )
                    except Exception as exc:  # noqa: BLE001
                        self._send_json(502, {"error": str(exc)})
                        return
                if not session:
                    self._send_json(404, {"error": "Checkout session not found"})
                    return

            self._send_json(
                200,
                {
                    "session_id": session_id,
                    "status": session.get("status", "pending"),
                    "tier": session.get("tier"),
                    "license_key": session.get("license_key"),
                },
            )
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/webhooks/stripe":
            signature = self.headers.get("Stripe-Signature", "")
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length) if length else b"{}"
            try:
                event = verify_webhook_signature(payload, signature)
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"error": str(exc)})
                return

            if event.get("type") == "checkout.session.completed":
                session = event.get("data", {}).get("object", {})
                session_id = session.get("id")
                tier = session.get("metadata", {}).get("tier", "professional")
                if session_id:
                    _fulfill_checkout(
                        session_id,
                        tier,
                        session.get("customer_details", {}).get("email"),
                    )

            self._send_json(200, {"received": True})
            return

        if not _authorize(self):
            self._send_json(401, {"error": "Unauthorized"})
            return

        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        if path == "/activate":
            license_key = str(body.get("license_key", "")).strip()
            organization = body.get("organization")
            if organization is not None:
                organization = str(organization).strip() or None
            try:
                tier, _ = validate_license_key(license_key)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, _activation_response(tier, organization))
            return

        if path == "/checkout":
            tier = str(body.get("tier", "professional")).strip().lower()
            if tier not in ("professional", "enterprise"):
                self._send_json(400, {"error": "tier must be professional or enterprise"})
                return

            customer_email = body.get("customer_email")
            if customer_email is not None:
                customer_email = str(customer_email).strip() or None

            if not stripe_configured():
                self._send_json(
                    503,
                    {
                        "error": "Stripe is not configured on this license server",
                        "stripe_configured": False,
                    },
                )
                return

            try:
                stripe_session = create_checkout_session(tier, customer_email)
            except Exception as exc:  # noqa: BLE001
                self._send_json(502, {"error": str(exc)})
                return

            session_id = stripe_session["id"]
            _upsert_session(
                session_id,
                {
                    "session_id": session_id,
                    "tier": tier,
                    "status": "pending",
                    "checkout_url": stripe_session.get("url"),
                },
            )
            self._send_json(
                200,
                {
                    "session_id": session_id,
                    "checkout_url": stripe_session.get("url"),
                    "stripe_configured": True,
                },
            )
            return

        self._send_json(404, {"error": "Not found"})


def main() -> None:
    if os.environ.get("THORPE_LICENSE_SIGNING_SECRET", "") in ("", "thorpe-license-signing-key-v1"):
        print(
            "[license-server] warning: using default signing secret. "
            "Set THORPE_LICENSE_SIGNING_SECRET in production."
        )
    httpd = HTTPServer((HOST, PORT), LicenseHandler)
    print(f"[license-server] listening on http://{HOST}:{PORT}")
    print(f"[license-server] stripe configured: {stripe_configured()}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
