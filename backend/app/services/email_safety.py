import re
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Campaign, GeneratedMessage, Lead, LeadStatus, SentEmail

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match((email or "").strip().lower()))


def _sent_today_count(items: list[SentEmail]) -> int:
    today = date.today()
    return sum(1 for item in items if item.sent_at and item.sent_at.date() == today)


def remaining_send_capacity(
    db: Session,
    workspace_id,
    campaign_id,
    worker_id,
    worker_daily_limit: int,
) -> int:
    workspace_sends = db.query(SentEmail).filter(SentEmail.workspace_id == workspace_id, SentEmail.sent_at.isnot(None)).all()
    workspace_remaining = max(settings.workspace_daily_send_cap - _sent_today_count(workspace_sends), 0)

    campaign_sends = (
        db.query(SentEmail).filter(SentEmail.workspace_id == workspace_id, SentEmail.campaign_id == campaign_id).all()
    )
    campaign_remaining = max(worker_daily_limit - _sent_today_count(campaign_sends), 0)

    worker_remaining = campaign_remaining
    if worker_id:
        worker_sends = (
            db.query(SentEmail)
            .join(Campaign, SentEmail.campaign_id == Campaign.id)
            .filter(SentEmail.workspace_id == workspace_id, Campaign.worker_id == worker_id)
            .all()
        )
        worker_remaining = max(worker_daily_limit - _sent_today_count(worker_sends), 0)

    return min(workspace_remaining, campaign_remaining, worker_remaining)


def is_lead_send_eligible(db: Session, workspace_id, campaign_id, lead: Lead, sequence_step: int) -> tuple[bool, str]:
    if lead.lead_status == LeadStatus.DO_NOT_CONTACT.value:
        return False, "lead_marked_do_not_contact"
    if not is_valid_email(lead.email):
        return False, "invalid_email"

    same_email_lead = db.query(Lead).filter(Lead.workspace_id == workspace_id, Lead.email == lead.email.lower()).first()
    if same_email_lead and same_email_lead.lead_status == LeadStatus.DO_NOT_CONTACT.value:
        return False, "workspace_do_not_contact"

    prior_suppression_event = (
        db.query(SentEmail)
        .join(Lead, SentEmail.lead_id == Lead.id)
        .filter(
            SentEmail.workspace_id == workspace_id,
            Lead.email == lead.email.lower(),
            (SentEmail.unsubscribed.is_(True) | SentEmail.bounce_detected.is_(True)),
        )
        .first()
    )
    if prior_suppression_event:
        return False, "suppressed_by_unsubscribe_or_bounce"

    duplicate_step = (
        db.query(SentEmail)
        .join(GeneratedMessage, SentEmail.generated_message_id == GeneratedMessage.id)
        .filter(
            SentEmail.workspace_id == workspace_id,
            SentEmail.campaign_id == campaign_id,
            SentEmail.lead_id == lead.id,
            GeneratedMessage.sequence_step == sequence_step,
            SentEmail.delivery_status.in_(["queued", "sent", "delivered"]),
        )
        .first()
    )
    if duplicate_step:
        return False, "duplicate_step_send_prevented"

    return True, "eligible"


def mark_bounce_or_unsubscribe_do_not_contact(db: Session, lead: Lead) -> None:
    lead.lead_status = LeadStatus.DO_NOT_CONTACT.value
    lead.updated_at = datetime.now(UTC)
