import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, WorkerTemplate
from app.schemas.api import (
    CreatorRevenueSummaryRead,
    MarketplaceInstallResponse,
    MarketplaceListingRead,
    MarketplaceWorkerDetailRead,
    WorkerReviewCatalogRead,
    WorkerReviewCreate,
    WorkerTemplatePublishRequest,
    WorkerTemplateInstallRequest,
)
from app.services.audit import log_audit_event
from app.services.billing import (
    ensure_creator_monetization_profile,
    require_marketplace_publish_access,
    require_paid_worker_entitlement,
    require_published_worker_capacity,
    require_worker_install_access,
)
from app.services.marketplace import (
    create_or_update_review,
    get_creator_revenue_summary,
    get_marketplace_worker_detail,
    install_marketplace_worker,
    list_marketplace_workers,
    list_reviews,
    publish_template_to_marketplace,
)
from app.services.worker_templates import get_worker_template_details

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/templates", response_model=list[MarketplaceListingRead])
def list_marketplace_templates(
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated tags"),
    pricing_type: str | None = Query(default=None),
    min_price_cents: int | None = Query(default=None, ge=0),
    max_price_cents: int | None = Query(default=None, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listings = list_marketplace_workers(
        db,
        workspace_id=current_user.workspace_id,
        category=category,
        tags=[item.strip() for item in f"{tag or ''},{tags or ''}".split(",") if item.strip()],
        pricing_type=pricing_type,
        min_price_cents=min_price_cents,
        max_price_cents=max_price_cents,
    )
    return [MarketplaceListingRead(**item) for item in listings]


@router.get("/templates/{template_id}", response_model=MarketplaceWorkerDetailRead)
def get_marketplace_template_by_id(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = get_marketplace_worker_detail(
        db,
        workspace_id=current_user.workspace_id,
        template_id=template_id,
    )
    return MarketplaceWorkerDetailRead(
        template=detail.template,
        is_installed=detail.is_installed,
        has_active_entitlement=detail.has_active_entitlement,
        purchase_required=detail.purchase_required,
        subscription=detail.subscription,
        reviews=detail.reviews,
        tools=detail.tools,
        average_rating=detail.template.rating_avg,
        installs=detail.template.install_count,
    )


@router.get("/templates/slug/{slug}", response_model=MarketplaceWorkerDetailRead)
def get_marketplace_template_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = get_marketplace_worker_detail(
        db,
        workspace_id=current_user.workspace_id,
        slug=slug,
    )
    return MarketplaceWorkerDetailRead(
        template=detail.template,
        is_installed=detail.is_installed,
        has_active_entitlement=detail.has_active_entitlement,
        purchase_required=detail.purchase_required,
        subscription=detail.subscription,
        reviews=detail.reviews,
        tools=detail.tools,
        average_rating=detail.template.rating_avg,
        installs=detail.template.install_count,
    )


@router.post("/templates/{template_id}/publish", response_model=MarketplaceWorkerDetailRead)
def publish_to_marketplace(
    template_id: uuid.UUID,
    payload: WorkerTemplatePublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.get(WorkerTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    require_marketplace_publish_access(db, workspace_id=current_user.workspace_id)
    require_published_worker_capacity(db, workspace_id=current_user.workspace_id)
    ensure_creator_monetization_profile(db, user_id=current_user.id)
    published = publish_template_to_marketplace(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        payload=payload,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_template_published_to_marketplace",
        payload={"template_id": str(template_id)},
    )
    db.commit()
    detail = get_marketplace_worker_detail(
        db,
        workspace_id=current_user.workspace_id,
        template_id=published.id,
    )
    return MarketplaceWorkerDetailRead(
        template=detail.template,
        is_installed=detail.is_installed,
        has_active_entitlement=detail.has_active_entitlement,
        purchase_required=detail.purchase_required,
        subscription=detail.subscription,
        reviews=detail.reviews,
        tools=detail.tools,
        average_rating=detail.template.rating_avg,
        installs=detail.template.install_count,
    )


@router.post("/templates/{template_id}/install", response_model=MarketplaceInstallResponse)
def install_marketplace_template(
    template_id: uuid.UUID,
    payload: WorkerTemplateInstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = get_worker_template_details(
        db,
        template_id=template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    require_worker_install_access(db, workspace_id=current_user.workspace_id)
    require_paid_worker_entitlement(
        db,
        workspace_id=current_user.workspace_id,
        worker_template=template,
    )
    install_result, billing_result, revenue_event = install_marketplace_worker(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        installer_user_id=current_user.id,
        instance_name=payload.instance_name,
        runtime_config_overrides=payload.runtime_config_overrides,
        schedule_expression=payload.schedule_expression,
        memory_scope=payload.memory_scope,
    )
    if install_result.subscription is None:
        raise HTTPException(status_code=400, detail="Marketplace subscription could not be created")
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="marketplace_template_installed",
        payload={
            "template_id": str(template.id),
            "instance_id": str(install_result.instance.id),
            "billing_status": billing_result.billing_status,
            "revenue_event_id": str(revenue_event.id),
        },
    )
    db.commit()
    db.refresh(install_result.subscription)
    return MarketplaceInstallResponse(
        success=True,
        worker_template_id=template.id,
        subscription=install_result.subscription,
        message=billing_result.message or "Template installed successfully",
    )


@router.post("/templates/{template_id}/reviews", response_model=WorkerReviewCatalogRead)
def create_review(
    template_id: uuid.UUID,
    payload: WorkerReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = get_marketplace_worker_detail(
        db,
        workspace_id=current_user.workspace_id,
        template_id=template_id,
    )
    review = create_or_update_review(
        db,
        template=detail.template,
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        payload=payload,
    )
    db.commit()
    db.refresh(review)
    return review


@router.get("/templates/{template_id}/reviews", response_model=list[WorkerReviewCatalogRead])
def get_reviews(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    detail = get_marketplace_worker_detail(
        db,
        workspace_id=current_user.workspace_id,
        template_id=template_id,
    )
    return list_reviews(db, template_id=detail.template.id)


@router.get("/creator/revenue", response_model=CreatorRevenueSummaryRead)
def creator_revenue_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    summary = get_creator_revenue_summary(db, creator_user_id=current_user.id)
    return CreatorRevenueSummaryRead(
        total_gross_cents=summary.total_gross_cents,
        total_platform_fee_cents=summary.total_platform_fee_cents,
        total_creator_payout_cents=summary.total_creator_payout_cents,
        recent_events=summary.recent_events,
    )
