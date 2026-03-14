import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import SubscriptionPlan, User
from app.schemas.api import (
    BillingCheckoutSessionResponse,
    BillingCheckoutSubscriptionRequest,
    BillingEntitlementsRead,
    BillingPlanRead,
    BillingPortalResponse,
    BillingSubscriptionRead,
    BillingWebhookResponse,
    BillingWorkerCheckoutRequest,
)
from app.services.audit import log_audit_event
from app.services.billing import (
    create_billing_portal_session,
    create_subscription_checkout_session,
    create_worker_checkout_session,
    get_workspace_entitlements,
    process_stripe_webhook,
    resolve_workspace_plan,
)
from app.services.subscription_plans import ensure_default_subscription_plans
from app.services.worker_templates import get_worker_template_details

router = APIRouter(prefix="/billing", tags=["billing"])


def _build_subscription_read(plan, subscription) -> BillingSubscriptionRead:
    if subscription is None:
        raise HTTPException(status_code=404, detail="Workspace subscription not found")
    return BillingSubscriptionRead(
        id=subscription.id,
        workspace_id=subscription.workspace_id,
        plan_id=subscription.plan_id,
        plan_code=plan.code,
        plan_name=plan.name,
        status=subscription.status,
        billing_interval=subscription.billing_interval,
        stripe_customer_id=subscription.stripe_customer_id,
        stripe_subscription_id=subscription.stripe_subscription_id,
        stripe_checkout_session_id=subscription.stripe_checkout_session_id,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        subscribed_at=subscription.subscribed_at,
        canceled_at=subscription.canceled_at,
        trial_ends_at=subscription.trial_ends_at,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


@router.get("/plans", response_model=list[BillingPlanRead])
def list_billing_plans(db: Session = Depends(get_db)):
    ensure_default_subscription_plans(db)
    plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.monthly_price_cents.asc(), SubscriptionPlan.name.asc())
        .all()
    )
    return plans


@router.get("/subscription", response_model=BillingSubscriptionRead)
def get_subscription(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan, subscription = resolve_workspace_plan(db, workspace_id=current_user.workspace_id)
    return _build_subscription_read(plan, subscription)


@router.post("/checkout/subscription", response_model=BillingCheckoutSessionResponse)
def checkout_subscription(
    payload: BillingCheckoutSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_result = create_subscription_checkout_session(
        db,
        workspace_id=current_user.workspace_id,
        plan_code=payload.plan_code,
        billing_interval=payload.billing_interval.value if hasattr(payload.billing_interval, "value") else str(payload.billing_interval),
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="billing_subscription_checkout_created",
        payload={"session_id": session_result.session_id, "plan_code": payload.plan_code},
    )
    db.commit()
    return BillingCheckoutSessionResponse(
        session_id=session_result.session_id,
        checkout_url=session_result.checkout_url,
        mode=session_result.mode,
    )


@router.post("/portal", response_model=BillingPortalResponse)
def create_portal(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    portal_url = create_billing_portal_session(
        db,
        workspace_id=current_user.workspace_id,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="billing_portal_session_created",
        payload={"portal_url": portal_url},
    )
    db.commit()
    return BillingPortalResponse(portal_url=portal_url)


@router.post("/checkout/worker/{worker_template_id}", response_model=BillingCheckoutSessionResponse)
def checkout_worker_template(
    worker_template_id: uuid.UUID,
    payload: BillingWorkerCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = payload
    template = get_worker_template_details(
        db,
        template_id=worker_template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    session_result = create_worker_checkout_session(
        db,
        workspace_id=current_user.workspace_id,
        purchaser_user_id=current_user.id,
        worker_template=template,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="billing_worker_checkout_created",
        payload={"session_id": session_result.session_id, "worker_template_id": str(worker_template_id)},
    )
    db.commit()
    return BillingCheckoutSessionResponse(
        session_id=session_result.session_id,
        checkout_url=session_result.checkout_url,
        mode=session_result.mode,
    )


@router.get("/entitlements", response_model=BillingEntitlementsRead)
def get_entitlements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entitlements = get_workspace_entitlements(db, workspace_id=current_user.workspace_id)
    subscription = (
        _build_subscription_read(entitlements.plan, entitlements.workspace_subscription)
        if entitlements.workspace_subscription
        else None
    )
    return BillingEntitlementsRead(
        plan=entitlements.plan,
        subscription=subscription,
        features=entitlements.features,
        limits=entitlements.limits,
        usage=entitlements.usage,
    )


@router.post("/webhooks/stripe", response_model=BillingWebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    payload = await request.body()
    event_log = process_stripe_webhook(db, payload=payload, signature=stripe_signature)
    db.commit()
    return BillingWebhookResponse(
        received=True,
        event_id=event_log.stripe_event_id,
        status=event_log.status,
    )
