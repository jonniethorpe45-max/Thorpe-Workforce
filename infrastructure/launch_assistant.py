#!/usr/bin/env python3
"""
Thorpe Workforce Launch Assistant

Purpose:
- Track remaining manual launch tasks
- Validate DNS + backend health for production URLs
- Validate basic CORS behavior for the frontend origin

Usage examples:
  python infrastructure/launch_assistant.py checklist
  python infrastructure/launch_assistant.py verify --api-url https://api.thorpeworkforce.ai --app-url https://thorpeworkforce.ai
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable


DEFAULT_API_URL = "https://api.thorpeworkforce.ai"
DEFAULT_APP_URL = "https://thorpeworkforce.ai"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _print_results(results: Iterable[CheckResult]) -> int:
    failures = 0
    for result in results:
        icon = "OK" if result.ok else "FAIL"
        print(f"[{icon}] {result.name}: {result.detail}")
        if not result.ok:
            failures += 1
    return failures


def _http_json(url: str, timeout: int = 10) -> tuple[int, dict | None, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = None
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = None
            return resp.status, data, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, None, body


def _cors_preflight(url: str, origin: str, timeout: int = 10) -> tuple[int | None, str | None]:
    req = urllib.request.Request(url, method="OPTIONS")
    req.add_header("Origin", origin)
    req.add_header("Access-Control-Request-Method", "GET")
    req.add_header("Access-Control-Request-Headers", "content-type,authorization")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Access-Control-Allow-Origin")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Access-Control-Allow-Origin")
    except Exception:
        return None, None


def _dns_check(api_url: str) -> CheckResult:
    parsed = urllib.parse.urlparse(api_url)
    host = parsed.hostname
    if not host:
        return CheckResult("DNS lookup", False, f"invalid api url: {api_url}")
    try:
        ip = socket.gethostbyname(host)
        return CheckResult("DNS lookup", True, f"{host} resolves to {ip}")
    except socket.gaierror as exc:
        return CheckResult("DNS lookup", False, f"{host} not resolvable ({exc})")


def _tls_check(api_url: str) -> CheckResult:
    parsed = urllib.parse.urlparse(api_url)
    host = parsed.hostname
    if not host:
        return CheckResult("TLS handshake", False, f"invalid api url: {api_url}")
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host):
                return CheckResult("TLS handshake", True, f"TLS valid for {host}")
    except Exception as exc:
        return CheckResult("TLS handshake", False, f"TLS failed for {host} ({exc})")


def _health_checks(api_url: str) -> list[CheckResult]:
    base = api_url.rstrip("/")
    endpoints = [
        ("/health", "health"),
        ("/health/live", "liveness"),
        ("/health/ready", "readiness"),
    ]
    results: list[CheckResult] = []
    for path, label in endpoints:
        status, payload, body = _http_json(f"{base}{path}")
        if status != 200:
            results.append(CheckResult(f"API {label}", False, f"HTTP {status}; body={body[:180]}"))
            continue
        if isinstance(payload, dict) and payload.get("status") == "ok":
            results.append(CheckResult(f"API {label}", True, "status=ok"))
        else:
            results.append(CheckResult(f"API {label}", False, f"unexpected payload={body[:180]}"))
    return results


def _cors_check(api_url: str, app_url: str) -> CheckResult:
    status, allow_origin = _cors_preflight(f"{api_url.rstrip('/')}/health", app_url)
    if status is None:
        return CheckResult("CORS preflight", False, "request failed")
    if status not in (200, 204):
        return CheckResult("CORS preflight", False, f"HTTP {status}; allow-origin={allow_origin!r}")
    if allow_origin in ("*", app_url):
        return CheckResult("CORS preflight", True, f"allow-origin={allow_origin!r}")
    return CheckResult("CORS preflight", False, f"allow-origin={allow_origin!r}; expected {app_url!r} or '*'")


def run_verify(api_url: str, app_url: str) -> int:
    print("Thorpe Workforce Launch Assistant — verification")
    print(f"- API URL: {api_url}")
    print(f"- APP URL: {app_url}")
    print("")
    results: list[CheckResult] = []
    results.append(_dns_check(api_url))
    results.append(_tls_check(api_url))
    results.extend(_health_checks(api_url))
    results.append(_cors_check(api_url, app_url))
    failures = _print_results(results)
    print("")
    if failures:
        print(f"Verification completed with {failures} failing checks.")
        print("Action: fix the failed items, then rerun this command.")
        return 1
    print("All verification checks passed.")
    return 0


def print_checklist(api_url: str, app_url: str) -> int:
    print("Thorpe Workforce Launch Assistant — remaining manual tasks")
    print("")
    print("Railway setup")
    print("- [ ] API service deployed from `backend/` and reachable")
    print("- [ ] Worker service deployed from `backend/` and running Celery")
    print("- [ ] PostgreSQL + Redis attached and env references set")
    print("- [ ] `ENVIRONMENT=production` and strong `SECRET_KEY` configured")
    print("")
    print("Domain + DNS")
    print(f"- [ ] API custom domain attached in Railway: {urllib.parse.urlparse(api_url).hostname}")
    print("- [ ] DNS CNAME points to Railway target for API service")
    print("- [ ] TLS certificate issued and active")
    print("")
    print("Frontend integration")
    print(f"- [ ] `NEXT_PUBLIC_API_BASE_URL={api_url}`")
    print(f"- [ ] `NEXT_PUBLIC_APP_URL={app_url}`")
    print("")
    print("Backend cross-origin + host safety")
    print(f"- [ ] `APP_BASE_URL={app_url}`")
    print(f"- [ ] `CORS_ORIGINS` allows frontend origin ({app_url})")
    print(f"- [ ] `TRUSTED_HOSTS` includes API host ({urllib.parse.urlparse(api_url).hostname})")
    print("")
    print("Stripe (if billing enabled)")
    print("- [ ] Stripe webhook endpoint configured: /billing/webhooks/stripe")
    print("- [ ] STRIPE_* vars populated for live/staging mode")
    print("")
    print("Validation")
    print(f"- [ ] `python infrastructure/launch_assistant.py verify --api-url {api_url} --app-url {app_url}`")
    print("")
    print("Detailed Railway guide: infrastructure/railway.md")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Thorpe Workforce launch assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    checklist = sub.add_parser("checklist", help="print remaining manual launch tasks")
    checklist.add_argument("--api-url", default=DEFAULT_API_URL)
    checklist.add_argument("--app-url", default=DEFAULT_APP_URL)

    verify = sub.add_parser("verify", help="verify DNS, TLS, health, and CORS")
    verify.add_argument("--api-url", default=DEFAULT_API_URL)
    verify.add_argument("--app-url", default=DEFAULT_APP_URL)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "checklist":
        return print_checklist(args.api_url, args.app_url)
    if args.command == "verify":
        return run_verify(args.api_url, args.app_url)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
