from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, campaigns, leads, meetings, messages, replies, webhooks, worker_builder, workers, workspace
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
app.include_router(workspace.router)
app.include_router(workers.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(messages.router)
app.include_router(replies.router)
app.include_router(meetings.router)
app.include_router(analytics.router)
app.include_router(webhooks.router)
app.include_router(worker_builder.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "thorpe-workforce-api"}
