from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Lead, SentEmail
from app.schemas.api import WebhookPayload
from app.services.email_safety import mark_bounce_or_unsubscribe_do_not_contact
from app.services.reply_classifier import classify_and_store_reply
from app.tasks.dispatcher import enqueue_task
from app.tasks.jobs import process_reply_classification_task

router = APIRouter(prefix="/webhooks/email", tags=["webhooks"])


def _find_sent_email(db: Session, payload: WebhookPayload) -> SentEmail | None:
    if payload.provider_message_id:
        return db.query(SentEmail).filter(SentEmail.provider_message_id == payload.provider_message_id).first()
    if payload.email:
        return (
            db.query(SentEmail)
            .join(Lead, SentEmail.lead_id == Lead.id)
            .filter(Lead.email == payload.email.lower())
            .order_by(SentEmail.created_at.desc())
            .first()
        )
    return None


@router.post("/delivery")
def delivery_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    if sent_email:
        sent_email.delivery_status = "delivered"
        db.commit()
    return {"success": True}


@router.post("/open")
def open_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    if sent_email:
        sent_email.open_count += 1
        db.commit()
    return {"success": True}


@router.post("/click")
def click_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    if sent_email:
        sent_email.click_count += 1
        db.commit()
    return {"success": True}


@router.post("/reply")
def reply_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    task_id = None
    if sent_email:
        reply_text = payload.data.get("reply_text", "")
        task_id = enqueue_task(process_reply_classification_task, str(sent_email.id), reply_text)
        if not task_id:
            classify_and_store_reply(db, sent_email=sent_email, reply_text=reply_text)
            db.commit()
    return {"success": True, "queued": bool(task_id), "task_id": task_id}


@router.post("/bounce")
def bounce_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    if sent_email:
        sent_email.bounce_detected = True
        sent_email.delivery_status = "bounced"
        lead = db.get(Lead, sent_email.lead_id)
        if lead:
            mark_bounce_or_unsubscribe_do_not_contact(db, lead)
        db.commit()
    return {"success": True}


@router.post("/unsubscribe")
def unsubscribe_event(payload: WebhookPayload, db: Session = Depends(get_db)):
    sent_email = _find_sent_email(db, payload)
    if sent_email:
        sent_email.unsubscribed = True
        sent_email.delivery_status = "unsubscribed"
        lead = db.get(Lead, sent_email.lead_id)
        if lead:
            mark_bounce_or_unsubscribe_do_not_contact(db, lead)
        db.commit()
    return {"success": True}
