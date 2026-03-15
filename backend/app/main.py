from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import redis
from sqlalchemy import text

from app.api.routes import (
    analytics,
    admin_analytics,
    auth,
    creator_dashboard,
    founder_os,
    billing,
    campaigns,
    leads,
    marketplace,
    meetings,
    messages,
    onboarding,
    public_workers,
    replies,
    support,
    webhooks,
    worker_chains,
    worker_builder,
    worker_creator,
    worker_instances,
    worker_runs,
    worker_tools,
    workers,
    workspace,
)
from app.core.config import settings
from app.db.session import engine

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(workspace.router)
app.include_router(creator_dashboard.router)
app.include_router(founder_os.router)
app.include_router(admin_analytics.router)
app.include_router(workers.router)
app.include_router(worker_instances.router)
app.include_router(worker_runs.router)
app.include_router(worker_chains.router)
app.include_router(worker_tools.router)
app.include_router(marketplace.router)
app.include_router(public_workers.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(messages.router)
app.include_router(replies.router)
app.include_router(meetings.router)
app.include_router(analytics.router)
app.include_router(onboarding.router)
app.include_router(support.router)
app.include_router(webhooks.router)
app.include_router(worker_builder.router)
app.include_router(worker_creator.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "thorpe-workforce-api"}


@app.get("/health/live")
def liveness():
    return {"status": "ok", "service": "thorpe-workforce-api", "check": "live"}


@app.get("/health/ready")
def readiness():
    checks = {"database": "unknown", "redis": "unknown", "migrations": "unknown"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database not ready") from exc

    if settings.environment != "test":
        try:
            redis.Redis.from_url(settings.redis_url).ping()
            checks["redis"] = "ok"
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Redis not ready") from exc

        try:
            alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
            if not alembic_ini.exists():
                alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
            head_revision = ScriptDirectory.from_config(alembic_cfg).get_current_head()
            with engine.connect() as connection:
                current_revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if not current_revision or current_revision != head_revision:
                raise HTTPException(status_code=503, detail="Database migrations are not at head")
            checks["migrations"] = "ok"
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Migration state not ready") from exc
    else:
        checks["redis"] = "skipped_test_env"
        checks["migrations"] = "skipped_test_env"

    return {"status": "ok", "service": "thorpe-workforce-api", "check": "ready", **checks}
