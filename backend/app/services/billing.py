import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from fastapi import HTTPException
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    BillingEventLog,
    BillingEventStatus,
    BillingInterval,
    CreatorMonetizationProfile,
    Lead,
    SubscriptionPlan,
    WorkerAccessType,
    WorkerEntitlementStatus,
    WorkerInstance,
    WorkerMemoryScope,
    WorkerRun,
    WorkerSubscription,
    WorkerTemplate,
    WorkerTemplateDraft,
    Workspace,
    WorkspaceSubscription,
    WorkspaceSubscriptionStatus,
)
from app.services.subscription_plans import ensure_default_subscription_plans, get_plan_by_code

try:  # pragma: no cover - optional dependency guard
    import stripe
except Exception:  # pragma: no cover - fallback if stripe is not installed
    stripe = None


ACTIVE_WORKSPACE_SUBSCRIPTION_STATES = {
    WorkspaceSubscriptionStatus.TRIALING.value,
    WorkspaceSubscriptionStatus.ACTIVE.value,
    WorkspaceSubscriptionStatus.PAST_DUE.value,
}
ACTIVE_WORKER_ENTITLEMENT_STATES = {
    WorkerEntitlementStatus.ACTIVE.value,
    WorkerEntitlementStatus.PENDING.value,
}


@dataclass(frozen=True)
class BillingResult:
    billing_status: str
    is_captured: bool
    external_reference: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class CheckoutSessionResult:
    session_id: str
    checkout_url: str
    mode: str


@dataclass(frozen=True)
class WorkspaceEntitlements:
    plan: SubscriptionPlan
    workspace_subscription: WorkspaceSubscription | None
    usage: dict[str, int]
    limits: dict[str, int | None]
    features: dict[str, bool]


class StripeGateway(Protocol):
    def create_customer(self, *, name: str, metadata: dict[str, str]) -> dict[str, Any]: ...

    def create_checkout_session(self, **kwargs: Any) -> dict[str, Any]: ...

    def create_billing_portal_session(self, **kwargs: Any) -> dict[str, Any]: ...

    def verify_webhook_event(self, payload: bytes, signature: str) -> dict[str, Any]: ...

    def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]: ...


class StripeSDKGateway:
    def __init__(self) -> None:
        if stripe is None:
            raise HTTPException(status_code=500, detail="Stripe SDK is not installed")
        if not settings.stripe_secret_key:
            raise HTTPException(status_code=503, detail="Stripe is not configured")
        stripe.api_key = settings.stripe_secret_key

    def create_customer(self, *, name: str, metadata: dict[str, str]) -> dict[str, Any]:
        return stripe.Customer.create(name=name, metadata=metadata)

    def create_checkout_session(self, **kwargs: Any) -> dict[str, Any]:
        return stripe.checkout.Session.create(**kwargs)

    def create_billing_portal_session(self, **kwargs: Any) -> dict[str, Any]:
        return stripe.billing_portal.Session.create(**kwargs)

    def verify_webhook_event(self, payload: bytes, signature: str) -> dict[str, Any]:
        if not settings.stripe_webhook_secret:
            raise HTTPException(status_code=503, detail="Stripe webhook secret is not configured")
        return stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=settings.stripe_webhook_secret)

    def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        return stripe.Subscription.retrieve(subscription_id)


def get_stripe_gateway() -> StripeGateway:
    return StripeSDKGateway()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _from_unix(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=UTC)


def _first_active_worker_subscription(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    worker_template_id: uuid.UUID,
) -> WorkerSubscription | None:
    return (
        db.query(WorkerSubscription)
        .filter(
            WorkerSubscription.workspace_id == workspace_id,
            WorkerSubscription.worker_template_id == worker_template_id,
            WorkerSubscription.is_active.is_(True),
            WorkerSubscription.status.in_(tuple(ACTIVE_WORKER_ENTITLEMENT_STATES)),
        )
        .order_by(WorkerSubscription.granted_at.desc())
        .first()
    )


def _resolve_legacy_plan_code(workspace: Workspace) -> str:
    current = (workspace.subscription_plan or "").strip().lower()
    if current in {"starter", "legacy"}:
        return "starter"
    if current in {"pro", "creator", "enterprise", "free"}:
        return current
    return "starter"


def get_workspace_subscription(db: Session, *, workspace_id: uuid.UUID) -> WorkspaceSubscription | None:
    return (
        db.query(WorkspaceSubscription)
        .filter(WorkspaceSubscription.workspace_id == workspace_id)
        .order_by(WorkspaceSubscription.updated_at.desc(), WorkspaceSubscription.created_at.desc())
        .first()
    )


def ensure_workspace_subscription(db: Session, *, workspace: Workspace) -> WorkspaceSubscription:
    ensure_default_subscription_plans(db)
    existing = get_workspace_subscription(db, workspace_id=workspace.id)
    if existing:
        return existing
    plan_code = _resolve_legacy_plan_code(workspace)
    plan = get_plan_by_code(db, plan_code, include_inactive=True) or get_plan_by_code(db, "free", include_inactive=True)
    now = _utc_now()
    record = WorkspaceSubscription(
        workspace_id=workspace.id,
        plan_id=plan.id if plan else None,
        status=WorkspaceSubscriptionStatus.ACTIVE.value,
        billing_interval=BillingInterval.MONTHLY.value,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        subscribed_at=now,
    )
    db.add(record)
    db.flush()
    return record


def resolve_workspace_plan(db: Session, *, workspace_id: uuid.UUID) -> tuple[SubscriptionPlan, WorkspaceSubscription | None]:
    ensure_default_subscription_plans(db)
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    subscription = ensure_workspace_subscription(db, workspace=workspace)
    plan = db.get(SubscriptionPlan, subscription.plan_id) if subscription and subscription.plan_id else None
    if not plan:
        plan = get_plan_by_code(db, _resolve_legacy_plan_code(workspace), include_inactive=True)
    if not plan:
        plan = get_plan_by_code(db, "free", include_inactive=True)
    if not plan:
        raise HTTPException(status_code=500, detail="No subscription plans are configured")
    return plan, subscription


def _start_of_current_month() -> datetime:
    now = _utc_now()
    return datetime(now.year, now.month, 1, tzinfo=UTC)


def _compute_workspace_usage(db: Session, *, workspace_id: uuid.UUID) -> dict[str, int]:
    month_start = _start_of_current_month()
    draft_count = (
        db.query(func.count(WorkerTemplateDraft.id))
        .filter(WorkerTemplateDraft.workspace_id == workspace_id)
        .scalar()
    )
    published_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.workspace_id == workspace_id,
            WorkerTemplate.status == "active",
            WorkerTemplate.visibility.in_(("public", "marketplace")),
        )
        .scalar()
    )
    install_count = (
        db.query(func.count(WorkerInstance.id))
        .filter(WorkerInstance.workspace_id == workspace_id)
        .scalar()
    )
    run_count = (
        db.query(func.count(WorkerRun.id))
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= month_start,
        )
        .scalar()
    )
    return {
        "worker_drafts": int(draft_count or 0),
        "published_workers": int(published_count or 0),
        "worker_installs": int(install_count or 0),
        "worker_runs_month": int(run_count or 0),
    }


def get_workspace_entitlements(db: Session, *, workspace_id: uuid.UUID) -> WorkspaceEntitlements:
    plan, workspace_subscription = resolve_workspace_plan(db, workspace_id=workspace_id)
    usage = _compute_workspace_usage(db, workspace_id=workspace_id)
    limits = {
        "max_worker_drafts": plan.max_worker_drafts,
        "max_published_workers": plan.max_published_workers,
        "max_worker_installs_per_workspace": plan.max_worker_installs_per_workspace,
        "max_worker_runs_per_month": plan.max_worker_runs_per_month,
    }
    features = {
        "allow_worker_builder": bool(plan.allow_worker_builder),
        "allow_marketplace_publishing": bool(plan.allow_marketplace_publishing),
        "allow_private_workers": bool(plan.allow_private_workers),
        "allow_public_workers": bool(plan.allow_public_workers),
        "allow_marketplace_install": bool(plan.allow_marketplace_install),
        "allow_team_features": bool(plan.allow_team_features),
    }
    return WorkspaceEntitlements(
        plan=plan,
        workspace_subscription=workspace_subscription,
        usage=usage,
        limits=limits,
        features=features,
    )


def _assert_limit(limit: int | None, value: int, *, error_message: str) -> None:
    if limit is None:
        return
    if int(value) >= int(limit):
        raise HTTPException(status_code=403, detail=error_message)


def can_use_worker_builder(db: Session, *, workspace_id: uuid.UUID) -> bool:
    return bool(get_workspace_entitlements(db, workspace_id=workspace_id).features["allow_worker_builder"])


def can_publish_to_marketplace(db: Session, *, workspace_id: uuid.UUID) -> bool:
    return bool(get_workspace_entitlements(db, workspace_id=workspace_id).features["allow_marketplace_publishing"])


def can_create_more_worker_drafts(db: Session, *, workspace_id: uuid.UUID) -> bool:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    limit = ent.limits["max_worker_drafts"]
    return limit is None or ent.usage["worker_drafts"] < limit


def can_publish_more_workers(db: Session, *, workspace_id: uuid.UUID) -> bool:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    limit = ent.limits["max_published_workers"]
    return limit is None or ent.usage["published_workers"] < limit


def can_install_worker(db: Session, *, workspace_id: uuid.UUID) -> bool:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    if not ent.features["allow_marketplace_install"]:
        return False
    limit = ent.limits["max_worker_installs_per_workspace"]
    return limit is None or ent.usage["worker_installs"] < limit


def can_run_worker(db: Session, *, workspace_id: uuid.UUID) -> bool:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    limit = ent.limits["max_worker_runs_per_month"]
    return limit is None or ent.usage["worker_runs_month"] < limit


def can_access_paid_worker(db: Session, *, workspace_id: uuid.UUID, worker_template_id: uuid.UUID) -> bool:
    template = db.get(WorkerTemplate, worker_template_id)
    if not template:
        return False
    if template.pricing_type in {"free", "internal"} or int(template.price_cents or 0) <= 0:
        return True
    entitlement = _first_active_worker_subscription(
        db,
        workspace_id=workspace_id,
        worker_template_id=worker_template_id,
    )
    return entitlement is not None


def ensure_creator_monetization_profile(db: Session, *, user_id: uuid.UUID) -> CreatorMonetizationProfile:
    profile = (
        db.query(CreatorMonetizationProfile)
        .filter(CreatorMonetizationProfile.user_id == user_id)
        .first()
    )
    if profile:
        return profile
    profile = CreatorMonetizationProfile(user_id=user_id)
    db.add(profile)
    db.flush()
    return profile


def require_worker_builder_access(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    if not ent.features["allow_worker_builder"]:
        raise HTTPException(status_code=403, detail="Current plan does not include Worker Builder")


def require_worker_draft_creation_access(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    if not ent.features["allow_worker_builder"]:
        raise HTTPException(status_code=403, detail="Current plan does not include Worker Builder")
    _assert_limit(
        ent.limits["max_worker_drafts"],
        ent.usage["worker_drafts"],
        error_message="Draft limit reached for current plan. Upgrade to create more drafts.",
    )


def require_marketplace_publish_access(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    if not ent.features["allow_marketplace_publishing"]:
        raise HTTPException(status_code=403, detail="Current plan does not include marketplace publishing")
    _assert_limit(
        ent.limits["max_published_workers"],
        ent.usage["published_workers"],
        error_message="Published worker limit reached for current plan.",
    )


def require_published_worker_capacity(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    _assert_limit(
        ent.limits["max_published_workers"],
        ent.usage["published_workers"],
        error_message="Published worker limit reached for current plan.",
    )


def require_worker_install_access(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    if not ent.features["allow_marketplace_install"]:
        raise HTTPException(status_code=403, detail="Current plan does not allow worker installs")
    _assert_limit(
        ent.limits["max_worker_installs_per_workspace"],
        ent.usage["worker_installs"],
        error_message="Install limit reached for current plan.",
    )


def require_worker_run_access(db: Session, *, workspace_id: uuid.UUID) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    _assert_limit(
        ent.limits["max_worker_runs_per_month"],
        ent.usage["worker_runs_month"],
        error_message="Monthly worker run limit reached for current plan.",
    )


def require_template_visibility_access(db: Session, *, workspace_id: uuid.UUID, visibility: str) -> None:
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    normalized = (visibility or "").strip().lower()
    if normalized == "private" and not ent.features["allow_private_workers"]:
        raise HTTPException(status_code=403, detail="Current plan does not support private workers")
    if normalized in {"public", "marketplace"} and not ent.features["allow_public_workers"]:
        raise HTTPException(status_code=403, detail="Current plan does not support public worker publishing")


def require_paid_worker_entitlement(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    worker_template: WorkerTemplate,
) -> WorkerSubscription | None:
    if worker_template.pricing_type in {"free", "internal"} or int(worker_template.price_cents or 0) <= 0:
        return None
    entitlement = _first_active_worker_subscription(
        db,
        workspace_id=workspace_id,
        worker_template_id=worker_template.id,
    )
    if not entitlement:
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Paid worker requires purchase before install.",
                "purchase_required": True,
                "worker_template_id": str(worker_template.id),
            },
        )
    return entitlement


def _resolve_return_url(path: str) -> str:
    base = settings.app_base_url.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base}{path if path.startswith('/') else f'/{path}'}"


def _resolve_plan_stripe_price_id(plan: SubscriptionPlan, interval: str) -> str:
    if interval == BillingInterval.MONTHLY.value:
        price_id = (plan.stripe_price_id_monthly or "").strip()
        if plan.code == "pro":
            price_id = price_id or settings.stripe_price_id_pro_monthly
        elif plan.code == "creator":
            price_id = price_id or settings.stripe_price_id_creator_monthly
        elif plan.code == "enterprise":
            price_id = price_id or settings.stripe_price_id_enterprise_monthly
    else:
        price_id = (plan.stripe_price_id_annual or "").strip()
        if plan.code == "pro":
            price_id = price_id or settings.stripe_price_id_pro_annual
        elif plan.code == "creator":
            price_id = price_id or settings.stripe_price_id_creator_annual
    if not price_id:
        raise HTTPException(status_code=400, detail=f"No Stripe price ID configured for {plan.code} {interval}")
    return price_id


def ensure_workspace_customer_id(
    db: Session,
    *,
    workspace: Workspace,
    workspace_subscription: WorkspaceSubscription,
    gateway: StripeGateway | None = None,
) -> str:
    if workspace_subscription.stripe_customer_id:
        return workspace_subscription.stripe_customer_id
    stripe_gateway = gateway or get_stripe_gateway()
    customer = stripe_gateway.create_customer(
        name=workspace.company_name,
        metadata={"workspace_id": str(workspace.id)},
    )
    customer_id = str(customer.get("id", "")).strip()
    if not customer_id:
        raise HTTPException(status_code=502, detail="Stripe customer creation failed")
    workspace_subscription.stripe_customer_id = customer_id
    db.flush()
    return customer_id


def create_subscription_checkout_session(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    plan_code: str,
    billing_interval: str,
    gateway: StripeGateway | None = None,
) -> CheckoutSessionResult:
    interval = (billing_interval or "").strip().lower()
    if interval not in {BillingInterval.MONTHLY.value, BillingInterval.ANNUAL.value}:
        raise HTTPException(status_code=400, detail="billing_interval must be monthly or annual")
    ensure_default_subscription_plans(db)
    plan = get_plan_by_code(db, plan_code, include_inactive=False)
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    if plan.code == "free":
        raise HTTPException(status_code=400, detail="Free plan does not require checkout")
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace_subscription = ensure_workspace_subscription(db, workspace=workspace)
    stripe_gateway = gateway or get_stripe_gateway()
    customer_id = ensure_workspace_customer_id(
        db,
        workspace=workspace,
        workspace_subscription=workspace_subscription,
        gateway=stripe_gateway,
    )
    price_id = _resolve_plan_stripe_price_id(plan, interval)
    success_url = _resolve_return_url("/app/settings/billing?checkout=success")
    cancel_url = _resolve_return_url("/app/settings/billing?checkout=cancel")
    session = stripe_gateway.create_checkout_session(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "checkout_kind": "workspace_subscription",
            "workspace_id": str(workspace_id),
            "plan_code": plan.code,
            "billing_interval": interval,
        },
    )
    session_id = str(session.get("id", "")).strip()
    checkout_url = str(session.get("url", "")).strip()
    if not session_id or not checkout_url:
        raise HTTPException(status_code=502, detail="Stripe checkout session creation failed")
    workspace_subscription.stripe_checkout_session_id = session_id
    workspace_subscription.plan_id = plan.id
    workspace_subscription.billing_interval = interval
    db.flush()
    return CheckoutSessionResult(session_id=session_id, checkout_url=checkout_url, mode="subscription")


def create_worker_checkout_session(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    purchaser_user_id: uuid.UUID | None,
    worker_template: WorkerTemplate,
    gateway: StripeGateway | None = None,
) -> CheckoutSessionResult:
    if worker_template.pricing_type in {"free", "internal"} or int(worker_template.price_cents or 0) <= 0:
        raise HTTPException(status_code=400, detail="Worker does not require payment")
    require_worker_install_access(db, workspace_id=workspace_id)
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    plan, workspace_subscription = resolve_workspace_plan(db, workspace_id=workspace_id)
    if not plan.allow_marketplace_install:
        raise HTTPException(status_code=403, detail="Current plan does not allow marketplace purchases")
    workspace_subscription = workspace_subscription or ensure_workspace_subscription(db, workspace=workspace)
    stripe_gateway = gateway or get_stripe_gateway()
    customer_id = ensure_workspace_customer_id(
        db,
        workspace=workspace,
        workspace_subscription=workspace_subscription,
        gateway=stripe_gateway,
    )
    mode = "payment" if worker_template.pricing_type == WorkerAccessType.ONE_TIME.value else "subscription"
    metadata = {
        "checkout_kind": "worker_purchase",
        "workspace_id": str(workspace_id),
        "worker_template_id": str(worker_template.id),
        "purchaser_user_id": str(purchaser_user_id) if purchaser_user_id else "",
        "purchase_type": "one_time" if mode == "payment" else "subscription",
    }
    line_item: dict[str, Any]
    if mode == "payment":
        line_item = {
            "price_data": {
                "currency": (worker_template.currency or "USD").lower(),
                "unit_amount": int(worker_template.price_cents),
                "product_data": {
                    "name": worker_template.display_name or worker_template.name,
                    "metadata": {"worker_template_id": str(worker_template.id)},
                },
            },
            "quantity": 1,
        }
    else:
        line_item = {
            "price_data": {
                "currency": (worker_template.currency or "USD").lower(),
                "unit_amount": int(worker_template.price_cents),
                "recurring": {"interval": "month", "interval_count": 1},
                "product_data": {
                    "name": worker_template.display_name or worker_template.name,
                    "metadata": {"worker_template_id": str(worker_template.id)},
                },
            },
            "quantity": 1,
        }
    success_url = _resolve_return_url("/app/marketplace?purchase=success")
    cancel_url = _resolve_return_url("/app/marketplace?purchase=cancel")
    session = stripe_gateway.create_checkout_session(
        mode=mode,
        customer=customer_id,
        line_items=[line_item],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    session_id = str(session.get("id", "")).strip()
    checkout_url = str(session.get("url", "")).strip()
    if not session_id or not checkout_url:
        raise HTTPException(status_code=502, detail="Stripe worker checkout session creation failed")
    return CheckoutSessionResult(session_id=session_id, checkout_url=checkout_url, mode=mode)


def create_billing_portal_session(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    gateway: StripeGateway | None = None,
) -> str:
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace_subscription = ensure_workspace_subscription(db, workspace=workspace)
    stripe_gateway = gateway or get_stripe_gateway()
    customer_id = ensure_workspace_customer_id(
        db,
        workspace=workspace,
        workspace_subscription=workspace_subscription,
        gateway=stripe_gateway,
    )
    return_url = settings.stripe_billing_portal_return_url or _resolve_return_url("/app/settings/billing")
    session = stripe_gateway.create_billing_portal_session(customer=customer_id, return_url=return_url)
    portal_url = str(session.get("url", "")).strip()
    if not portal_url:
        raise HTTPException(status_code=502, detail="Stripe billing portal session creation failed")
    return portal_url


def _upsert_workspace_subscription_from_checkout(
    db: Session,
    *,
    session_payload: dict[str, Any],
) -> None:
    metadata = session_payload.get("metadata", {}) if isinstance(session_payload.get("metadata"), dict) else {}
    workspace_id_raw = str(metadata.get("workspace_id", "")).strip()
    if not workspace_id_raw:
        return
    try:
        workspace_id = uuid.UUID(workspace_id_raw)
    except ValueError:
        return
    workspace = db.get(Workspace, workspace_id)
    if not workspace:
        return
    subscription = ensure_workspace_subscription(db, workspace=workspace)
    if session_payload.get("customer"):
        subscription.stripe_customer_id = str(session_payload.get("customer"))
    if session_payload.get("subscription"):
        subscription.stripe_subscription_id = str(session_payload.get("subscription"))
    if session_payload.get("id"):
        subscription.stripe_checkout_session_id = str(session_payload.get("id"))
    plan_code = str(metadata.get("plan_code", "")).strip().lower()
    plan = get_plan_by_code(db, plan_code, include_inactive=True) if plan_code else None
    if plan:
        subscription.plan_id = plan.id
        workspace.subscription_plan = plan.code
    interval = str(metadata.get("billing_interval", "")).strip().lower()
    if interval in {BillingInterval.MONTHLY.value, BillingInterval.ANNUAL.value}:
        subscription.billing_interval = interval
    subscription.status = WorkspaceSubscriptionStatus.ACTIVE.value
    subscription.subscribed_at = _utc_now()
    subscription.canceled_at = None
    subscription.cancel_at_period_end = False
    db.flush()


def _upsert_worker_entitlement_from_checkout(db: Session, *, session_payload: dict[str, Any]) -> WorkerSubscription | None:
    metadata = session_payload.get("metadata", {}) if isinstance(session_payload.get("metadata"), dict) else {}
    workspace_id_raw = str(metadata.get("workspace_id", "")).strip()
    template_id_raw = str(metadata.get("worker_template_id", "")).strip()
    if not workspace_id_raw or not template_id_raw:
        return None
    try:
        workspace_id = uuid.UUID(workspace_id_raw)
        template_id = uuid.UUID(template_id_raw)
    except ValueError:
        return None
    template = db.get(WorkerTemplate, template_id)
    if not template:
        return None
    purchaser_user_id: uuid.UUID | None = None
    purchaser_user_raw = str(metadata.get("purchaser_user_id", "")).strip()
    if purchaser_user_raw:
        try:
            purchaser_user_id = uuid.UUID(purchaser_user_raw)
        except ValueError:
            purchaser_user_id = None
    purchase_type = str(metadata.get("purchase_type", "")).strip().lower()
    access_type = WorkerAccessType.ONE_TIME.value if purchase_type == WorkerAccessType.ONE_TIME.value else WorkerAccessType.SUBSCRIPTION.value
    entitlement = (
        db.query(WorkerSubscription)
        .filter(
            WorkerSubscription.workspace_id == workspace_id,
            WorkerSubscription.worker_template_id == template_id,
            WorkerSubscription.status.in_(tuple(ACTIVE_WORKER_ENTITLEMENT_STATES)),
        )
        .order_by(WorkerSubscription.created_at.desc())
        .first()
    )
    if not entitlement:
        entitlement = WorkerSubscription(
            workspace_id=workspace_id,
            worker_template_id=template_id,
            purchaser_user_id=purchaser_user_id,
            price_cents=int(template.price_cents or 0),
            currency=template.currency or "USD",
        )
        db.add(entitlement)
    entitlement.access_type = access_type
    entitlement.status = WorkerEntitlementStatus.ACTIVE.value
    entitlement.is_active = True
    entitlement.billing_status = "active"
    entitlement.purchaser_user_id = purchaser_user_id or entitlement.purchaser_user_id
    entitlement.stripe_checkout_session_id = str(session_payload.get("id") or "") or entitlement.stripe_checkout_session_id
    entitlement.stripe_payment_intent_id = str(session_payload.get("payment_intent") or "") or entitlement.stripe_payment_intent_id
    entitlement.stripe_subscription_id = str(session_payload.get("subscription") or "") or entitlement.stripe_subscription_id
    entitlement.granted_at = _utc_now()
    entitlement.expires_at = None
    entitlement.ends_at = None
    db.flush()
    return entitlement


def _sync_workspace_subscription_from_stripe(
    db: Session,
    *,
    stripe_subscription: dict[str, Any],
) -> None:
    stripe_subscription_id = str(stripe_subscription.get("id", "")).strip()
    customer_id = str(stripe_subscription.get("customer", "")).strip()
    if not stripe_subscription_id and not customer_id:
        return
    query = db.query(WorkspaceSubscription)
    if stripe_subscription_id:
        query = query.filter(WorkspaceSubscription.stripe_subscription_id == stripe_subscription_id)
    elif customer_id:
        query = query.filter(WorkspaceSubscription.stripe_customer_id == customer_id)
    record = query.order_by(WorkspaceSubscription.updated_at.desc()).first()
    if not record:
        return
    status = str(stripe_subscription.get("status", "")).strip() or WorkspaceSubscriptionStatus.ACTIVE.value
    record.status = status
    record.stripe_customer_id = customer_id or record.stripe_customer_id
    record.stripe_subscription_id = stripe_subscription_id or record.stripe_subscription_id
    current_period_start = _from_unix(stripe_subscription.get("current_period_start"))
    current_period_end = _from_unix(stripe_subscription.get("current_period_end"))
    if current_period_start:
        record.current_period_start = current_period_start
    if current_period_end:
        record.current_period_end = current_period_end
    record.cancel_at_period_end = bool(stripe_subscription.get("cancel_at_period_end", False))
    trial_end = _from_unix(stripe_subscription.get("trial_end"))
    if trial_end:
        record.trial_ends_at = trial_end
    if status in {WorkspaceSubscriptionStatus.CANCELED.value, WorkspaceSubscriptionStatus.UNPAID.value}:
        record.canceled_at = _utc_now()
    db.flush()


def _sync_worker_entitlement_subscription_state(
    db: Session,
    *,
    stripe_subscription: dict[str, Any],
) -> None:
    stripe_subscription_id = str(stripe_subscription.get("id", "")).strip()
    if not stripe_subscription_id:
        return
    records = (
        db.query(WorkerSubscription)
        .filter(WorkerSubscription.stripe_subscription_id == stripe_subscription_id)
        .all()
    )
    if not records:
        return
    status = str(stripe_subscription.get("status", "")).strip().lower()
    entitlement_status = WorkerEntitlementStatus.ACTIVE.value
    is_active = True
    if status in {"canceled", "unpaid"}:
        entitlement_status = WorkerEntitlementStatus.CANCELED.value
        is_active = False
    elif status in {"incomplete", "past_due", "incomplete_expired"}:
        entitlement_status = WorkerEntitlementStatus.PENDING.value
        is_active = True
    for record in records:
        record.status = entitlement_status
        record.is_active = is_active
        record.billing_status = status or record.billing_status
        if not is_active:
            record.expires_at = _utc_now()
            record.ends_at = record.expires_at
    db.flush()


def _sync_invoice_state(db: Session, *, invoice: dict[str, Any], paid: bool) -> None:
    subscription_id = str(invoice.get("subscription", "")).strip()
    customer_id = str(invoice.get("customer", "")).strip()
    if subscription_id:
        workspace_records = db.query(WorkspaceSubscription).filter(
            WorkspaceSubscription.stripe_subscription_id == subscription_id
        )
    else:
        workspace_records = db.query(WorkspaceSubscription).filter(
            WorkspaceSubscription.stripe_customer_id == customer_id
        )
    for record in workspace_records.all():
        record.status = WorkspaceSubscriptionStatus.ACTIVE.value if paid else WorkspaceSubscriptionStatus.PAST_DUE.value
    worker_records_query = db.query(WorkerSubscription)
    if subscription_id:
        worker_records_query = worker_records_query.filter(WorkerSubscription.stripe_subscription_id == subscription_id)
    else:
        worker_records_query = worker_records_query.filter(WorkerSubscription.stripe_checkout_session_id == str(invoice.get("checkout_session", "")))
    for entitlement in worker_records_query.all():
        entitlement.status = WorkerEntitlementStatus.ACTIVE.value if paid else WorkerEntitlementStatus.PENDING.value
        entitlement.is_active = True if paid else entitlement.is_active
        entitlement.billing_status = "active" if paid else "past_due"
    db.flush()


def process_stripe_webhook(
    db: Session,
    *,
    payload: bytes,
    signature: str,
    gateway: StripeGateway | None = None,
) -> BillingEventLog:
    stripe_gateway = gateway or get_stripe_gateway()
    event = stripe_gateway.verify_webhook_event(payload, signature)
    event_id = str(event.get("id", "")).strip()
    event_type = str(event.get("type", "")).strip()
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload")

    existing = db.query(BillingEventLog).filter(BillingEventLog.stripe_event_id == event_id).first()
    if existing:
        return existing

    log = BillingEventLog(
        stripe_event_id=event_id,
        event_type=event_type,
        payload_json=event if isinstance(event, dict) else {"raw": event},
        status=BillingEventStatus.RECEIVED.value,
    )
    db.add(log)
    db.flush()

    try:
        event_data_object = event.get("data", {}).get("object", {}) if isinstance(event, dict) else {}
        if event_type == "checkout.session.completed":
            metadata = event_data_object.get("metadata", {}) if isinstance(event_data_object, dict) else {}
            checkout_kind = str(metadata.get("checkout_kind", "")).strip()
            if checkout_kind == "workspace_subscription":
                _upsert_workspace_subscription_from_checkout(db, session_payload=event_data_object)
            elif checkout_kind == "worker_purchase":
                _upsert_worker_entitlement_from_checkout(db, session_payload=event_data_object)
        elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            _sync_workspace_subscription_from_stripe(db, stripe_subscription=event_data_object)
            _sync_worker_entitlement_subscription_state(db, stripe_subscription=event_data_object)
        elif event_type == "invoice.paid":
            _sync_invoice_state(db, invoice=event_data_object, paid=True)
        elif event_type == "invoice.payment_failed":
            _sync_invoice_state(db, invoice=event_data_object, paid=False)
        elif event_type == "payment_intent.succeeded":
            # checkout.session.completed already grants entitlement; payment_intent is retained for audit completeness.
            pass
        log.status = BillingEventStatus.PROCESSED.value
        log.error_message = None
        log.processed_at = _utc_now()
        db.flush()
        return log
    except Exception as exc:  # pragma: no cover - defensive error capture
        log.status = BillingEventStatus.FAILED.value
        log.error_message = str(exc)
        db.flush()
        raise


class BillingService:
    def process_marketplace_subscription(self, template: WorkerTemplate) -> BillingResult:
        raise NotImplementedError


class PlaceholderBillingService(BillingService):
    def process_marketplace_subscription(self, template: WorkerTemplate) -> BillingResult:
        if template.pricing_type in {"free", "internal"} or template.price_cents <= 0:
            return BillingResult(billing_status="active", is_captured=True, message="No payment required for this template.")
        return BillingResult(
            billing_status="pending_payment",
            is_captured=False,
            message="Payment required. Complete checkout to activate entitlement.",
        )


def get_billing_service() -> BillingService:
    return PlaceholderBillingService()
