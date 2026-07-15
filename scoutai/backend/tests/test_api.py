from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "scoutai-api"
    assert "demo_mode" in body


def test_research_demo_brief():
    res = client.post(
        "/research",
        json={"query": "AI receptionist market for dental clinics", "focus": "market"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["query"].startswith("AI receptionist")
    assert body["mode"] in {"demo", "live"}
    assert len(body["findings"]) >= 1
    assert len(body["next_actions"]) >= 1
