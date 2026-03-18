#!/usr/bin/env python3
"""
Thorpe Workforce Launch Assistant

Purpose:
- Track remaining manual launch tasks
- Validate DNS + backend health for production URLs
- Validate basic CORS behavior for the frontend origin
- Bootstrap local macOS setup (clone + install)

Usage examples:
  python infrastructure/launch_assistant.py checklist
  python infrastructure/launch_assistant.py verify --api-url https://api.thorpeworkforce.ai --app-url https://thorpeworkforce.ai
  python infrastructure/launch_assistant.py bootstrap-mac --repo-url https://github.com/<owner>/<repo>.git --target-dir ~/Developer/Thorpe-Workforce
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
import shlex
import shutil
import socket
import ssl
import subprocess
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


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _run_command_step(
    name: str,
    command: list[str],
    *,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> CheckResult:
    run_location = str(cwd) if cwd else os.getcwd()
    display = _format_command(command)
    if dry_run:
        return CheckResult(name, True, f"DRY RUN: ({run_location}) {display}")
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        return CheckResult(name, False, f"failed to start command ({exc})")
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip().replace("\n", " ")
        return CheckResult(name, False, f"exit={completed.returncode}; cmd={display}; detail={stderr[:220]}")
    return CheckResult(name, True, f"ok; cmd={display}")


def _copy_if_missing(name: str, src: Path, dst: Path, *, dry_run: bool = False) -> CheckResult:
    if dry_run:
        return CheckResult(name, True, f"DRY RUN: copy {src} -> {dst}")
    if dst.exists():
        return CheckResult(name, True, f"exists: {dst}")
    if not src.exists():
        return CheckResult(name, False, f"missing source file: {src}")
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return CheckResult(name, True, f"copied {src.name} -> {dst.name}")


def _ensure_tool(
    *,
    step_name: str,
    command_name: str,
    brew_package: str,
    skip_brew: bool,
    dry_run: bool,
    is_cask: bool = False,
) -> CheckResult:
    if _command_exists(command_name):
        return CheckResult(step_name, True, f"{command_name} already installed")
    if skip_brew:
        return CheckResult(
            step_name,
            False,
            f"{command_name} not found and --skip-brew is enabled",
        )
    if not _command_exists("brew"):
        return CheckResult(
            step_name,
            False,
            "Homebrew not found. Install Homebrew first: https://brew.sh/",
        )
    install_cmd = ["brew", "install"]
    if is_cask:
        install_cmd.append("--cask")
    install_cmd.append(brew_package)
    return _run_command_step(step_name, install_cmd, dry_run=dry_run)


def _default_repo_url() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        completed = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _clone_or_update_repo(
    *,
    repo_url: str,
    target_dir: Path,
    branch: str | None,
    dry_run: bool,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    parent_dir = target_dir.parent
    if dry_run:
        results.append(CheckResult("Create target parent", True, f"DRY RUN: mkdir -p {parent_dir}"))
    else:
        parent_dir.mkdir(parents=True, exist_ok=True)
        results.append(CheckResult("Create target parent", True, f"ready: {parent_dir}"))

    if target_dir.exists() and (target_dir / ".git").exists():
        results.append(_run_command_step("Git fetch", ["git", "fetch", "origin"], cwd=target_dir, dry_run=dry_run))
        if branch:
            results.append(
                _run_command_step("Git checkout branch", ["git", "checkout", branch], cwd=target_dir, dry_run=dry_run)
            )
            results.append(
                _run_command_step(
                    "Git pull branch",
                    ["git", "pull", "origin", branch],
                    cwd=target_dir,
                    dry_run=dry_run,
                )
            )
        return results

    if target_dir.exists():
        results.append(
            CheckResult(
                "Clone repository",
                False,
                f"target directory exists but is not a git repo: {target_dir}",
            )
        )
        return results

    clone_cmd = ["git", "clone"]
    if branch:
        clone_cmd.extend(["--branch", branch])
    clone_cmd.extend([repo_url, str(target_dir)])
    results.append(_run_command_step("Clone repository", clone_cmd, dry_run=dry_run))
    return results


def run_bootstrap_mac(
    *,
    repo_url: str,
    target_dir: str,
    branch: str | None,
    python_bin: str,
    skip_brew: bool,
    skip_infra: bool,
    dry_run: bool,
) -> int:
    print("Thorpe Workforce Launch Assistant — macOS bootstrap")
    print(f"- Repo URL: {repo_url}")
    print(f"- Target dir: {target_dir}")
    print(f"- Branch: {branch or '(default)'}")
    print(f"- Python binary: {python_bin}")
    print("")

    results: list[CheckResult] = []

    if platform.system() != "Darwin":
        detail = "non-macOS runtime detected"
        if dry_run:
            results.append(CheckResult("macOS runtime check", True, f"{detail}; continuing because --dry-run is enabled"))
        else:
            results.append(CheckResult("macOS runtime check", False, f"{detail}; rerun on macOS or use --dry-run"))
            failures = _print_results(results)
            print("")
            return 1 if failures else 0
    else:
        results.append(CheckResult("macOS runtime check", True, "Darwin detected"))

    results.append(
        _ensure_tool(
            step_name="Install Git",
            command_name="git",
            brew_package="git",
            skip_brew=skip_brew,
            dry_run=dry_run,
        )
    )
    results.append(
        _ensure_tool(
            step_name="Install Python 3",
            command_name=python_bin,
            brew_package="python@3.12",
            skip_brew=skip_brew,
            dry_run=dry_run,
        )
    )
    results.append(
        _ensure_tool(
            step_name="Install Node.js + npm",
            command_name="npm",
            brew_package="node",
            skip_brew=skip_brew,
            dry_run=dry_run,
        )
    )
    if not skip_infra:
        results.append(
            _ensure_tool(
                step_name="Install Docker Desktop",
                command_name="docker",
                brew_package="docker",
                skip_brew=skip_brew,
                dry_run=dry_run,
                is_cask=True,
            )
        )

    resolved_target = Path(target_dir).expanduser().resolve()
    results.extend(_clone_or_update_repo(repo_url=repo_url, target_dir=resolved_target, branch=branch, dry_run=dry_run))

    backend_dir = resolved_target / "backend"
    frontend_dir = resolved_target / "frontend"
    if not dry_run:
        if not backend_dir.exists():
            results.append(CheckResult("Backend directory check", False, f"missing: {backend_dir}"))
        else:
            results.append(CheckResult("Backend directory check", True, str(backend_dir)))
        if not frontend_dir.exists():
            results.append(CheckResult("Frontend directory check", False, f"missing: {frontend_dir}"))
        else:
            results.append(CheckResult("Frontend directory check", True, str(frontend_dir)))
    else:
        results.append(CheckResult("Backend directory check", True, f"DRY RUN: expect {backend_dir}"))
        results.append(CheckResult("Frontend directory check", True, f"DRY RUN: expect {frontend_dir}"))

    results.append(
        _run_command_step(
            "Create backend virtualenv",
            [python_bin, "-m", "venv", ".venv"],
            cwd=backend_dir,
            dry_run=dry_run,
        )
    )
    results.append(
        _run_command_step(
            "Upgrade backend pip tooling",
            [str(backend_dir / ".venv" / "bin" / "python"), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            cwd=backend_dir,
            dry_run=dry_run,
        )
    )
    results.append(
        _run_command_step(
            "Install backend requirements",
            [str(backend_dir / ".venv" / "bin" / "python"), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=backend_dir,
            dry_run=dry_run,
        )
    )
    results.append(
        _copy_if_missing(
            "Create backend .env",
            backend_dir / ".env.example",
            backend_dir / ".env",
            dry_run=dry_run,
        )
    )

    if not skip_infra:
        results.append(
            _run_command_step(
                "Start Docker services",
                ["docker", "compose", "up", "-d"],
                cwd=resolved_target,
                dry_run=dry_run,
            )
        )
        results.append(
            _run_command_step(
                "Run backend migrations",
                [str(backend_dir / ".venv" / "bin" / "python"), "-m", "alembic", "upgrade", "head"],
                cwd=backend_dir,
                dry_run=dry_run,
            )
        )
        results.append(
            _run_command_step(
                "Seed system data",
                [str(backend_dir / ".venv" / "bin" / "python"), "scripts/seed_worker_system.py"],
                cwd=backend_dir,
                dry_run=dry_run,
            )
        )
        results.append(
            _run_command_step(
                "Seed demo data",
                [str(backend_dir / ".venv" / "bin" / "python"), "scripts/seed_demo.py"],
                cwd=backend_dir,
                dry_run=dry_run,
            )
        )

    results.append(
        _run_command_step(
            "Install frontend dependencies",
            ["npm", "install"],
            cwd=frontend_dir,
            dry_run=dry_run,
        )
    )
    results.append(
        _copy_if_missing(
            "Create frontend .env.local",
            frontend_dir / ".env.example",
            frontend_dir / ".env.local",
            dry_run=dry_run,
        )
    )

    failures = _print_results(results)
    print("")
    if failures:
        print(f"Bootstrap completed with {failures} failing steps.")
        print("Action: fix failed steps, then rerun bootstrap-mac.")
        return 1

    print("Bootstrap completed successfully.")
    print("")
    print("Next commands (run in separate terminals):")
    print(f"1) cd {shlex.quote(str(backend_dir))} && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000")
    print(
        f"2) cd {shlex.quote(str(backend_dir))} && source .venv/bin/activate && celery -A app.tasks.celery_app.celery_app worker -l info"
    )
    print(f"3) cd {shlex.quote(str(frontend_dir))} && npm run dev")
    return 0


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

    bootstrap = sub.add_parser("bootstrap-mac", help="clone and install the app on macOS")
    bootstrap.add_argument("--repo-url", default=_default_repo_url(), help="git repository URL")
    bootstrap.add_argument("--target-dir", default="~/Developer/Thorpe-Workforce", help="local directory for the repo")
    bootstrap.add_argument("--branch", default="", help="optional git branch to checkout/pull")
    bootstrap.add_argument("--python-bin", default="python3", help="python binary to use (default: python3)")
    bootstrap.add_argument("--skip-brew", action="store_true", help="skip Homebrew-based dependency installation")
    bootstrap.add_argument(
        "--skip-infra",
        action="store_true",
        help="skip Docker services, migrations, and seed steps",
    )
    bootstrap.add_argument("--dry-run", action="store_true", help="print planned commands without executing")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "checklist":
        return print_checklist(args.api_url, args.app_url)
    if args.command == "verify":
        return run_verify(args.api_url, args.app_url)
    if args.command == "bootstrap-mac":
        if not str(args.repo_url).strip():
            print("Missing --repo-url and no git remote.origin.url could be inferred.")
            return 2
        branch = args.branch.strip() or None
        return run_bootstrap_mac(
            repo_url=args.repo_url.strip(),
            target_dir=args.target_dir,
            branch=branch,
            python_bin=args.python_bin.strip(),
            skip_brew=bool(args.skip_brew),
            skip_infra=bool(args.skip_infra),
            dry_run=bool(args.dry_run),
        )
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
