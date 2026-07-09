import os
import sys

import pytest
from fastapi.testclient import TestClient

CORE_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "jonathan-core")
sys.path.insert(0, CORE_DIR)

from app import main as jonathan_main  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.sqlite3"
    monkeypatch.setattr(jonathan_main, "DB_PATH", str(db))
    jonathan_main.init_db()
    with TestClient(jonathan_main.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "jonathan-core"


def test_intent_requires_approval_for_meeting(client):
    response = client.post(
        "/intent",
        json={"message": "Schedule a meeting with Bob tomorrow at 10", "user_id": "demo-user"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["status"] == "pending_approval"
    assert body["execution"]["approval_id"]
    assert body["policy"]["decision"] == "allow"


def test_blocked_capability(client):
    response = client.post(
        "/intent",
        json={"message": "Send a fax to Bob", "user_id": "demo-user"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["status"] == "blocked"
    assert body["policy"]["decision"] == "block"


def test_approve_and_audit(client):
    intent = client.post(
        "/intent",
        json={"message": "Schedule a meeting with Alice", "user_id": "demo-user"},
    ).json()
    approval_id = intent["execution"]["approval_id"]
    approved = client.post(
        "/approvals/approve",
        json={"approval_id": approval_id, "approved_by": "demo-user"},
    )
    assert approved.status_code == 200
    audit = client.get("/audit").json()
    assert any(event["event_type"] == "approval.approved" for event in audit)
