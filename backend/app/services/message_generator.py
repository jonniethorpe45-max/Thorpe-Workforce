from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.integrations.email.base import SendEmailInput
from app.integrations.email.factory import get_email_provider
from app.models import ApprovalStatus, Campaign, GeneratedMessage, Lead, LeadStatus, SentEmail, Worker
from app.services.ai_service import generate_followup_email, generate_outreach_email


def generate_initial_sequence(db: Session, campaign: Campaign, lead: Lead, require_approval: bool = True) -> list[GeneratedMessage]:
    cta = campaign.cta_text or "Would you be open to a 15-minute intro next week?"
    lead_name = lead.first_name or lead.full_name or "there"

    step1 = generate_outreach_email(lead_name=lead_name, company_name=lead.company_name, title=lead.title, cta=cta)
    generated = [
        GeneratedMessage(
            campaign_id=campaign.id,
            lead_id=lead.id,
            sequence_step=1,
            subject_line=step1.subject,
            body_text=step1.body,
            personalization_json=step1.personalization,
            approval_status=ApprovalStatus.PENDING.value if require_approval else ApprovalStatus.APPROVED.value,
        )
    ]
    for step in [2, 3, 4]:
        followup = generate_followup_email(
            lead_name=lead_name,
            company_name=lead.company_name,
            step=step - 1,
            cta=cta,
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


def regenerate_message(db: Session, message: GeneratedMessage, campaign: Campaign, lead: Lead) -> GeneratedMessage:
    cta = campaign.cta_text or "Would a short intro call be helpful?"
    lead_name = lead.first_name or lead.full_name or "there"
    if message.sequence_step == 1:
        result = generate_outreach_email(lead_name=lead_name, company_name=lead.company_name, title=lead.title, cta=cta)
    else:
        result = generate_followup_email(
            lead_name=lead_name,
            company_name=lead.company_name,
            step=message.sequence_step - 1,
            cta=cta,
        )
    message.subject_line = result.subject
    message.body_text = result.body
    message.personalization_json = result.personalization
    message.approval_status = ApprovalStatus.PENDING.value
    return message


def send_approved_messages(db: Session, workspace_id, campaign_id) -> int:
    email_provider = get_email_provider()
    campaign = db.get(Campaign, campaign_id)
    daily_cap = 100
    if campaign and campaign.worker_id:
        worker = db.get(Worker, campaign.worker_id)
        if worker:
            daily_cap = worker.send_limit_per_day
    sent_today = (
        db.query(SentEmail)
        .filter(
            SentEmail.workspace_id == workspace_id,
            SentEmail.campaign_id == campaign_id,
            SentEmail.sent_at.isnot(None),
        )
        .all()
    )
    sent_today_count = sum(1 for item in sent_today if item.sent_at and item.sent_at.date() == date.today())
    remaining_capacity = max(daily_cap - sent_today_count, 0)
    if remaining_capacity == 0:
        return 0

    pending_send = (
        db.query(GeneratedMessage)
        .filter(
            GeneratedMessage.campaign_id == campaign_id,
            GeneratedMessage.approval_status == ApprovalStatus.APPROVED.value,
        )
        .all()
    )
    sent_count = 0
    for message in pending_send:
        if sent_count >= remaining_capacity:
            break
        lead = db.get(Lead, message.lead_id)
        if not lead:
            continue
        if lead.lead_status == LeadStatus.DO_NOT_CONTACT.value:
            continue
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
    return sent_count
