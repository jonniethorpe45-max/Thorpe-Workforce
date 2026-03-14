import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, Worker
from app.schemas.api import WorkerCreate, WorkerRead, WorkerUpdate
from app.services.audit import log_audit_event
from app.services.worker_service import pause_worker, resume_worker

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("", response_model=WorkerRead)
def create_worker(payload: WorkerCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    worker = Worker(
        workspace_id=current_user.workspace_id,
        name=payload.name,
        worker_type="ai_sales_worker",
        goal=payload.goal,
        tone=payload.tone,
        send_limit_per_day=payload.daily_send_limit,
        config_json={
            "target_industry": payload.target_industry,
            "target_roles": payload.target_roles,
            "target_locations": payload.target_locations,
            "company_size_range": payload.company_size_range,
        },
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
    for field in ["name", "goal", "tone", "status", "config_json"]:
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
