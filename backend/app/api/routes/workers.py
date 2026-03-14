import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Campaign, User, Worker, WorkerStatus, WorkerTemplate
from app.schemas.api import WorkerCreate, WorkerRead, WorkerRunRead, WorkerTemplateRead, WorkerUpdate
from app.services.audit import log_audit_event
from app.services.worker_definitions import (
    build_worker_config,
    ensure_builtin_worker_templates,
    resolve_worker_definition,
)
from app.services.worker_service import list_worker_runs, pause_worker, queue_worker_run, resume_worker, run_worker_for_campaign
from app.tasks.dispatcher import enqueue_task
from app.tasks.jobs import execute_worker_run_task

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("", response_model=WorkerRead)
def create_worker(payload: WorkerCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_builtin_worker_templates(db)
    try:
        definition = resolve_worker_definition(payload.worker_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not definition.public_available:
        raise HTTPException(status_code=403, detail="Worker type is not publicly available")

    selected_template: WorkerTemplate | None = None
    if payload.template_id:
        selected_template = db.get(WorkerTemplate, payload.template_id)
        if not selected_template:
            raise HTTPException(status_code=404, detail="Worker template not found")
        if selected_template.worker_type != definition.worker_type:
            raise HTTPException(status_code=400, detail="Template does not match worker type")
        if selected_template.workspace_id is not None:
            raise HTTPException(status_code=400, detail="Public worker creation only supports built-in templates")
    if not selected_template:
        selected_template = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.template_key == definition.worker_type, WorkerTemplate.workspace_id.is_(None))
            .first()
        )

    worker = Worker(
        workspace_id=current_user.workspace_id,
        name=payload.name,
        worker_type=definition.worker_type,
        worker_category=definition.worker_category,
        mission=payload.goal,
        goal=payload.goal,
        plan_version=definition.plan_version,
        allowed_actions=list(definition.allowed_actions),
        template_id=selected_template.id if selected_template else None,
        origin_type=definition.origin_type,
        is_custom_worker=False,
        is_internal=False,
        tone=payload.tone,
        send_limit_per_day=payload.daily_send_limit,
        run_interval_minutes=max(payload.run_interval_minutes, 15),
        next_run_at=datetime.now(UTC) + timedelta(minutes=max(payload.run_interval_minutes, 15)),
        config_json=build_worker_config(
            definition,
            target_industry=payload.target_industry,
            target_roles=payload.target_roles,
            target_locations=payload.target_locations,
            company_size_range=payload.company_size_range,
        ),
    )
    db.add(worker)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_created",
        payload={"worker_name": worker.name},
    )
    db.commit()
    db.refresh(worker)
    return worker


@router.get("", response_model=list[WorkerRead])
def list_workers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Worker).filter(Worker.workspace_id == current_user.workspace_id).order_by(Worker.created_at.desc()).all()


@router.get("/{worker_id}", response_model=WorkerRead)
def get_worker(worker_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.get("/templates/library", response_model=list[WorkerTemplateRead])
def list_worker_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_builtin_worker_templates(db)
    templates = (
        db.query(WorkerTemplate)
        .filter(WorkerTemplate.is_active.is_(True), WorkerTemplate.is_public.is_(True), WorkerTemplate.workspace_id.is_(None))
        .order_by(WorkerTemplate.display_name.asc())
        .all()
    )
    db.commit()
    return templates


@router.patch("/{worker_id}", response_model=WorkerRead)
def update_worker(
    worker_id: uuid.UUID,
    payload: WorkerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    if payload.daily_send_limit is not None:
        worker.send_limit_per_day = payload.daily_send_limit
    if payload.run_interval_minutes is not None:
        worker.run_interval_minutes = max(payload.run_interval_minutes, 15)
        if worker.status != WorkerStatus.PAUSED.value:
            worker.next_run_at = datetime.now(UTC) + timedelta(minutes=worker.run_interval_minutes)
    if payload.status is not None and payload.status not in {item.value for item in WorkerStatus}:
        raise HTTPException(status_code=400, detail="Invalid worker status")
    if payload.goal is not None and payload.mission is None:
        worker.mission = payload.goal
    for field in [
        "name",
        "mission",
        "goal",
        "tone",
        "status",
        "config_json",
        "plan_version",
        "allowed_actions",
        "is_internal",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(worker, field, value)
    db.commit()
    db.refresh(worker)
    return worker


@router.post("/{worker_id}/pause", response_model=WorkerRead)
def pause(worker_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    pause_worker(db, worker, actor_id=str(current_user.id))
    db.commit()
    db.refresh(worker)
    return worker


@router.post("/{worker_id}/resume", response_model=WorkerRead)
def resume(worker_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    resume_worker(db, worker, actor_id=str(current_user.id))
    db.commit()
    db.refresh(worker)
    return worker


@router.get("/{worker_id}/runs", response_model=list[WorkerRunRead])
def worker_runs(worker_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    return list_worker_runs(db, worker_id=worker.id)


@router.post("/{worker_id}/execute")
def execute_worker(
    worker_id: uuid.UUID,
    campaign_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    worker = db.get(Worker, worker_id)
    if not worker or worker.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Worker not found")
    campaign = db.get(Campaign, campaign_id)
    if not campaign or campaign.workspace_id != current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    run = queue_worker_run(
        db,
        worker=worker,
        campaign=campaign,
        actor_id=str(current_user.id),
        require_manual_approval=False,
    )
    db.flush()
    task_id = enqueue_task(execute_worker_run_task, str(run.id))
    queued = True
    if not task_id:
        queued = False
        run_worker_for_campaign(
            db=db,
            worker=worker,
            campaign=campaign,
            require_manual_approval=False,
            run=run,
        )
    db.commit()
    return {"success": True, "run_id": str(run.id), "queued": queued, "task_id": task_id}
