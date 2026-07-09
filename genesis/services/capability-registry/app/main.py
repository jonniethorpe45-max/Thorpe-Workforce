from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Capability Registry", version="0.1.0")

CAPABILITIES = {
    "calendar.create_event": {
        "id": "calendar.create_event",
        "name": "Create Calendar Event",
        "description": "Create an event via the calendar connector",
        "risk_level": "medium",
        "connector": "mock-calendar",
        "status": "active",
    },
    "calendar.list_events": {
        "id": "calendar.list_events",
        "name": "List Calendar Events",
        "description": "List events from the calendar connector",
        "risk_level": "low",
        "connector": "mock-calendar",
        "status": "active",
    },
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "capability-registry"}


@app.get("/capabilities")
def list_capabilities():
    return list(CAPABILITIES.values())


@app.get("/capabilities/{capability_id}")
def get_capability(capability_id: str):
    cap = CAPABILITIES.get(capability_id)
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")
    return cap
