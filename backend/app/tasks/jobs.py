import uuid

from app.db.session import SessionLocal
from app.models import Campaign, Lead, SentEmail
from app.services.analytics import get_campaign_analytics
from app.services.followup_scheduler import schedule_followups
from app.services.lead_researcher import research_lead
from app.services.message_generator import generate_initial_sequence, send_approved_messages
from app.services.reply_classifier import classify_and_store_reply
from app.tasks.celery_app import celery_app


@celery_app.task
def research_lead_task(lead_id: str):
    db = SessionLocal()
    try:
        lead = db.get(Lead, uuid.UUID(lead_id))
        if lead:
            research_lead(db, lead)
            db.commit()
    finally:
        db.close()


@celery_app.task
def generate_messages_task(campaign_id: str, lead_id: str, require_approval: bool = True):
    db = SessionLocal()
    try:
        campaign = db.get(Campaign, uuid.UUID(campaign_id))
        lead = db.get(Lead, uuid.UUID(lead_id))
        if campaign and lead:
            generate_initial_sequence(db, campaign=campaign, lead=lead, require_approval=require_approval)
            db.commit()
    finally:
        db.close()


@celery_app.task
def send_approved_messages_task(workspace_id: str, campaign_id: str):
    db = SessionLocal()
    try:
        count = send_approved_messages(db, workspace_id=uuid.UUID(workspace_id), campaign_id=uuid.UUID(campaign_id))
        db.commit()
        return count
    finally:
        db.close()


@celery_app.task
def schedule_followups_task(campaign_id: str):
    db = SessionLocal()
    try:
        return schedule_followups(db, campaign_id=uuid.UUID(campaign_id))
    finally:
        db.close()


@celery_app.task
def process_reply_classification_task(sent_email_id: str, reply_text: str):
    db = SessionLocal()
    try:
        sent_email = db.get(SentEmail, uuid.UUID(sent_email_id))
        if sent_email:
            classify_and_store_reply(db, sent_email, reply_text=reply_text)
            db.commit()
    finally:
        db.close()


@celery_app.task
def update_campaign_analytics_task(workspace_id: str, campaign_id: str):
    db = SessionLocal()
    try:
        return get_campaign_analytics(db, workspace_id=uuid.UUID(workspace_id), campaign_id=uuid.UUID(campaign_id))
    finally:
        db.close()


@celery_app.task
def sync_meetings_task():
    return {"status": "placeholder", "message": "Meeting sync pipeline will be implemented for external sync"}
