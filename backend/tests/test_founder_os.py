from __future__ import annotations

from app.db.session import SessionLocal
from app.models import User
from app.services.founder_os import founder_os_seed_integrity_summary


def _signup(client, *, email: str, company_name: str):
    payload = {
        "full_name": "Founder User",
        "email": email,
        "password": "Passw0rd!",
        "company_name": company_name,
        "website": f"https://{company_name.lower().replace(' ', '')}.example",
        "industry": "SaaS",
    }
    res = client.post("/auth/signup", json=payload)
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _set_user_role(email: str, role: str) -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.role = role
        db.commit()


def test_founder_os_chain_seed_integrity_definition():
    summary = founder_os_seed_integrity_summary()
    assert summary["chain_template_count"] == 5
    assert {
        "daily_founder_briefing",
        "growth_campaign",
        "creator_recruitment",
        "investor_update",
        "weekly_content_engine",
    } == set(summary["template_keys"])


def test_founder_os_chains_seeded_and_overview_available(client):
    headers = _signup(client, email="founder-overview@example.com", company_name="Founder Overview Co")

    chains_res = client.get("/founder-os/chains", headers=headers)
    assert chains_res.status_code == 200
    chains_body = chains_res.json()
    assert chains_body["total"] >= 5
    keys = {item["template_key"] for item in chains_body["items"]}
    assert {"daily_founder_briefing", "growth_campaign", "investor_update"}.issubset(keys)
    assert all(len(item["workers"]) >= 3 for item in chains_body["items"])

    overview_res = client.get("/founder-os/overview", headers=headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert len(overview["available_chains"]) >= 5
    assert "metrics_snapshot" in overview


def test_founder_os_manual_run_creates_report(client):
    headers = _signup(client, email="founder-run@example.com", company_name="Founder Run Co")
    chains_res = client.get("/founder-os/chains", headers=headers)
    assert chains_res.status_code == 200
    chain = next(item for item in chains_res.json()["items"] if item["template_key"] == "growth_campaign")

    run_res = client.post(
        f"/founder-os/chains/{chain['id']}/run",
        json={
            "runtime_input": {
                "campaign_goal": "acquire beta users",
                "target_audience": "startup founders",
                "mention_self_as_worker": True,
            },
            "use_prefill_context": True,
        },
        headers=headers,
    )
    assert run_res.status_code == 200
    run_body = run_res.json()
    assert run_body["success"] is True
    assert run_body["report_id"]

    report_res = client.get(f"/founder-os/reports/{run_body['report_id']}", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["report_type"] == "growth_campaign"
    assert isinstance(report["output_json"], dict)
    assert "executed_steps" in report["output_json"]

    list_res = client.get("/founder-os/reports?report_type=growth_campaign", headers=headers)
    assert list_res.status_code == 200
    assert any(item["id"] == run_body["report_id"] for item in list_res.json()["items"])


def test_founder_os_report_workspace_permissions(client):
    owner_headers = _signup(client, email="founder-owner-a@example.com", company_name="Owner A Co")
    chains_res = client.get("/founder-os/chains", headers=owner_headers)
    chain = next(item for item in chains_res.json()["items"] if item["template_key"] == "daily_founder_briefing")
    run_res = client.post(
        f"/founder-os/chains/{chain['id']}/run",
        json={"runtime_input": {}, "use_prefill_context": True},
        headers=owner_headers,
    )
    report_id = run_res.json()["report_id"]

    other_headers = _signup(client, email="founder-owner-b@example.com", company_name="Owner B Co")
    forbidden = client.get(f"/founder-os/reports/{report_id}", headers=other_headers)
    assert forbidden.status_code == 404


def test_founder_os_automation_create_list_update(client):
    headers = _signup(client, email="founder-automation@example.com", company_name="Founder Auto Co")
    chains_res = client.get("/founder-os/chains", headers=headers)
    assert chains_res.status_code == 200
    chain = chains_res.json()["items"][0]

    create_res = client.post(
        "/founder-os/automations",
        json={
            "chain_id": chain["id"],
            "frequency": "weekly",
            "is_enabled": True,
            "runtime_input_json": {"timeframe": "weekly"},
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    automation = create_res.json()
    assert automation["chain_id"] == chain["id"]
    assert automation["is_enabled"] is True

    list_res = client.get("/founder-os/automations", headers=headers)
    assert list_res.status_code == 200
    assert any(item["id"] == automation["id"] for item in list_res.json()["items"])

    update_res = client.patch(
        f"/founder-os/automations/{automation['id']}",
        json={"is_enabled": False},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["is_enabled"] is False


def test_founder_os_requires_owner_or_admin(client):
    member_email = "founder-member@example.com"
    member_headers = _signup(client, email=member_email, company_name="Founder Member Co")
    _set_user_role(member_email, "member")

    forbidden = client.get("/founder-os/overview", headers=member_headers)
    assert forbidden.status_code == 403
