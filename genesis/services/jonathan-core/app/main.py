from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(APP_DIR), "jonathan_core.sqlite3")
CAPABILITY_REGISTRY_URL = os.getenv("CAPABILITY_REGISTRY_URL", "http://localhost:8003")
MOCK_CALENDAR_URL = os.getenv("MOCK_CALENDAR_URL", "http://localhost:8004")
GENESIS_ENV = os.getenv("GENESIS_ENV", "development")

FALLBACK_CAPABILITIES = {
    "calendar.create_event": {
        "id": "calendar.create_event",
        "name": "Create Calendar Event",
        "risk_level": "medium",
        "connector": "mock-calendar",
    },
    "calendar.list_events": {
        "id": "calendar.list_events",
        "name": "List Calendar Events",
        "risk_level": "low",
        "connector": "mock-calendar",
    },
}

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Jonathan Core", version="0.1.0", lifespan=lifespan)


class IntentRequest(BaseModel):
    message: str
    user_id: str = "demo-user"


class ApprovalRequest(BaseModel):
    approval_id: str
    approved_by: str = "demo-user"


class ExecuteRequest(BaseModel):
    approval_id: str
    executed_by: str = "demo-user"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                intent_json TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                policy_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def audit(event_type: str, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": user_id,
        "payload": payload,
        "created_at": utc_now(),
    }
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_events (id, event_type, user_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (event["id"], event_type, user_id, json.dumps(payload), event["created_at"]),
        )
    return event


def parse_intent(message: str) -> dict[str, Any]:
    lower = message.lower()
    if any(word in lower for word in ("meeting", "schedule", "calendar", "appoint")):
        return {
            "type": "calendar.create_event",
            "capability": "calendar.create_event",
            "summary": message,
            "entities": {"raw": message},
        }
    if "fax" in lower:
        return {
            "type": "fax.send",
            "capability": "fax.send",
            "summary": message,
            "entities": {"raw": message},
        }
    return {
        "type": "general",
        "capability": None,
        "summary": message,
        "entities": {"raw": message},
    }


def build_plan(intent: dict[str, Any]) -> dict[str, Any]:
    steps = [
        {"id": "understand", "description": "Interpret user intent"},
        {"id": "policy", "description": "Evaluate policy and capability gates"},
    ]
    if intent.get("capability"):
        steps.append({"id": "prepare", "description": f"Prepare {intent['capability']} execution"})
        steps.append({"id": "approve", "description": "Request user approval when required"})
        steps.append({"id": "execute", "description": "Execute via registered connector"})
    steps.append({"id": "explain", "description": "Explain outcome and write audit"})
    return {"steps": steps, "capability": intent.get("capability")}


def lookup_capability(capability_id: str | None) -> dict[str, Any]:
    if not capability_id:
        return {"found": False, "source": "none", "capability": None}
    try:
        import httpx

        response = httpx.get(f"{CAPABILITY_REGISTRY_URL}/capabilities/{capability_id}", timeout=2.0)
        if response.status_code == 200:
            return {"found": True, "source": "registry", "capability": response.json()}
        if response.status_code == 404:
            return {"found": False, "source": "registry", "capability": None}
    except Exception:
        pass

    if GENESIS_ENV == "production":
        return {"found": False, "source": "registry_unavailable", "capability": None}

    fallback = FALLBACK_CAPABILITIES.get(capability_id)
    if fallback:
        return {"found": True, "source": "fallback", "capability": fallback}
    return {"found": False, "source": "fallback", "capability": None}


def evaluate_policy(intent: dict[str, Any], capability_result: dict[str, Any]) -> dict[str, Any]:
    capability_id = intent.get("capability")
    if not capability_id:
        return {
            "decision": "allow",
            "risk_level": "low",
            "requires_approval": False,
            "reason": "General informational intent; no connector execution required.",
            "capability_result": capability_result,
        }

    if not capability_result.get("found"):
        return {
            "decision": "block",
            "risk_level": "high",
            "requires_approval": False,
            "reason": f"Capability '{capability_id}' is not registered.",
            "capability_result": capability_result,
        }

    cap = capability_result["capability"] or {}
    risk = cap.get("risk_level", "medium")
    requires_approval = risk in ("medium", "high")
    return {
        "decision": "allow",
        "risk_level": risk,
        "requires_approval": requires_approval,
        "reason": "Capability registered and within policy.",
        "capability_result": capability_result,
    }


def explain(intent: dict[str, Any], policy: dict[str, Any], status: str) -> str:
    if policy["decision"] == "block":
        return f"I cannot proceed: {policy['reason']}"
    if status == "pending_approval":
        return (
            f"I understood your request to '{intent['summary']}'. "
            f"Policy risk is {policy['risk_level']}, so I need your approval before executing."
        )
    if status == "ready":
        return f"Ready to help with '{intent['summary']}' without connector execution."
    return f"Processed intent '{intent['summary']}' with status {status}."


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jonathan-core"}


@app.post("/intent")
def create_intent(body: IntentRequest) -> dict[str, Any]:
    intent = parse_intent(body.message)
    plan = build_plan(intent)
    capability_result = lookup_capability(intent.get("capability"))
    policy = evaluate_policy(intent, capability_result)

    approval_id = None
    status = "ready"
    if policy["decision"] == "block":
        status = "blocked"
    elif policy.get("requires_approval"):
        status = "pending_approval"
        approval_id = str(uuid.uuid4())
        now = utc_now()
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO approvals (id, user_id, intent_json, plan_json, policy_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_id,
                    body.user_id,
                    json.dumps(intent),
                    json.dumps(plan),
                    json.dumps(policy),
                    "pending",
                    now,
                    now,
                ),
            )

    explanation = explain(intent, policy, status)
    result = {
        "intent": intent,
        "plan": plan,
        "policy": policy,
        "execution": {
            "status": status,
            "approval_id": approval_id,
        },
        "explanation": explanation,
    }
    audit("intent.processed", body.user_id, result)
    return result


@app.get("/approvals")
def list_approvals() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM approvals ORDER BY created_at DESC").fetchall()
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "intent": json.loads(row["intent_json"]),
            "plan": json.loads(row["plan_json"]),
            "policy": json.loads(row["policy_json"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


@app.post("/approvals/approve")
def approve(body: ApprovalRequest) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (body.approval_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Approval not found")
        if row["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Approval is {row['status']}")
        now = utc_now()
        conn.execute(
            "UPDATE approvals SET status = ?, updated_at = ? WHERE id = ?",
            ("approved", now, body.approval_id),
        )
    payload = {"approval_id": body.approval_id, "approved_by": body.approved_by, "status": "approved"}
    audit("approval.approved", body.approved_by, payload)
    return payload


@app.post("/execute")
def execute(body: ExecuteRequest) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM approvals WHERE id = ?", (body.approval_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Approval not found")
        if row["status"] != "approved":
            raise HTTPException(status_code=400, detail="Approval must be approved before execution")
        intent = json.loads(row["intent_json"])
        policy = json.loads(row["policy_json"])

    execution_result: dict[str, Any] = {"status": "completed", "connector": None, "result": None}
    capability_id = intent.get("capability")
    if capability_id == "calendar.create_event":
        try:
            import httpx

            response = httpx.post(
                f"{MOCK_CALENDAR_URL}/calendar/events",
                json={
                    "title": intent.get("summary", "Meeting"),
                    "created_by": body.executed_by,
                    "source_approval_id": body.approval_id,
                },
                timeout=5.0,
            )
            response.raise_for_status()
            execution_result["connector"] = "mock-calendar"
            execution_result["result"] = response.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Connector execution failed: {exc}") from exc

    with get_conn() as conn:
        conn.execute(
            "UPDATE approvals SET status = ?, updated_at = ? WHERE id = ?",
            ("executed", utc_now(), body.approval_id),
        )

    payload = {
        "approval_id": body.approval_id,
        "executed_by": body.executed_by,
        "intent": intent,
        "policy": policy,
        "execution": execution_result,
        "explanation": f"Executed '{intent.get('summary')}' successfully.",
    }
    audit("execution.completed", body.executed_by, payload)
    return payload


@app.get("/audit")
def list_audit() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM audit_events ORDER BY created_at DESC").fetchall()
    return [
        {
            "id": row["id"],
            "event_type": row["event_type"],
            "user_id": row["user_id"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
