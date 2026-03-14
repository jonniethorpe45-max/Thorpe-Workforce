import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    WorkerReview,
    WorkerSubscription,
    WorkerTemplate,
    WorkerTemplateStatus,
    WorkerTemplateTool,
    WorkerTemplateVisibility,
    WorkerTool,
    WorkerRevenueEvent,
)
from app.schemas.api import WorkerReviewCreate, WorkerTemplatePublishRequest
from app.services.billing import BillingResult, get_billing_service
from app.services.worker_templates import (
    TemplateInstallResult,
    get_worker_template_details,
    install_worker_template,
    list_worker_templates,
    publish_worker_template,
)


@dataclass(frozen=True)
class MarketplaceTemplateDetail:
    template: WorkerTemplate
    is_installed: bool
    subscription: WorkerSubscription | None
    reviews: list[WorkerReview]
    tools: list[WorkerTool]


@dataclass(frozen=True)
class CreatorRevenueSummary:
    total_gross_cents: int
    total_platform_fee_cents: int
    total_creator_payout_cents: int
    recent_events: list[WorkerRevenueEvent]


def _is_marketplace_visible(template: WorkerTemplate) -> bool:
    if not template.is_active or template.status != WorkerTemplateStatus.ACTIVE.value:
        return False
    if not template.is_public and template.visibility not in {
        WorkerTemplateVisibility.PUBLIC.value,
        WorkerTemplateVisibility.MARKETPLACE.value,
    }:
        return False
    return template.is_marketplace_listed or template.visibility == WorkerTemplateVisibility.MARKETPLACE.value


def _assert_marketplace_template(template: WorkerTemplate) -> None:
    if not _is_marketplace_visible(template):
        raise HTTPException(status_code=404, detail="Marketplace template not found")


def _resolve_template_tools(db: Session, template_id: uuid.UUID, configured_tool_slugs: list[str] | None) -> list[WorkerTool]:
    configured = [str(item).strip() for item in (configured_tool_slugs or []) if str(item).strip()]
    linked = [
        row[0]
        for row in db.query(WorkerTool.slug)
        .join(WorkerTemplateTool, WorkerTemplateTool.worker_tool_id == WorkerTool.id)
        .filter(WorkerTemplateTool.worker_template_id == template_id, WorkerTool.is_active.is_(True))
        .all()
    ]
    slugs = sorted(set(configured + linked))
    if not slugs:
        return []
    return db.query(WorkerTool).filter(WorkerTool.slug.in_(slugs), WorkerTool.is_active.is_(True)).all()


def calculate_platform_fee_cents(gross_cents: int, fee_percent: float | None = None) -> tuple[int, int]:
    gross = max(int(gross_cents), 0)
    percent = settings.marketplace_platform_fee_percent if fee_percent is None else fee_percent
    bounded = max(0.0, min(1.0, float(percent)))
    platform_fee = int(round(gross * bounded))
    creator_payout = max(gross - platform_fee, 0)
    return platform_fee, creator_payout


def list_marketplace_workers(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    category: str | None = None,
    tags: list[str] | None = None,
    pricing_type: str | None = None,
    min_price_cents: int | None = None,
    max_price_cents: int | None = None,
) -> list[dict[str, Any]]:
    templates = list_worker_templates(
        db,
        workspace_id=workspace_id,
        include_workspace_templates=False,
        include_public_templates=True,
        include_global_non_public_templates=False,
        marketplace_only=True,
    )
    category_filter = (category or "").strip().lower()
    tag_filters = {(item or "").strip().lower() for item in (tags or []) if (item or "").strip()}
    pricing_filter = (pricing_type or "").strip().lower()
    items: list[WorkerTemplate] = []
    for template in templates:
        if category_filter and (template.category or "").lower() != category_filter:
            continue
        if pricing_filter and (template.pricing_type or "").lower() != pricing_filter:
            continue
        if min_price_cents is not None and int(template.price_cents or 0) < int(min_price_cents):
            continue
        if max_price_cents is not None and int(template.price_cents or 0) > int(max_price_cents):
            continue
        if tag_filters:
            tags = {(item or "").lower() for item in (template.tags_json or [])}
            if not (tags & tag_filters):
                continue
        items.append(template)

    template_ids = [item.id for item in items]
    installed_template_ids = {
        row[0]
        for row in db.query(WorkerSubscription.worker_template_id)
        .filter(
            WorkerSubscription.workspace_id == workspace_id,
            WorkerSubscription.is_active.is_(True),
            WorkerSubscription.worker_template_id.in_(template_ids) if template_ids else False,
        )
        .all()
    }
    subscriptions = (
        db.query(WorkerSubscription)
        .filter(
            WorkerSubscription.workspace_id == workspace_id,
            WorkerSubscription.worker_template_id.in_(template_ids) if template_ids else False,
            WorkerSubscription.is_active.is_(True),
        )
        .all()
    )
    subscription_by_template = {item.worker_template_id: item for item in subscriptions}
    return [
        {
            "template": template,
            "is_installed": template.id in installed_template_ids,
            "subscription": subscription_by_template.get(template.id),
        }
        for template in items
    ]


def get_marketplace_worker_detail(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    template_id: uuid.UUID | None = None,
    slug: str | None = None,
) -> MarketplaceTemplateDetail:
    template = get_worker_template_details(
        db,
        template_id=template_id,
        slug=slug,
        workspace_id=workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    _assert_marketplace_template(template)
    subscription = (
        db.query(WorkerSubscription)
        .filter(
            WorkerSubscription.workspace_id == workspace_id,
            WorkerSubscription.worker_template_id == template.id,
            WorkerSubscription.is_active.is_(True),
        )
        .order_by(WorkerSubscription.started_at.desc())
        .first()
    )
    reviews = (
        db.query(WorkerReview)
        .filter(WorkerReview.worker_template_id == template.id)
        .order_by(WorkerReview.created_at.desc())
        .limit(50)
        .all()
    )
    tools = _resolve_template_tools(db, template.id, template.tools_json)
    return MarketplaceTemplateDetail(
        template=template,
        is_installed=subscription is not None,
        subscription=subscription,
        reviews=reviews,
        tools=tools,
    )


def publish_template_to_marketplace(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    payload: WorkerTemplatePublishRequest,
) -> WorkerTemplate:
    publish_payload = payload.model_copy(
        update={"visibility": WorkerTemplateVisibility.MARKETPLACE, "is_marketplace_listed": True}
    )
    published = publish_worker_template(db, template=template, workspace_id=workspace_id, payload=publish_payload)
    return published


def _upsert_subscription_from_billing(
    db: Session,
    *,
    install_result: TemplateInstallResult,
    billing_result: BillingResult,
    installer_user_id: uuid.UUID | None,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
) -> WorkerSubscription:
    subscription = install_result.subscription
    if not subscription:
        subscription = WorkerSubscription(
            workspace_id=workspace_id,
            worker_template_id=template.id,
            purchaser_user_id=installer_user_id,
            billing_status=billing_result.billing_status,
            price_cents=template.price_cents,
            currency=template.currency,
            is_active=True,
        )
        db.add(subscription)
    subscription.billing_status = billing_result.billing_status
    subscription.price_cents = template.price_cents
    subscription.currency = template.currency
    if not billing_result.is_captured and template.price_cents > 0:
        subscription.is_active = True
    db.flush()
    return subscription


def create_revenue_event(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    gross_cents: int,
    revenue_type: str,
    reference_type: str | None,
    reference_id: str | None,
) -> WorkerRevenueEvent:
    platform_fee_cents, creator_payout_cents = calculate_platform_fee_cents(gross_cents)
    event = WorkerRevenueEvent(
        worker_template_id=template.id,
        creator_user_id=template.creator_user_id,
        workspace_id=workspace_id,
        revenue_type=revenue_type,
        gross_cents=max(int(gross_cents), 0),
        platform_fee_cents=platform_fee_cents,
        creator_payout_cents=creator_payout_cents,
        currency=template.currency or "USD",
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(event)
    db.flush()
    return event


def install_marketplace_worker(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    installer_user_id: uuid.UUID | None,
    instance_name: str | None,
    runtime_config_overrides: dict[str, Any] | None,
    schedule_expression: str | None,
    memory_scope: str,
) -> tuple[TemplateInstallResult, BillingResult, WorkerRevenueEvent]:
    _assert_marketplace_template(template)
    install_result = install_worker_template(
        db,
        template=template,
        workspace_id=workspace_id,
        installer_user_id=installer_user_id,
        instance_name=instance_name,
        runtime_config_overrides=runtime_config_overrides,
        schedule_expression=schedule_expression,
        memory_scope=memory_scope,
    )
    billing_result = get_billing_service().process_marketplace_subscription(template)
    subscription = _upsert_subscription_from_billing(
        db,
        install_result=install_result,
        billing_result=billing_result,
        installer_user_id=installer_user_id,
        template=template,
        workspace_id=workspace_id,
    )
    if template.price_cents <= 0:
        revenue_type = "free_install"
        gross = 0
    elif billing_result.is_captured:
        revenue_type = "purchase_captured"
        gross = template.price_cents
    else:
        revenue_type = "purchase_pending"
        gross = 0
    revenue_event = create_revenue_event(
        db,
        template=template,
        workspace_id=workspace_id,
        gross_cents=gross,
        revenue_type=revenue_type,
        reference_type="worker_subscription",
        reference_id=str(subscription.id),
    )
    return install_result, billing_result, revenue_event


def _recompute_template_rating(db: Session, template: WorkerTemplate) -> None:
    avg_value, count_value = (
        db.query(func.avg(WorkerReview.rating), func.count(WorkerReview.id))
        .filter(WorkerReview.worker_template_id == template.id)
        .one()
    )
    template.rating_avg = float(avg_value or 0.0)
    template.rating_count = int(count_value or 0)
    db.flush()


def create_or_update_review(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: WorkerReviewCreate,
) -> WorkerReview:
    _assert_marketplace_template(template)
    review = (
        db.query(WorkerReview)
        .filter(
            WorkerReview.worker_template_id == template.id,
            WorkerReview.user_id == user_id,
            WorkerReview.workspace_id == workspace_id,
        )
        .first()
    )
    if review:
        review.rating = payload.rating
        review.review_text = payload.review_text
    else:
        review = WorkerReview(
            worker_template_id=template.id,
            user_id=user_id,
            workspace_id=workspace_id,
            rating=payload.rating,
            review_text=payload.review_text,
        )
        db.add(review)
    db.flush()
    _recompute_template_rating(db, template)
    return review


def list_reviews(db: Session, *, template_id: uuid.UUID, limit: int = 50) -> list[WorkerReview]:
    return (
        db.query(WorkerReview)
        .filter(WorkerReview.worker_template_id == template_id)
        .order_by(WorkerReview.created_at.desc())
        .limit(max(limit, 1))
        .all()
    )


def get_creator_revenue_summary(db: Session, *, creator_user_id: uuid.UUID, limit: int = 25) -> CreatorRevenueSummary:
    gross, fees, payout = (
        db.query(
            func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.platform_fee_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
        )
        .filter(WorkerRevenueEvent.creator_user_id == creator_user_id)
        .one()
    )
    recent_events = (
        db.query(WorkerRevenueEvent)
        .filter(WorkerRevenueEvent.creator_user_id == creator_user_id)
        .order_by(WorkerRevenueEvent.created_at.desc())
        .limit(max(limit, 1))
        .all()
    )
    return CreatorRevenueSummary(
        total_gross_cents=int(gross or 0),
        total_platform_fee_cents=int(fees or 0),
        total_creator_payout_cents=int(payout or 0),
        recent_events=recent_events,
    )
