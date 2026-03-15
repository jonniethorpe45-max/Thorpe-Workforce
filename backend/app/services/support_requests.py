from datetime import UTC, datetime
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import SupportRequest, SupportRequestStatus, User
from app.schemas.api import SupportRequestCreate, SupportRequestUpdate
from app.services.transactional_email import send_transactional_email


def create_support_request(
    db: Session,
    *,
    payload: SupportRequestCreate,
    user: User | None = None,
) -> SupportRequest:
    request = SupportRequest(
        workspace_id=user.workspace_id if user else None,
        user_id=user.id if user else None,
        name=payload.name,
        email=str(payload.email).lower(),
        subject=payload.subject,
        message=payload.message,
        source=payload.source,
        status=SupportRequestStatus.OPEN.value,
        metadata_json={},
    )
    db.add(request)
    db.flush()
    try:
        send_transactional_email(
            to_email=request.email,
            template_key="support_request_received",
            recipient_name=request.name,
            context={},
        )
    except Exception:
        # Non-blocking for MVP launch flow.
        pass
    return request


def list_support_requests(
    db: Session,
    *,
    status: SupportRequestStatus | None = None,
    limit: int = 100,
) -> list[SupportRequest]:
    query = db.query(SupportRequest)
    if status:
        query = query.filter(SupportRequest.status == status.value)
    return query.order_by(SupportRequest.created_at.desc()).limit(max(limit, 1)).all()


def update_support_request(
    db: Session,
    *,
    support_request_id: uuid.UUID,
    payload: SupportRequestUpdate,
    admin_user: User,
) -> SupportRequest:
    item = db.get(SupportRequest, support_request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Support request not found")
    item.status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
    item.handled_by_user_id = admin_user.id
    if item.status in {SupportRequestStatus.RESOLVED.value, SupportRequestStatus.CLOSED.value}:
        item.resolved_at = datetime.now(UTC)
    if payload.resolution_note:
        metadata = dict(item.metadata_json or {})
        metadata["resolution_note"] = payload.resolution_note
        item.metadata_json = metadata
    db.flush()
    return item
