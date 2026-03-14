from sqlalchemy.orm import Session

from app.models import Campaign, Worker, WorkerStatus
from app.services.audit import log_audit_event
from app.workers.executor import WorkerExecutor


def pause_worker(db: Session, worker: Worker, actor_id: str) -> Worker:
    worker.status = WorkerStatus.PAUSED.value
    log_audit_event(
        db,
        workspace_id=worker.workspace_id,
        actor_type="user",
        actor_id=actor_id,
        event_name="worker_paused",
        payload={"worker_id": str(worker.id)},
    )
    return worker


def resume_worker(db: Session, worker: Worker, actor_id: str) -> Worker:
    worker.status = WorkerStatus.IDLE.value
    log_audit_event(
        db,
        workspace_id=worker.workspace_id,
        actor_type="user",
        actor_id=actor_id,
        event_name="worker_resumed",
        payload={"worker_id": str(worker.id)},
    )
    return worker


def run_worker_for_campaign(db: Session, worker: Worker, campaign: Campaign, require_manual_approval: bool = True):
    return WorkerExecutor().run_campaign_loop(
        db=db,
        worker=worker,
        campaign=campaign,
        require_manual_approval=require_manual_approval,
    )
