from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.integrations.email.base import SendEmailInput
from app.integrations.email.factory import get_email_provider
from app.models import ApprovalStatus, Campaign, GeneratedMessage, Lead, LeadStatus, SentEmail, Worker
from app.services.audit import log_audit_event
from app.services.ai_service import generate_followup_email, generate_outreach_email
from app.services.email_safety import is_lead_send_eligible, remaining_send_capacity


def generate_initial_sequence(
    db: Session,
    campaign: Campaign,
    lead: Lead,
    require_approval: bool = True,
    worker_type: str = "ai_sales_worker",
) -> list[GeneratedMessage]:
    cta = campaign.cta_text or "Would you be open to a 15-minute intro next week?"
    lead_name = lead.first_name or lead.full_name or "there"
    existing_steps = {
        row[0]
        for row in db.query(GeneratedMessage.sequence_step)
        .filter(GeneratedMessage.campaign_id == campaign.id, GeneratedMessage.lead_id == lead.id)
        .all()
    }

    step1 = generate_outreach_email(
        lead_name=lead_name,
        company_name=lead.company_name,
        title=lead.title,
        cta=cta,
        worker_type=worker_type,
    )
    generated: list[GeneratedMessage] = []
    if 1 not in existing_steps:
        generated.append(
            GeneratedMessage(
                campaign_id=campaign.id,
                lead_id=lead.id,
                sequence_step=1,
                subject_line=step1.subject,
                body_text=step1.body,
                personalization_json=step1.personalization,
                approval_status=ApprovalStatus.PENDING.value if require_approval else ApprovalStatus.APPROVED.value,
            )
        )
    for step in [2, 3, 4]:
        if step in existing_steps:
            continue
        followup = generate_followup_email(
            lead_name=lead_name,
            company_name=lead.company_name,
            step=step - 1,
            cta=cta,
            worker_type=worker_type,
        )
        generated.append(
            GeneratedMessage(
                campaign_id=campaign.id,
                lead_id=lead.id,
                sequence_step=step,
                subject_line=followup.subject,
                body_text=followup.body,
                personalization_json=followup.personalization,
                approval_status=ApprovalStatus.PENDING.value if require_approval else ApprovalStatus.APPROVED.value,
            )
        )
    for message in generated:
        db.add(message)
    return generated


def regenerate_message(
    db: Session,
    message: GeneratedMessage,
    campaign: Campaign,
    lead: Lead,
    worker_type: str = "ai_sales_worker",
) -> GeneratedMessage:
    cta = campaign.cta_text or "Would a short intro call be helpful?"
    lead_name = lead.first_name or lead.full_name or "there"
    if message.sequence_step == 1:
        result = generate_outreach_email(
            lead_name=lead_name,
            company_name=lead.company_name,
            title=lead.title,
            cta=cta,
            worker_type=worker_type,
        )
    else:
        result = generate_followup_email(
            lead_name=lead_name,
            company_name=lead.company_name,
            step=message.sequence_step - 1,
            cta=cta,
            worker_type=worker_type,
        )
    message.subject_line = result.subject
    message.body_text = result.body
    message.personalization_json = result.personalization
    message.approval_status = ApprovalStatus.PENDING.value
    return message


def send_approved_messages(db: Session, workspace_id, campaign_id) -> int:
    email_provider = get_email_provider()
    campaign = db.get(Campaign, campaign_id)
    daily_cap = 40
    worker_id = None
    if campaign and campaign.worker_id:
        worker = db.get(Worker, campaign.worker_id)
        if worker:
            daily_cap = worker.send_limit_per_day
            worker_id = worker.id
    remaining_capacity = remaining_send_capacity(
        db,
        workspace_id=workspace_id,
        campaign_id=campaign_id,
        worker_id=worker_id,
        worker_daily_limit=daily_cap,
    )
    if remaining_capacity == 0:
        return 0

    pending_send = (
        db.query(GeneratedMessage)
        .filter(
            GeneratedMessage.campaign_id == campaign_id,
            GeneratedMessage.approval_status == ApprovalStatus.APPROVED.value,
        )
        .order_by(GeneratedMessage.created_at.asc())
        .all()
    )
    sent_count = 0
    suppressed_count = 0
    for message in pending_send:
        if sent_count >= remaining_capacity:
            break
        lead = db.get(Lead, message.lead_id)
        if not lead:
            continue
        eligible, reason = is_lead_send_eligible(
            db,
            workspace_id=workspace_id,
            campaign_id=campaign_id,
            lead=lead,
            sequence_step=message.sequence_step,
        )
        if not eligible:
            if reason in {"suppressed_by_unsubscribe_or_bounce", "workspace_do_not_contact"}:
                lead.lead_status = LeadStatus.DO_NOT_CONTACT.value
            suppressed_count += 1
            continue
        try:
            send_result = email_provider.send_email(
                SendEmailInput(to_email=lead.email, subject=message.subject_line, body=message.body_text)
            )
            db.add(
                SentEmail(
                    workspace_id=workspace_id,
                    campaign_id=message.campaign_id,
                    lead_id=lead.id,
                    generated_message_id=message.id,
                    provider_message_id=send_result.provider_message_id,
                    sent_at=datetime.now(UTC),
                    delivery_status=send_result.status,
                )
            )
            lead.lead_status = LeadStatus.CONTACTED.value
            sent_count += 1
        except Exception as exc:
            db.add(
                SentEmail(
                    workspace_id=workspace_id,
                    campaign_id=message.campaign_id,
                    lead_id=lead.id,
                    generated_message_id=message.id,
                    provider_message_id=None,
                    sent_at=datetime.now(UTC),
                    delivery_status="failed",
                )
            )
            log_audit_event(
                db,
                workspace_id=workspace_id,
                actor_type="system",
                actor_id="email_sender",
                event_name="email_send_failed",
                payload={"lead_id": str(lead.id), "message_id": str(message.id), "error": str(exc)},
            )
    if sent_count or suppressed_count:
        log_audit_event(
            db,
            workspace_id=workspace_id,
            actor_type="system",
            actor_id="email_sender",
            event_name="approved_messages_processed",
            payload={
                "campaign_id": str(campaign_id),
                "sent_count": sent_count,
                "suppressed_count": suppressed_count,
                "daily_capacity": remaining_capacity,
                "processed_on": date.today().isoformat(),
            },
        )
    return sent_count
