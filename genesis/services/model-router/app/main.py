from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Model Router", version="0.1.0")


class RouteRequest(BaseModel):
    task_type: str = "general"
    risk_level: str = "low"
    modality: str = "text"
    privacy_level: str = "standard"


@app.get("/health")
def health():
    return {"status": "ok", "service": "model-router"}


@app.post("/models/route")
def route_model(body: RouteRequest):
    model = "local-rules"
    if body.risk_level in ("medium", "high"):
        model = "local-rules-conservative"
    if body.privacy_level == "strict":
        model = "local-only"
    return {
        "selected_model": model,
        "provider": "genesis-local",
        "reason": "Build Zero placeholder routing",
        "request": body.model_dump(),
    }
