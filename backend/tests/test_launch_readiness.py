from __future__ import annotations

import pytest

from app.core.config import Settings
from app.db.session import SessionLocal
from app.models import User, WorkerTemplate
from app.services.system_seed import seed_system_worker_templates_and_tools
from app.services.transactional_email import generate_password_reset_token, render_template


def _signup(client, *, email: str, company: str):
    payload = {
        "full_name": "Launch User",
        "email": email,
        "password": "Passw0rd!",
        "company_name": company,
        "website": f"https://{company.lower().replace(' ', '')}.example",
        "industry": "SaaS",
    }
    res = client.post("/auth/signup", json=payload)
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _set_role(email: str, role: str) -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.role = role
        db.commit()


def _create_and_publish_template(client, headers, slug: str) -> str:
    create_payload = {
        "name": f"Launch Template {slug}",
        "slug": slug,
        "short_description": "Launch worker template",
        "description": "Template used in launch readiness tests.",
        "category": "operations",
        "worker_type": "custom_worker",
        "worker_category": "operations",
        "visibility": "workspace",
        "status": "draft",
        "instructions": "Execute worker actions and return structured output.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "launch"},
        "capabilities_json": {"launch": True},
        "actions_json": ["record_optimization_signals"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": False,
        "is_marketplace_listed": False,
        "pricing_type": "free",
        "price_cents": 0,
        "currency": "USD",
        "tags_json": ["launch"],
    }
    create_res = client.post("/workers/templates", json=create_payload, headers=headers)
    assert create_res.status_code == 200
    template_id = create_res.json()["id"]
    publish_res = client.post(
        f"/marketplace/templates/{template_id}/publish",
        json={
            "name": create_payload["name"],
            "slug": create_payload["slug"],
            "description": "Publish-ready launch template for tests.",
            "instructions": "Run safely and provide concise output.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "launch_publish"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=headers,
    )
    assert publish_res.status_code == 200
    return template_id


def test_health_and_readiness_endpoints(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["check"] == "live"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"


def test_public_market_routes_do_not_crash(client):
    public_workers = client.get("/public-workers")
    assert public_workers.status_code == 200

    headers = _signup(client, email="market-routes@example.com", company="Market Routes Co")
    marketplace = client.get("/marketplace/templates", headers=headers)
    assert marketplace.status_code == 200


def test_onboarding_state_flow_and_recommendations(client):
    headers = _signup(client, email="onboarding-launch@example.com", company="Onboarding Co")
    state_res = client.get("/onboarding/state", headers=headers)
    assert state_res.status_code == 200
    assert state_res.json()["current_step"] == "welcome"

    patch_res = client.patch(
        "/onboarding/state",
        json={"goal_category": "sales", "complete_step": "welcome", "current_step": "goal_selection"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["goal_category"] == "sales"

    rec_res = client.get("/onboarding/recommendations?goal_category=sales&limit=5", headers=headers)
    assert rec_res.status_code == 200
    body = rec_res.json()
    assert body["goal_category"] == "sales"
    assert len(body["templates"]) > 0

    # Mixed-case value should normalize and not trigger response-model 500.
    rec_mixed_res = client.get("/onboarding/recommendations?goal_category=Sales&limit=5", headers=headers)
    assert rec_mixed_res.status_code == 200
    assert rec_mixed_res.json()["goal_category"] == "sales"


def test_starter_seed_integrity_has_marketplace_depth():
    with SessionLocal() as db:
        seed_system_worker_templates_and_tools(db)
        db.commit()
        marketplace_count = (
            db.query(WorkerTemplate)
            .filter(
                WorkerTemplate.is_system_template.is_(True),
                WorkerTemplate.is_marketplace_listed.is_(True),
                WorkerTemplate.slug.is_not(None),
            )
            .count()
        )
        assert marketplace_count >= 12


def test_featured_marketplace_filter_and_admin_feature_control(client):
    owner_headers = _signup(client, email="owner-feature@example.com", company="Feature Owner Co")
    template_id = _create_and_publish_template(client, owner_headers, "launch-feature-test")

    non_admin_feature = client.post(
        f"/admin/workers/{template_id}/feature",
        json={"is_featured": True, "featured_rank": 3},
        headers=owner_headers,
    )
    assert non_admin_feature.status_code == 403

    admin_email = "admin-feature@example.com"
    admin_headers = _signup(client, email=admin_email, company="Feature Admin Co")
    _set_role(admin_email, "admin")
    feature_res = client.post(
        f"/admin/workers/{template_id}/feature",
        json={"is_featured": True, "featured_rank": 3},
        headers=admin_headers,
    )
    assert feature_res.status_code == 200
    assert feature_res.json()["template"]["is_featured"] is True

    listings_res = client.get("/marketplace/templates?featured_only=true&sort_by=featured", headers=owner_headers)
    assert listings_res.status_code == 200
    listings = listings_res.json()
    assert len(listings) > 0
    assert all(item["template"]["is_featured"] is True for item in listings)


def test_support_contact_submission_and_admin_review(client):
    create_res = client.post(
        "/support/contact",
        json={
            "name": "Prospect User",
            "email": "prospect@example.com",
            "subject": "Need launch help",
            "message": "Please share rollout guidance for our team.",
            "source": "test_suite",
        },
    )
    assert create_res.status_code == 200
    support_id = create_res.json()["id"]

    admin_email = "admin-support@example.com"
    admin_headers = _signup(client, email=admin_email, company="Support Admin Co")
    _set_role(admin_email, "admin")

    list_res = client.get("/support/requests", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(item["id"] == support_id for item in list_res.json())

    patch_res = client.patch(
        f"/support/requests/{support_id}",
        json={"status": "resolved", "resolution_note": "Handled by support"},
        headers=admin_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "resolved"


def test_password_reset_flow_and_template_rendering(client):
    email = "password-reset@example.com"
    _signup(client, email=email, company="Reset Co")

    forgot_res = client.post("/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    assert forgot_res.json()["success"] is True

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        raw_token, token_hash, expires_at = generate_password_reset_token()
        from app.models import PasswordResetToken  # local import to avoid circular typing noise in test collection

        db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
        db.commit()

    reset_res = client.post("/auth/reset-password", json={"token": raw_token, "new_password": "NewPassw0rd!"})
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    for key in [
        "welcome",
        "workspace_ready",
        "subscription_active",
        "worker_published",
        "purchase_confirmed",
        "password_reset",
        "support_request_received",
    ]:
        template = render_template(
            key,
            recipient_name="Tester",
            context={"worker_name": "Launch Worker", "amount_text": "$19.00", "reset_url": "https://example.com/reset"},
        )
        assert template.subject
        assert template.text_body
        assert template.html_body


def test_production_settings_requires_non_default_secret():
    with pytest.raises(Exception):
        Settings(environment="production", secret_key="change-me")

    with pytest.raises(Exception):
        Settings(
            environment="production",
            secret_key="super-secure-value",
        )

    cfg = Settings(
        environment="production",
        secret_key="super-secure-value",
        database_url="postgresql+psycopg2://user:pass@db.example.com:5432/app",
        redis_url="redis://redis.example.com:6379/0",
        app_base_url="https://app.example.com",
        support_email="support@example.com",
    )
    assert cfg.secret_key == "super-secure-value"
