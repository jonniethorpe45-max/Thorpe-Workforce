import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin_access
from app.db.session import get_db
from app.models import User
from app.schemas.api import (
    AdminAnalyticsSummaryRead,
    AdminBillingSummaryRead,
    AdminCreatorListItemRead,
    AdminModerationRequest,
    AdminWorkerDetailRead,
    AdminWorkerListItemRead,
)
from app.services.audit import log_audit_event
from app.services.platform_analytics import (
    admin_billing_summary,
    admin_creators_list,
    admin_platform_summary,
    admin_worker_detail,
    admin_workers_list,
    moderate_worker,
)

router = APIRouter(prefix="/admin", tags=["admin_analytics"])


@router.get("/analytics/summary", response_model=AdminAnalyticsSummaryRead)
def admin_summary(current_user: User = Depends(require_platform_admin_access), db: Session = Depends(get_db)):
    _ = current_user
    return admin_platform_summary(db)


@router.get("/workers", response_model=list[AdminWorkerListItemRead])
def admin_workers(
    moderation_status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    pricing_model: str | None = Query(default=None),
    creator_user_id: uuid.UUID | None = Query(default=None),
    visibility: str | None = Query(default=None),
    flagged_only: bool = Query(default=False),
    current_user: User = Depends(require_platform_admin_access),
    db: Session = Depends(get_db),
):
    _ = current_user
    return admin_workers_list(
        db,
        moderation_status=moderation_status,
        category=category,
        pricing_type=pricing_model,
        creator_user_id=creator_user_id,
        visibility=visibility,
        flagged_only=flagged_only,
    )


@router.get("/workers/{worker_id}", response_model=AdminWorkerDetailRead)
def admin_worker(
    worker_id: uuid.UUID,
    current_user: User = Depends(require_platform_admin_access),
    db: Session = Depends(get_db),
):
    _ = current_user
    return admin_worker_detail(db, worker_template_id=worker_id)


@router.post("/workers/{worker_id}/moderate", response_model=AdminWorkerDetailRead)
def admin_moderate_worker(
    worker_id: uuid.UUID,
    payload: AdminModerationRequest,
    current_user: User = Depends(require_platform_admin_access),
    db: Session = Depends(get_db),
):
    template = moderate_worker(
        db,
        worker_template_id=worker_id,
        reviewer_user_id=current_user.id,
        action=payload.action,
        moderation_notes=payload.moderation_notes,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="admin_worker_moderation_updated",
        payload={"worker_template_id": str(worker_id), "action": payload.action, "status": template.moderation_status},
    )
    db.commit()
    return admin_worker_detail(db, worker_template_id=worker_id)


@router.get("/creators", response_model=list[AdminCreatorListItemRead])
def admin_creators(current_user: User = Depends(require_platform_admin_access), db: Session = Depends(get_db)):
    _ = current_user
    return admin_creators_list(db)


@router.get("/billing/summary", response_model=AdminBillingSummaryRead)
def admin_billing(current_user: User = Depends(require_platform_admin_access), db: Session = Depends(get_db)):
    _ = current_user
    return admin_billing_summary(db)
