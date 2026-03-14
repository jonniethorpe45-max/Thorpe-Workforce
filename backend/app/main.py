from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analytics,
    auth,
    billing,
    campaigns,
    leads,
    marketplace,
    meetings,
    messages,
    public_workers,
    replies,
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

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(workspace.router)
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
app.include_router(webhooks.router)
app.include_router(worker_builder.router)
app.include_router(worker_creator.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "thorpe-workforce-api"}
