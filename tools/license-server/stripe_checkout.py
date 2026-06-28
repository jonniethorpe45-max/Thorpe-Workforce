"""Stripe REST helpers using stdlib only (no stripe SDK required)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
STRIPE_PRICE_PROFESSIONAL = os.environ.get("STRIPE_PRICE_PROFESSIONAL", "").strip()
STRIPE_PRICE_ENTERPRISE = os.environ.get("STRIPE_PRICE_ENTERPRISE", "").strip()
CHECKOUT_SUCCESS_URL = os.environ.get(
    "THORPE_CHECKOUT_SUCCESS_URL",
    "https://thorpe.app/licensing?checkout=success&session_id={CHECKOUT_SESSION_ID}",
)
CHECKOUT_CANCEL_URL = os.environ.get("THORPE_CHECKOUT_CANCEL_URL", "https://thorpe.app/licensing?checkout=cancel")


def stripe_configured() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_PROFESSIONAL)


def _stripe_request(method: str, path: str, data: dict[str, str] | None = None) -> dict[str, Any]:
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")

    url = f"https://api.stripe.com/v1{path}"
    encoded = urllib.parse.urlencode(data or {}).encode("utf-8") if data else None
    request = urllib.request.Request(
        url,
        data=encoded,
        method=method,
        headers={
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Stripe API error ({exc.code}): {body}") from exc


def create_checkout_session(tier: str, customer_email: str | None = None) -> dict[str, Any]:
    price_id = STRIPE_PRICE_PROFESSIONAL if tier == "professional" else STRIPE_PRICE_ENTERPRISE
    if not price_id:
        raise RuntimeError(f"No Stripe price configured for tier: {tier}")

    payload: dict[str, str] = {
        "mode": "subscription",
        "success_url": CHECKOUT_SUCCESS_URL,
        "cancel_url": CHECKOUT_CANCEL_URL,
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "client_reference_id": tier,
        "metadata[tier]": tier,
        "metadata[product]": "thorpe-desktop",
    }
    if customer_email:
        payload["customer_email"] = customer_email

    return _stripe_request("POST", "/checkout/sessions", payload)


def retrieve_checkout_session(session_id: str) -> dict[str, Any]:
    return _stripe_request("GET", f"/checkout/sessions/{session_id}")


def verify_webhook_signature(payload: bytes, signature_header: str) -> dict[str, Any]:
    if not STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")

    parts = {}
    for item in signature_header.split(","):
        key, _, value = item.partition("=")
        parts.setdefault(key, []).append(value)

    timestamp = (parts.get("t") or [""])[0]
    signatures = parts.get("v1") or []
    if not timestamp or not signatures:
        raise ValueError("Invalid Stripe-Signature header")

    import hashlib
    import hmac

    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(
        STRIPE_WEBHOOK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not any(hmac.compare_digest(expected, sig) for sig in signatures):
        raise ValueError("Webhook signature verification failed")

    return json.loads(payload.decode("utf-8"))
