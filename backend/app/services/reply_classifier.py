from sqlalchemy.orm import Session

from app.models import Lead, LeadStatus, Reply, ReplyIntent, SentEmail
from app.services.ai_service import classify_reply
from app.services.audit import log_audit_event


def classify_and_store_reply(db: Session, sent_email: SentEmail, reply_text: str) -> Reply:
    result = classify_reply(reply_text)
    sent_email.reply_detected = True
    lead = db.get(Lead, sent_email.lead_id)
    if lead:
        if result.intent == ReplyIntent.INTERESTED.value:
            lead.lead_status = LeadStatus.REPLIED_POSITIVE.value
        elif result.intent in {ReplyIntent.NOT_INTERESTED.value, ReplyIntent.UNSUBSCRIBE.value}:
            lead.lead_status = LeadStatus.REPLIED_NEGATIVE.value
            if result.intent == ReplyIntent.UNSUBSCRIBE.value:
                lead.lead_status = LeadStatus.DO_NOT_CONTACT.value
                sent_email.unsubscribed = True
        else:
            lead.lead_status = LeadStatus.REPLIED_NEUTRAL.value
    reply = Reply(
        sent_email_id=sent_email.id,
        lead_id=sent_email.lead_id,
        reply_text=reply_text,
        sentiment=result.sentiment,
        intent_classification=result.intent,
        requires_human_review=result.requires_human_review,
    )
    db.add(reply)
    log_audit_event(
        db,
        workspace_id=sent_email.workspace_id,
        actor_type="system",
        actor_id="reply_classifier",
        event_name="reply_classified",
        payload={"intent": result.intent, "confidence": result.confidence, "lead_id": str(sent_email.lead_id)},
    )
    return reply
