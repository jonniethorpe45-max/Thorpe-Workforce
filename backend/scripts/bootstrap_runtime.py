#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User, Workspace
from app.services.founder_os import ensure_founder_os_chains
from app.services.system_seed import seed_system_worker_templates_and_tools


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _wait_for_database(timeout_seconds: int = 120) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except SQLAlchemyError:
            time.sleep(2)
    raise RuntimeError("Database was not reachable before timeout")


def _wait_for_redis(timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    client = redis.Redis.from_url(settings.redis_url)
    while time.time() < deadline:
        try:
            client.ping()
            return
        except redis.RedisError:
            time.sleep(2)
    raise RuntimeError("Redis was not reachable before timeout")


def _run_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=str(ROOT),
    )


def _seed_worker_system() -> None:
    with SessionLocal() as db:
        seed_system_worker_templates_and_tools(db)
        db.commit()


def _seed_founder_os_chains_for_existing_workspaces() -> None:
    with SessionLocal() as db:
        workspaces = db.query(Workspace).all()
        for workspace in workspaces:
            owner_or_admin = (
                db.query(User)
                .filter(
                    User.workspace_id == workspace.id,
                    User.role.in_(("owner", "admin", "super_admin")),
                )
                .order_by(User.created_at.asc())
                .first()
            )
            ensure_founder_os_chains(
                db,
                workspace_id=workspace.id,
                actor_user_id=owner_or_admin.id if owner_or_admin else None,
            )
        db.commit()


def _run_demo_seed() -> None:
    from scripts.seed_demo import seed as seed_demo

    seed_demo()


def bootstrap() -> None:
    _wait_for_database()
    _wait_for_redis()
    run_migrations_default = settings.environment in {"development", "test"}
    seed_worker_default = settings.environment in {"development", "test"}
    seed_demo_default = settings.environment == "development"
    seed_founder_default = settings.environment in {"development", "test"}

    if _env_flag("RUN_MIGRATIONS", run_migrations_default):
        _run_migrations()
    if _env_flag("SEED_WORKER_SYSTEM", seed_worker_default):
        _seed_worker_system()
    if _env_flag("SEED_DEMO_DATA", seed_demo_default):
        _run_demo_seed()
    if _env_flag("SEED_FOUNDER_OS_CHAINS", seed_founder_default):
        _seed_founder_os_chains_for_existing_workspaces()


def main() -> None:
    bootstrap()
    command = sys.argv[1:]
    if not command:
        return
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
