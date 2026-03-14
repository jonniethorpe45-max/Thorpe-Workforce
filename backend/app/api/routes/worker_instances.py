import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, WorkerInstance, WorkerRunStatus
from app.schemas.api import (
    WorkerInstanceExecuteRequest,
    WorkerInstanceExecuteResponse,
    WorkerInstanceRead,
    WorkerInstanceUpdate,
)
from app.services.worker_execution import execute_worker_instance_run, queue_worker_instance_run
from app.tasks.dispatcher import enqueue_task
from app.tasks.jobs import execute_worker_instance_run_task

router = APIRouter(prefix="/worker-instances", tags=["worker_instances"])


def _get_workspace_instance(db: Session, instance_id: uuid.UUID, workspace_id: uuid.UUID) -> WorkerInstance:
    instance = db.get(WorkerInstance, instance_id)
    if not instance or instance.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Worker instance not found")
    return instance


@router.get("", response_model=list[WorkerInstanceRead])
def list_worker_instances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(WorkerInstance)
        .filter(WorkerInstance.workspace_id == current_user.workspace_id)
        .order_by(WorkerInstance.created_at.desc())
        .all()
    )


@router.get("/{instance_id}", response_model=WorkerInstanceRead)
def get_worker_instance(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_workspace_instance(db, instance_id, current_user.workspace_id)


@router.patch("/{instance_id}", response_model=WorkerInstanceRead)
def update_worker_instance(
    instance_id: uuid.UUID,
    payload: WorkerInstanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id, current_user.workspace_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/{instance_id}/execute", response_model=WorkerInstanceExecuteResponse)
def execute_instance(
    instance_id: uuid.UUID,
    payload: WorkerInstanceExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id, current_user.workspace_id)
    run = queue_worker_instance_run(
        db,
        instance=instance,
        runtime_input=payload.runtime_input,
        trigger_source=payload.trigger_source or "manual_api",
    )
    db.flush()
    task_id = enqueue_task(execute_worker_instance_run_task, str(run.id))
    queued = True
    if not task_id:
        queued = False
        execute_worker_instance_run(db, run_id=run.id)
    db.commit()
    db.refresh(run)
    status_value = run.status if run.status in {item.value for item in WorkerRunStatus} else WorkerRunStatus.FAILED.value
    return WorkerInstanceExecuteResponse(
        success=run.status != WorkerRunStatus.FAILED.value,
        queued=queued,
        run_id=run.id,
        task_id=task_id,
        status=WorkerRunStatus(status_value),
    )
