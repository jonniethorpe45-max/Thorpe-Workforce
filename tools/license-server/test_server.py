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
    from server import validate_license_key

    key = make_key("PRO", "TEST", "0001", "SMOKE")
    tier, normalized = validate_license_key(key)
    assert tier == "professional"
    assert normalized == key


def test_http_roundtrip() -> None:
    os.environ["THORPE_LICENSE_SIGNING_SECRET"] = SECRET
    os.environ["THORPE_LICENSE_ALLOW_DEMO"] = "true"
    os.environ["THORPE_LICENSE_SERVER_PORT"] = "8799"

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
    finally:
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    test_validate()
    test_http_roundtrip()
    print("license-server smoke tests passed")
