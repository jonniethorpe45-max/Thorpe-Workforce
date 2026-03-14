from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ConnectedAccount, Meeting, User
from app.schemas.api import CalendarConnectRequest, MeetingBookRequest, MeetingRead
from app.services.meeting_service import book_meeting, connect_google_calendar

router = APIRouter(tags=["meetings"])


@router.get("/meetings", response_model=list[MeetingRead])
def list_meetings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Meeting).filter(Meeting.workspace_id == current_user.workspace_id).order_by(Meeting.created_at.desc()).all()


@router.post("/calendar/connect/google")
def connect_calendar(
    payload: CalendarConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = connect_google_calendar(auth_code=payload.auth_code, redirect_uri=payload.redirect_uri)
    existing = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.workspace_id == current_user.workspace_id,
            ConnectedAccount.provider_type == "google_calendar",
        )
        .first()
    )
    if not existing:
        db.add(
            ConnectedAccount(
                workspace_id=current_user.workspace_id,
                provider_type="google_calendar",
                access_token_encrypted="placeholder",
                refresh_token_encrypted="placeholder",
                metadata_json={"connected": result.get("connected", False)},
            )
        )
    db.commit()
    return result


@router.post("/meetings/book", response_model=MeetingRead)
def create_meeting(payload: MeetingBookRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        meeting = book_meeting(db, workspace_id=current_user.workspace_id, actor_id=str(current_user.id), payload=payload)
        db.commit()
        db.refresh(meeting)
        return meeting
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
