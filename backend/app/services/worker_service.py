from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Campaign, Worker, WorkerRun, WorkerRunStatus, WorkerStatus
from app.services.audit import log_audit_event
from app.workers.executor import WorkerExecutor


def pause_worker(db: Session, worker: Worker, actor_id: str) -> Worker:
    worker.status = WorkerStatus.PAUSED.value
    worker.next_run_at = None
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
    worker.next_run_at = datetime.now(UTC) + timedelta(minutes=max(worker.run_interval_minutes, 15))
    log_audit_event(
        db,
        workspace_id=worker.workspace_id,
        actor_type="user",
        actor_id=actor_id,
        event_name="worker_resumed",
        payload={"worker_id": str(worker.id)},
    )
    return worker


def run_worker_for_campaign(
    db: Session,
    worker: Worker,
    campaign: Campaign,
    require_manual_approval: bool = True,
    run: WorkerRun | None = None,
):
    return WorkerExecutor().run_campaign_loop(
        db=db,
        worker=worker,
        campaign=campaign,
        require_manual_approval=require_manual_approval,
        run=run,
    )


def queue_worker_run(
    db: Session,
    worker: Worker,
    campaign: Campaign,
    actor_id: str,
    require_manual_approval: bool = True,
) -> WorkerRun:
    run = WorkerRun(
        worker_id=worker.id,
        campaign_id=campaign.id,
        run_type="campaign_loop",
        status=WorkerRunStatus.QUEUED.value,
        input_json={"campaign_id": str(campaign.id), "require_manual_approval": require_manual_approval},
    )
    db.add(run)
    worker.status = WorkerStatus.PROSPECTING.value
    worker.next_run_at = datetime.now(UTC)
    log_audit_event(
        db,
        workspace_id=worker.workspace_id,
        actor_type="user",
        actor_id=actor_id,
        event_name="worker_run_queued",
        payload={"worker_id": str(worker.id), "campaign_id": str(campaign.id), "run_id": str(run.id)},
    )
    return run


def list_worker_runs(db: Session, worker_id, limit: int = 20) -> list[WorkerRun]:
    return (
        db.query(WorkerRun)
        .filter(WorkerRun.worker_id == worker_id)
        .order_by(WorkerRun.started_at.desc())
        .limit(limit)
        .all()
    )
