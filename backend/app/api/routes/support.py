import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_platform_admin_access
from app.core.rate_limit import limit_requests
from app.db.session import get_db
from app.models import SupportRequestStatus, User
from app.schemas.api import SupportRequestCreate, SupportRequestRead, SupportRequestUpdate
from app.services.audit import log_audit_event
from app.services.support_requests import create_support_request, list_support_requests, update_support_request

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/contact", response_model=SupportRequestRead, dependencies=[Depends(limit_requests("support_contact", 60, 30))])
def create_contact_request(
    payload: SupportRequestCreate,
    db: Session = Depends(get_db),
):
    item = create_support_request(db, payload=payload, user=None)
    db.commit()
    db.refresh(item)
    return item


@router.post("/contact/authenticated", response_model=SupportRequestRead)
def create_authenticated_contact_request(
    payload: SupportRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = create_support_request(db, payload=payload, user=current_user)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="support_request_created",
        payload={"support_request_id": str(item.id), "subject": item.subject},
    )
    db.commit()
    db.refresh(item)
    return item


@router.get("/requests", response_model=list[SupportRequestRead])
def admin_support_requests(
    status: SupportRequestStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_platform_admin_access),
    db: Session = Depends(get_db),
):
    _ = current_user
    return list_support_requests(db, status=status, limit=limit)


@router.patch("/requests/{support_request_id}", response_model=SupportRequestRead)
def admin_update_support_request(
    support_request_id: uuid.UUID,
    payload: SupportRequestUpdate,
    current_user: User = Depends(require_platform_admin_access),
    db: Session = Depends(get_db),
):
    item = update_support_request(
        db,
        support_request_id=support_request_id,
        payload=payload,
        admin_user=current_user,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="support_request_updated",
        payload={"support_request_id": str(item.id), "status": item.status},
    )
    db.commit()
    db.refresh(item)
    return item
