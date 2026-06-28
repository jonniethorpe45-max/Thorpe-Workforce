#!/usr/bin/env python3
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

SECRET = "thorpe-license-test-secret"


def checksum(body: str) -> str:
    digest = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return digest[:2].hex().upper()


def make_key(prefix: str, g1: str, g2: str, g3: str) -> str:
    body = f"{prefix}-{g1}-{g2}-{g3}"
    return f"{body}-{checksum(body)}"


def test_validate() -> None:
    os.environ["THORPE_LICENSE_SIGNING_SECRET"] = SECRET
    os.environ["THORPE_LICENSE_ALLOW_DEMO"] = "true"
    from license_keys import validate_license_key

    key = make_key("PRO", "TEST", "0001", "SMOKE")
    tier, normalized = validate_license_key(key)
    assert tier == "professional"
    assert normalized == key


def test_generate_key() -> None:
    os.environ["THORPE_LICENSE_SIGNING_SECRET"] = SECRET
    from license_keys import generate_license_key, validate_license_key

    key = generate_license_key("enterprise")
    assert key.startswith("ENT-")
    assert validate_license_key(key)[0] == "enterprise"


def test_http_roundtrip() -> None:
    os.environ["THORPE_LICENSE_SIGNING_SECRET"] = SECRET
    os.environ["THORPE_LICENSE_ALLOW_DEMO"] = "true"
    os.environ["THORPE_LICENSE_SERVER_PORT"] = "8799"
    os.environ["THORPE_LICENSE_SESSION_STORE"] = "/tmp/thorpe-test-sessions.json"

    proc = subprocess.Popen([sys.executable, "server.py"], cwd=os.path.dirname(__file__))
    try:
        key = make_key("ENT", "HTTP", "0001", "SMOKE")
        payload = json.dumps(
            {
                "license_key": key,
                "organization": "Acme MSP",
                "app_version": "1.1.0",
                "platform": "linux",
            }
        ).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8799/activate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for _ in range(20):
            try:
                with urllib.request.urlopen(req, timeout=2) as resp:
                    body = json.loads(resp.read().decode())
                break
            except (urllib.error.URLError, ConnectionRefusedError) as exc:
                last_error = exc
                time.sleep(0.2)
        else:
            raise last_error or RuntimeError("license server did not start")

        assert body["tier"] == "enterprise"
        assert body["organization"] == "Acme MSP"
        assert body["expires_at"]

        health_req = urllib.request.Request("http://127.0.0.1:8799/health", method="GET")
        with urllib.request.urlopen(health_req, timeout=2) as resp:
            health = json.loads(resp.read().decode())
        assert health["status"] == "ok"
        assert health["stripe_configured"] is False

        checkout_payload = json.dumps({"tier": "professional"}).encode()
        checkout_req = urllib.request.Request(
            "http://127.0.0.1:8799/checkout",
            data=checkout_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(checkout_req, timeout=2)
            raise AssertionError("expected checkout to fail without Stripe")
        except urllib.error.HTTPError as exc:
            assert exc.code == 503
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        if os.path.exists("/tmp/thorpe-test-sessions.json"):
            os.remove("/tmp/thorpe-test-sessions.json")


if __name__ == "__main__":
    test_validate()
    test_generate_key()
    test_http_roundtrip()
    print("license-server smoke tests passed")
