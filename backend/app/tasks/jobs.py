import uuid

from app.db.session import SessionLocal
from app.models import Campaign, Lead, SentEmail, Worker, WorkerRun, WorkerRunStatus
from app.services.analytics import get_campaign_analytics
from app.services.audit import log_audit_event
from app.services.followup_scheduler import schedule_followups
from app.services.lead_researcher import research_lead
from app.services.message_generator import generate_initial_sequence, send_approved_messages
from app.services.reply_classifier import classify_and_store_reply
from app.services.worker_execution import execute_worker_instance_run
from app.workers.executor import WorkerExecutor
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
            worker_type = "ai_sales_worker"
            if campaign.worker_id:
                worker = db.get(Worker, campaign.worker_id)
                if worker:
                    worker_type = worker.worker_type
            generate_initial_sequence(
                db,
                campaign=campaign,
                lead=lead,
                require_approval=require_approval,
                worker_type=worker_type,
            )
            db.commit()
    finally:
        db.close()


@celery_app.task
def send_approved_messages_task(workspace_id: str, campaign_id: str):
    db = SessionLocal()
    try:
        count = send_approved_messages(db, workspace_id=uuid.UUID(workspace_id), campaign_id=uuid.UUID(campaign_id))
        schedule_followups(db, campaign_id=uuid.UUID(campaign_id))
        log_audit_event(
            db,
            workspace_id=uuid.UUID(workspace_id),
            actor_type="system",
            actor_id="celery_sender",
            event_name="approved_messages_send_task_completed",
            payload={"campaign_id": campaign_id, "sent_count": count},
        )
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
            reply = classify_and_store_reply(db, sent_email, reply_text=reply_text)
            db.commit()
            return str(reply.id)
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
    return {"status": "ok", "message": "Meeting sync stub executed", "provider": "mock"}


@celery_app.task
def execute_worker_run_task(run_id: str):
    db = SessionLocal()
    try:
        run = db.get(WorkerRun, uuid.UUID(run_id))
        if not run:
            return {"success": False, "error": "run_not_found"}
        worker = db.get(Worker, run.worker_id)
        campaign = db.get(Campaign, run.campaign_id) if run.campaign_id else None
        if not worker or not campaign:
            run.status = WorkerRunStatus.FAILED.value
            run.error_text = "worker_or_campaign_not_found"
            db.commit()
            return {"success": False, "error": "worker_or_campaign_not_found"}

        require_manual_approval = bool((run.input_json or {}).get("require_manual_approval", True))
        run.attempts = max((run.attempts or 1), 1)
        WorkerExecutor().run_campaign_loop(
            db=db,
            worker=worker,
            campaign=campaign,
            require_manual_approval=require_manual_approval,
            run=run,
        )
        db.commit()
        return {"success": True, "run_id": run_id, "status": run.status}
    except Exception as exc:
        db.rollback()
        run = db.get(WorkerRun, uuid.UUID(run_id))
        if run:
            run.attempts = max((run.attempts or 1) + 1, 1)
            run.status = WorkerRunStatus.FAILED.value
            run.error_text = str(exc)
            db.commit()
        return {"success": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task
def execute_worker_instance_run_task(run_id: str):
    db = SessionLocal()
    try:
        run = db.get(WorkerRun, uuid.UUID(run_id))
        if not run:
            return {"success": False, "error": "run_not_found"}
        execute_worker_instance_run(db, run_id=uuid.UUID(run_id))
        db.commit()
        return {"success": True, "run_id": run_id, "status": run.status}
    except Exception as exc:
        db.rollback()
        run = db.get(WorkerRun, uuid.UUID(run_id))
        if run:
            run.status = WorkerRunStatus.FAILED.value
            run.error_message = str(exc)
            run.error_text = str(exc)
            run.attempts = max((run.attempts or 1) + 1, 1)
            db.commit()
        return {"success": False, "error": str(exc)}
    finally:
        db.close()
