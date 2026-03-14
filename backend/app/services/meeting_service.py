from sqlalchemy.orm import Session

from app.integrations.calendar.base import CalendarEventInput
from app.integrations.calendar.factory import get_calendar_provider
from app.models import Lead, LeadStatus, Meeting
from app.schemas.api import MeetingBookRequest
from app.services.audit import log_audit_event


def connect_google_calendar(auth_code: str | None, redirect_uri: str | None) -> dict:
    provider = get_calendar_provider()
    return provider.connect(auth_code=auth_code, redirect_uri=redirect_uri)


def book_meeting(db: Session, workspace_id, actor_id: str, payload: MeetingBookRequest) -> Meeting:
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise ValueError("Lead not found")
    provider = get_calendar_provider()
    event = provider.create_event(
        CalendarEventInput(
            title=f"Thorpe Workforce intro with {lead.company_name}",
            start=payload.scheduled_start,
            end=payload.scheduled_end,
            attendee_email=lead.email,
        )
    )
    meeting = Meeting(
        workspace_id=workspace_id,
        campaign_id=payload.campaign_id,
        lead_id=payload.lead_id,
        calendar_provider="google",
        external_event_id=event.external_event_id,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        meeting_status=event.status,
    )
    lead.lead_status = LeadStatus.MEETING_BOOKED.value
    db.add(meeting)
    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=actor_id,
        event_name="meeting_booked",
        payload={"lead_id": str(payload.lead_id), "campaign_id": str(payload.campaign_id)},
    )
    return meeting
