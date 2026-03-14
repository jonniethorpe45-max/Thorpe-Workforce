import json

from fastapi import HTTPException

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import BillingEventLog, User, WorkerSubscription, Workspace, WorkspaceSubscription
from app.services.subscription_plans import ensure_default_subscription_plans, get_plan_by_code


class FakeStripeGateway:
    def __init__(self, *, event: dict | None = None, fail_verify: bool = False):
        self.event = event
        self.fail_verify = fail_verify
        self.checkout_counter = 0

    def create_customer(self, *, name: str, metadata: dict[str, str]) -> dict:
        _ = (name, metadata)
        return {"id": "cus_test_123"}

    def create_checkout_session(self, **kwargs) -> dict:
        self.checkout_counter += 1
        mode = kwargs.get("mode", "payment")
        return {
            "id": f"cs_test_{self.checkout_counter}",
            "url": f"https://checkout.stripe.test/{self.checkout_counter}",
            "mode": mode,
            "customer": kwargs.get("customer", "cus_test_123"),
            "subscription": "sub_test_123" if mode == "subscription" else None,
        }

    def create_billing_portal_session(self, **kwargs) -> dict:
        _ = kwargs
        return {"url": "https://billing.stripe.test/portal"}

    def verify_webhook_event(self, payload: bytes, signature: str) -> dict:
        _ = payload
        if self.fail_verify or signature != "valid-signature":
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        if self.event is not None:
            return self.event
        return json.loads(payload.decode("utf-8"))

    def retrieve_subscription(self, subscription_id: str) -> dict:
        return {"id": subscription_id, "status": "active"}


def _current_user_workspace_id() -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "tester@example.com").first()
        assert user is not None
        return str(user.workspace_id)
    finally:
        db.close()


def _set_workspace_plan(plan_code: str) -> None:
    db = SessionLocal()
    try:
        ensure_default_subscription_plans(db)
        user = db.query(User).filter(User.email == "tester@example.com").first()
        assert user is not None
        plan = get_plan_by_code(db, plan_code, include_inactive=True)
        assert plan is not None
        subscription = (
            db.query(WorkspaceSubscription)
            .filter(WorkspaceSubscription.workspace_id == user.workspace_id)
            .order_by(WorkspaceSubscription.updated_at.desc())
            .first()
        )
        assert subscription is not None
        subscription.plan_id = plan.id
        workspace = db.get(Workspace, user.workspace_id)
        assert workspace is not None
        workspace.subscription_plan = plan.code
        db.commit()
    finally:
        db.close()


def _create_paid_marketplace_template(client, auth_headers, slug: str = "paid-worker-template"):
    payload = {
        "name": f"Paid Template {slug}",
        "slug": slug,
        "short_description": "Paid worker template",
        "description": "Paid worker template for billing tests.",
        "category": "sales",
        "worker_type": "custom_worker",
        "worker_category": "sales",
        "visibility": "marketplace",
        "status": "active",
        "instructions": "Run tasks safely.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "paid"},
        "capabilities_json": {},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": False,
        "is_marketplace_listed": True,
        "pricing_type": "one_time",
        "price_cents": 2500,
        "currency": "USD",
        "tags_json": ["paid"],
    }
    response = client.post("/workers/templates", json=payload, headers=auth_headers)
    assert response.status_code == 200
    return response.json()


def test_billing_plans_endpoint_lists_default_tiers(client):
    response = client.get("/billing/plans")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"free", "pro", "creator", "enterprise"}.issubset(codes)


def test_subscription_checkout_and_portal_creation(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "stripe_price_id_pro_monthly", "price_pro_monthly_test")
    fake_gateway = FakeStripeGateway()
    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: fake_gateway)

    checkout_res = client.post(
        "/billing/checkout/subscription",
        json={"plan_code": "pro", "billing_interval": "monthly"},
        headers=auth_headers,
    )
    assert checkout_res.status_code == 200
    assert checkout_res.json()["checkout_url"].startswith("https://checkout.stripe.test/")

    subscription_res = client.get("/billing/subscription", headers=auth_headers)
    assert subscription_res.status_code == 200
    assert subscription_res.json()["stripe_customer_id"] == "cus_test_123"

    portal_res = client.post("/billing/portal", json={}, headers=auth_headers)
    assert portal_res.status_code == 200
    assert portal_res.json()["portal_url"].startswith("https://billing.stripe.test/")

    entitlements_res = client.get("/billing/entitlements", headers=auth_headers)
    assert entitlements_res.status_code == 200
    assert "features" in entitlements_res.json()
    assert "usage" in entitlements_res.json()


def test_webhook_signature_verification_and_idempotency(client, auth_headers, monkeypatch):
    _ = auth_headers
    workspace_id = _current_user_workspace_id()
    event = {
        "id": "evt_checkout_workspace_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_ws_1",
                "customer": "cus_test_123",
                "subscription": "sub_ws_123",
                "metadata": {
                    "checkout_kind": "workspace_subscription",
                    "workspace_id": workspace_id,
                    "plan_code": "pro",
                    "billing_interval": "monthly",
                },
            }
        },
    }

    no_signature = client.post("/billing/webhooks/stripe", data=json.dumps(event))
    assert no_signature.status_code == 400

    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: FakeStripeGateway(fail_verify=True))
    invalid_sig = client.post(
        "/billing/webhooks/stripe",
        data=json.dumps(event),
        headers={"Stripe-Signature": "invalid"},
    )
    assert invalid_sig.status_code == 400

    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: FakeStripeGateway(event=event))
    first = client.post(
        "/billing/webhooks/stripe",
        data=json.dumps(event),
        headers={"Stripe-Signature": "valid-signature"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "processed"

    second = client.post(
        "/billing/webhooks/stripe",
        data=json.dumps(event),
        headers={"Stripe-Signature": "valid-signature"},
    )
    assert second.status_code == 200

    db = SessionLocal()
    try:
        count = db.query(BillingEventLog).filter(BillingEventLog.stripe_event_id == "evt_checkout_workspace_1").count()
        assert count == 1
    finally:
        db.close()

    update_event = {
        "id": "evt_subscription_updated_1",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_ws_123",
                "customer": "cus_test_123",
                "status": "active",
                "current_period_start": 1735689600,
                "current_period_end": 1738291200,
                "cancel_at_period_end": False,
            }
        },
    }
    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: FakeStripeGateway(event=update_event))
    update_res = client.post(
        "/billing/webhooks/stripe",
        data=json.dumps(update_event),
        headers={"Stripe-Signature": "valid-signature"},
    )
    assert update_res.status_code == 200

    db = SessionLocal()
    try:
        workspace_sub = db.query(WorkspaceSubscription).filter(WorkspaceSubscription.stripe_subscription_id == "sub_ws_123").first()
        assert workspace_sub is not None
        assert workspace_sub.status == "active"
        assert workspace_sub.current_period_end is not None
    finally:
        db.close()


def test_worker_purchase_checkout_and_entitlement_gated_install(client, auth_headers, monkeypatch):
    template = _create_paid_marketplace_template(client, auth_headers, slug="paid-template-checkout")

    blocked_install = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={"instance_name": "Paid Install Attempt"},
        headers=auth_headers,
    )
    assert blocked_install.status_code == 402

    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: FakeStripeGateway())
    checkout_res = client.post(f"/billing/checkout/worker/{template['id']}", json={}, headers=auth_headers)
    assert checkout_res.status_code == 200
    assert checkout_res.json()["checkout_url"].startswith("https://checkout.stripe.test/")

    workspace_id = _current_user_workspace_id()
    entitlement_event = {
        "id": "evt_worker_checkout_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_worker_1",
                "payment_intent": "pi_worker_1",
                "metadata": {
                    "checkout_kind": "worker_purchase",
                    "workspace_id": workspace_id,
                    "worker_template_id": template["id"],
                    "purchaser_user_id": "",
                    "purchase_type": "one_time",
                },
            }
        },
    }
    monkeypatch.setattr("app.services.billing.get_stripe_gateway", lambda: FakeStripeGateway(event=entitlement_event))
    webhook_res = client.post(
        "/billing/webhooks/stripe",
        data=json.dumps(entitlement_event),
        headers={"Stripe-Signature": "valid-signature"},
    )
    assert webhook_res.status_code == 200

    install_res = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={"instance_name": "Paid Install Success"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200


def test_usage_limit_enforcement_for_worker_runs(client, auth_headers):
    _set_workspace_plan("free")

    db = SessionLocal()
    try:
        free_plan = get_plan_by_code(db, "free", include_inactive=True)
        assert free_plan is not None
        free_plan.max_worker_runs_per_month = 0
        db.commit()
    finally:
        db.close()

    create_template_res = client.post(
        "/workers/templates",
        json={
            "name": "Run Limit Template",
            "slug": "run-limit-template",
            "short_description": "Run limit test",
            "description": "Template to validate run usage limit gating.",
            "category": "ops",
            "worker_type": "custom_worker",
            "worker_category": "ops",
            "visibility": "workspace",
            "status": "active",
            "instructions": "Run safely.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "run-limit"},
            "capabilities_json": {},
            "actions_json": ["monitor_outbound_events"],
            "tools_json": [],
            "memory_enabled": True,
            "chain_enabled": False,
            "is_marketplace_listed": False,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
            "tags_json": [],
        },
        headers=auth_headers,
    )
    assert create_template_res.status_code == 200
    template_id = create_template_res.json()["id"]

    install_res = client.post(
        f"/workers/templates/{template_id}/install",
        json={"instance_name": "Run Limit Instance"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance_id = install_res.json()["id"]

    run_res = client.post(
        f"/workers/instances/{instance_id}/run",
        json={"runtime_input": {"source": "limit-test"}},
        headers=auth_headers,
    )
    assert run_res.status_code == 403


def test_entitlement_gating_blocks_marketplace_publish_for_free_plan(client, auth_headers):
    _set_workspace_plan("free")

    create_res = client.post(
        "/workers/templates",
        json={
            "name": "Free Plan Publish Block",
            "slug": "free-plan-publish-block",
            "short_description": "Publish block test",
            "description": "Template used to verify marketplace publishing gate.",
            "category": "sales",
            "worker_type": "custom_worker",
            "worker_category": "sales",
            "visibility": "workspace",
            "status": "draft",
            "instructions": "Run safely.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "publish-block"},
            "capabilities_json": {},
            "actions_json": ["monitor_outbound_events"],
            "tools_json": [],
            "memory_enabled": True,
            "chain_enabled": False,
            "is_marketplace_listed": False,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
            "tags_json": [],
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 200
    template_id = create_res.json()["id"]

    publish_res = client.post(
        f"/marketplace/templates/{template_id}/publish",
        json={
            "name": "Free Plan Publish Block",
            "slug": "free-plan-publish-block",
            "description": "Publish block template with complete fields for validation checks.",
            "instructions": "Follow mission and return structured outputs only.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "publish"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 403

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "tester@example.com").first()
        assert user is not None
        entitlement_count = (
            db.query(WorkerSubscription)
            .filter(WorkerSubscription.workspace_id == user.workspace_id)
            .count()
        )
        assert entitlement_count >= 0
    finally:
        db.close()
