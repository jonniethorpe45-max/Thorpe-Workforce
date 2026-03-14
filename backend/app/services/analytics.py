from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    ApprovalStatus,
    AuditLog,
    Campaign,
    CompanyResearch,
    GeneratedMessage,
    Lead,
    Meeting,
    Reply,
    ReplyIntent,
    SentEmail,
    Worker,
    WorkerRun,
)


def get_overview(db: Session, workspace_id) -> dict:
    active_workers = (
        db.query(func.count(Worker.id))
        .filter(Worker.workspace_id == workspace_id, Worker.status.notin_(["paused", "error"]))
        .scalar()
        or 0
    )
    campaigns = db.query(func.count(Campaign.id)).filter(Campaign.workspace_id == workspace_id).scalar() or 0
    leads_found = db.query(func.count(Lead.id)).filter(Lead.workspace_id == workspace_id).scalar() or 0
    leads_researched = (
        db.query(func.count(CompanyResearch.id))
        .join(Lead, CompanyResearch.lead_id == Lead.id)
        .filter(Lead.workspace_id == workspace_id)
        .scalar()
        or 0
    )
    messages_awaiting_approval = (
        db.query(func.count(GeneratedMessage.id))
        .join(Campaign, GeneratedMessage.campaign_id == Campaign.id)
        .filter(Campaign.workspace_id == workspace_id, GeneratedMessage.approval_status == ApprovalStatus.PENDING.value)
        .scalar()
        or 0
    )
    emails_sent = db.query(func.count(SentEmail.id)).filter(SentEmail.workspace_id == workspace_id).scalar() or 0
    replies = (
        db.query(func.count(Reply.id))
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(SentEmail.workspace_id == workspace_id)
        .scalar()
        or 0
    )
    interested_replies = (
        db.query(func.count(Reply.id))
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(
            SentEmail.workspace_id == workspace_id,
            Reply.intent_classification.in_([ReplyIntent.INTERESTED.value, ReplyIntent.REFERRAL.value]),
        )
        .scalar()
        or 0
    )
    meetings = db.query(func.count(Meeting.id)).filter(Meeting.workspace_id == workspace_id).scalar() or 0
    recent_activity = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_worker_runs = (
        db.query(WorkerRun, Worker.name)
        .join(Worker, WorkerRun.worker_id == Worker.id)
        .filter(Worker.workspace_id == workspace_id)
        .order_by(WorkerRun.started_at.desc())
        .limit(8)
        .all()
    )
    return {
        "active_workers": active_workers,
        "campaigns": campaigns,
        "leads_found": leads_found,
        "leads_researched": leads_researched,
        "messages_awaiting_approval": messages_awaiting_approval,
        "emails_sent": emails_sent,
        "replies": replies,
        "interested_replies": interested_replies,
        "meetings_booked": meetings,
        "recent_activity": [
            {"event_name": item.event_name, "created_at": item.created_at.isoformat(), "payload": item.payload_json or {}}
            for item in recent_activity
        ],
        "recent_worker_runs": [
            {
                "run_id": str(run.id),
                "worker_id": str(run.worker_id),
                "worker_name": worker_name,
                "status": run.status,
                "started_at": run.started_at.isoformat(),
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "campaign_id": str(run.campaign_id) if run.campaign_id else None,
            }
            for run, worker_name in recent_worker_runs
        ],
    }


def get_campaign_analytics(db: Session, workspace_id, campaign_id) -> dict:
    sent = (
        db.query(func.count(SentEmail.id))
        .filter(SentEmail.workspace_id == workspace_id, SentEmail.campaign_id == campaign_id)
        .scalar()
        or 0
    )
    replies = (
        db.query(func.count(Reply.id))
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(SentEmail.workspace_id == workspace_id, SentEmail.campaign_id == campaign_id)
        .scalar()
        or 0
    )
    meetings = (
        db.query(func.count(Meeting.id))
        .filter(Meeting.workspace_id == workspace_id, Meeting.campaign_id == campaign_id)
        .scalar()
        or 0
    )
    rate = float(replies / sent) if sent else 0.0
    return {"campaign_id": campaign_id, "sent": sent, "replies": replies, "meetings": meetings, "positive_reply_rate": rate}


def get_worker_analytics(db: Session, worker_id) -> dict:
    runs = db.query(func.count(WorkerRun.id)).filter(WorkerRun.worker_id == worker_id).scalar() or 0
    successful_runs = (
        db.query(func.count(WorkerRun.id)).filter(WorkerRun.worker_id == worker_id, WorkerRun.status == "completed").scalar()
        or 0
    )
    failed_runs = (
        db.query(func.count(WorkerRun.id)).filter(WorkerRun.worker_id == worker_id, WorkerRun.status == "failed").scalar()
        or 0
    )
    worker = db.get(Worker, worker_id)
    return {
        "worker_id": worker_id,
        "runs": runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "status": worker.status if worker else "unknown",
    }
