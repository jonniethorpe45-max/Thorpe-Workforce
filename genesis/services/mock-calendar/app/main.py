from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Calendar", version="0.1.0")

EVENTS: list[dict] = []


class EventCreate(BaseModel):
    title: str
    created_by: str = "demo-user"
    source_approval_id: str | None = None
    starts_at: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-calendar"}


@app.get("/calendar/events")
def list_events():
    return EVENTS


@app.post("/calendar/events")
def create_event(body: EventCreate):
    event = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "created_by": body.created_by,
        "source_approval_id": body.source_approval_id,
        "starts_at": body.starts_at or datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    EVENTS.append(event)
    return event
