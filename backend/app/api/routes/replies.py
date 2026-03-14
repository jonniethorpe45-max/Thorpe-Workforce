import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Reply, SentEmail, User
from app.schemas.api import ReplyRead

router = APIRouter(prefix="/replies", tags=["replies"])


@router.get("", response_model=list[ReplyRead])
def list_replies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Reply)
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(SentEmail.workspace_id == current_user.workspace_id)
        .order_by(Reply.created_at.desc())
        .all()
    )


@router.get("/{reply_id}", response_model=ReplyRead)
def get_reply(reply_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reply = (
        db.query(Reply)
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(Reply.id == reply_id, SentEmail.workspace_id == current_user.workspace_id)
        .first()
    )
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return reply
