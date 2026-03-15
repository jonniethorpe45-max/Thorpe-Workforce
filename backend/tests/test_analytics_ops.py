from __future__ import annotations

from datetime import UTC, datetime
import uuid

from app.db.session import SessionLocal
from app.models import User, WorkerRevenueEvent


def _signup(client, *, email: str, company_name: str):
    payload = {
        "full_name": "Analytics User",
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


def _create_template(client, headers, *, slug: str):
    payload = {
        "name": f"Analytics Template {slug}",
        "slug": slug,
        "short_description": "Analytics test template",
        "description": "Template used to validate analytics and platform operations behavior.",
        "category": "analytics",
        "worker_type": "custom_worker",
        "worker_category": "analytics",
        "visibility": "workspace",
        "status": "draft",
        "instructions": "Execute worker tasks and return structured output.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "analytics"},
        "capabilities_json": {"supports_reporting": True},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": True,
        "is_marketplace_listed": False,
        "pricing_type": "free",
        "price_cents": 0,
        "currency": "USD",
        "tags_json": ["analytics"],
    }
    res = client.post("/workers/templates", json=payload, headers=headers)
    assert res.status_code == 200
    return res.json()


def _publish_marketplace_template(client, headers, template_id: str, slug: str, *, pricing_type: str = "free", price_cents: int = 0):
    res = client.post(
        f"/marketplace/templates/{template_id}/publish",
        json={
            "name": f"Published {slug}",
            "slug": slug,
            "description": "Published template for analytics tests with complete metadata.",
            "instructions": "Run safely with clear guardrails and structured output.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "publish"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": pricing_type,
            "price_cents": price_cents,
            "currency": "USD",
        },
        headers=headers,
    )
    assert res.status_code == 200
    return res.json()


def _install_and_run_once(client, headers, template_id: str) -> str:
    install_res = client.post(
        f"/workers/templates/{template_id}/install",
        json={"instance_name": "Analytics Instance"},
        headers=headers,
    )
    assert install_res.status_code == 200
    instance_id = install_res.json()["id"]
    run_res = client.post(
        f"/workers/instances/{instance_id}/run",
        json={"runtime_input": {"source": "analytics_test"}},
        headers=headers,
    )
    assert run_res.status_code == 200
    return run_res.json()["run_id"]


def test_creator_dashboard_and_worker_analytics(client):
    headers = _signup(client, email="creator-analytics@example.com", company_name="Creator Analytics Co")
    template = _create_template(client, headers, slug="creator-analytics")
    _publish_marketplace_template(client, headers, template["id"], slug="creator-analytics")
    _install_and_run_once(client, headers, template["id"])

    summary_res = client.get("/creator/dashboard/summary?range=7d", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["published_workers_count"] >= 1
    assert len(summary["recent_install_trend"]) == 7
    assert len(summary["recent_run_trend"]) == 7

    workers_res = client.get("/creator/workers", headers=headers)
    assert workers_res.status_code == 200
    assert any(item["worker_template_id"] == template["id"] for item in workers_res.json())

    analytics_res = client.get(f"/creator/workers/{template['id']}/analytics?range=7d", headers=headers)
    assert analytics_res.status_code == 200
    worker_analytics = analytics_res.json()
    assert len(worker_analytics["installs_over_time"]) == 7
    assert len(worker_analytics["runs_over_time"]) == 7
    assert len(worker_analytics["active_workspaces_over_time"]) == 7


def test_workspace_analytics_summary_and_usage_history_shape(client):
    headers = _signup(client, email="workspace-analytics@example.com", company_name="Workspace Analytics Co")
    template = _create_template(client, headers, slug="workspace-analytics")
    _publish_marketplace_template(client, headers, template["id"], slug="workspace-analytics")
    _install_and_run_once(client, headers, template["id"])

    summary_res = client.get("/analytics/workspace/summary?range=30d", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["installed_workers_count"] >= 1
    assert summary["total_runs"] >= 1
    assert "plan" in summary
    assert "limits" in summary
    assert "usage" in summary

    history_res = client.get("/analytics/workspace/usage-history?range=7d", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 7
    assert {"date", "worker_runs", "chain_runs", "installs", "successful_runs", "failed_runs"} <= set(history[0].keys())


def test_admin_summary_access_control(client):
    owner_headers = _signup(client, email="owner-not-admin@example.com", company_name="Owner Co")
    forbidden_res = client.get("/admin/analytics/summary", headers=owner_headers)
    assert forbidden_res.status_code == 403

    admin_email = "platform-admin@example.com"
    admin_headers = _signup(client, email=admin_email, company_name="Admin Co")
    _set_user_role(admin_email, "admin")
    allowed_res = client.get("/admin/analytics/summary", headers=admin_headers)
    assert allowed_res.status_code == 200
    payload = allowed_res.json()
    assert "total_users" in payload
    assert "subscriptions_by_plan" in payload


def test_moderation_hide_removes_worker_from_public_and_marketplace(client):
    creator_headers = _signup(client, email="creator-moderation@example.com", company_name="Creator Mod Co")
    template = _create_template(client, creator_headers, slug="creator-moderation")
    _publish_marketplace_template(client, creator_headers, template["id"], slug="creator-moderation")

    admin_email = "moderator@example.com"
    admin_headers = _signup(client, email=admin_email, company_name="Moderator Co")
    _set_user_role(admin_email, "admin")

    moderate_res = client.post(
        f"/admin/workers/{template['id']}/moderate",
        json={"action": "hide", "moderation_notes": "Hidden for trust and safety test"},
        headers=admin_headers,
    )
    assert moderate_res.status_code == 200
    assert moderate_res.json()["moderation_status"] == "hidden"

    marketplace_list = client.get("/marketplace/templates", headers=creator_headers)
    assert marketplace_list.status_code == 200
    assert all(item["template"]["id"] != template["id"] for item in marketplace_list.json())

    public_list = client.get("/public-workers")
    assert public_list.status_code == 200
    assert all(item["id"] != template["id"] for item in public_list.json())


def test_report_submission_flow_and_report_count(client):
    headers = _signup(client, email="reporter@example.com", company_name="Reporter Co")
    template = _create_template(client, headers, slug="report-target")

    report_res = client.post(
        f"/workers/{template['id']}/report",
        json={"reason": "misleading_output", "details": "Worker generated low-quality output in test scenario."},
        headers=headers,
    )
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["worker_template_id"] == template["id"]
    assert report["status"] == "open"

    detail_res = client.get(f"/workers/templates/{template['id']}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["report_count"] >= 1


def test_creator_revenue_estimation_for_paid_worker_path(client):
    creator_email = "creator-paid@example.com"
    creator_headers = _signup(client, email=creator_email, company_name="Paid Creator Co")
    template = _create_template(client, creator_headers, slug="paid-creator-template")
    _publish_marketplace_template(
        client,
        creator_headers,
        template["id"],
        slug="paid-creator-template",
        pricing_type="one_time",
        price_cents=1500,
    )

    with SessionLocal() as db:
        creator = db.query(User).filter(User.email == creator_email).first()
        assert creator is not None
        event = WorkerRevenueEvent(
            worker_template_id=uuid.UUID(template["id"]),
            creator_user_id=creator.id,
            workspace_id=creator.workspace_id,
            revenue_type="purchase_completed",
            gross_cents=1500,
            platform_fee_cents=450,
            creator_payout_cents=1050,
            currency="USD",
            reference_type="test_purchase",
            reference_id="paid-worker-test",
            created_at=datetime.now(UTC),
        )
        db.add(event)
        db.commit()

    payouts_res = client.get("/creator/payouts/summary?range=30d", headers=creator_headers)
    assert payouts_res.status_code == 200
    payouts = payouts_res.json()
    assert payouts["estimated_gross_revenue"] >= 1500
    assert payouts["estimated_creator_share"] >= 1050
    assert payouts["estimated_platform_share"] >= 450


def test_creator_analytics_permissions_and_date_window_validation(client):
    creator_headers = _signup(client, email="creator-owner@example.com", company_name="Creator Owner Co")
    other_headers = _signup(client, email="creator-other@example.com", company_name="Creator Other Co")
    template = _create_template(client, creator_headers, slug="creator-owner-only")

    cross_access = client.get(f"/creator/workers/{template['id']}/analytics?range=7d", headers=other_headers)
    assert cross_access.status_code == 404

    bad_window = client.get(
        "/creator/dashboard/summary?start_date=2026-03-10&end_date=2026-03-01",
        headers=creator_headers,
    )
    assert bad_window.status_code == 400
