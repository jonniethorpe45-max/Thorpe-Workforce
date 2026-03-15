from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.api.routes import (
    analytics,
    admin_analytics,
    auth,
    creator_dashboard,
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
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database not ready") from exc
    return {"status": "ok", "service": "thorpe-workforce-api", "check": "ready", "database": "ok"}
