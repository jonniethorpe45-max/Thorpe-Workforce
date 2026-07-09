from fastapi import FastAPI

app = FastAPI(title="Knowledge Graph", version="0.1.0")

SERVICES = [
    {"id": "jonathan-core", "name": "Jonathan Core", "port": 8000, "status": "active"},
    {"id": "knowledge-graph", "name": "Knowledge Graph", "port": 8001, "status": "active"},
    {"id": "identity", "name": "Identity", "port": 8002, "status": "active"},
    {"id": "capability-registry", "name": "Capability Registry", "port": 8003, "status": "active"},
    {"id": "mock-calendar", "name": "Mock Calendar", "port": 8004, "status": "active"},
    {"id": "model-router", "name": "Model Router", "port": 8005, "status": "active"},
    {"id": "api-gateway", "name": "API Gateway", "port": 7999, "status": "active"},
]


@app.get("/health")
def health():
    return {"status": "ok", "service": "knowledge-graph"}


@app.get("/graph/services")
def list_services():
    return SERVICES
