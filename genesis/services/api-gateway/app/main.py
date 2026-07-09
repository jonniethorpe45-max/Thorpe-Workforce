from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

JONATHAN_CORE_URL = os.getenv("JONATHAN_CORE_URL", "http://localhost:8000")
KNOWLEDGE_GRAPH_URL = os.getenv("KNOWLEDGE_GRAPH_URL", "http://localhost:8001")
CAPABILITY_REGISTRY_URL = os.getenv("CAPABILITY_REGISTRY_URL", "http://localhost:8003")

app = FastAPI(title="API Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def proxy(method: str, url: str, json_body: dict | None = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(method, url, json=json_body)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream unavailable: {exc}") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    if response.status_code == 204:
        return None
    return response.json()


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}


@app.post("/gateway/intent")
async def gateway_intent(request: Request):
    body = await request.json()
    return await proxy("POST", f"{JONATHAN_CORE_URL}/intent", body)


@app.post("/gateway/approvals/approve")
async def gateway_approve(request: Request):
    body = await request.json()
    return await proxy("POST", f"{JONATHAN_CORE_URL}/approvals/approve", body)


@app.post("/gateway/execute")
async def gateway_execute(request: Request):
    body = await request.json()
    return await proxy("POST", f"{JONATHAN_CORE_URL}/execute", body)


@app.get("/gateway/audit")
async def gateway_audit():
    return await proxy("GET", f"{JONATHAN_CORE_URL}/audit")


@app.get("/gateway/approvals")
async def gateway_approvals():
    return await proxy("GET", f"{JONATHAN_CORE_URL}/approvals")


@app.get("/gateway/services")
async def gateway_services():
    return await proxy("GET", f"{KNOWLEDGE_GRAPH_URL}/graph/services")


@app.get("/gateway/capabilities")
async def gateway_capabilities():
    return await proxy("GET", f"{CAPABILITY_REGISTRY_URL}/capabilities")
