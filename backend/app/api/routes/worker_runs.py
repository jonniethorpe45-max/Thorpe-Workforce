import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, Worker, WorkerRun
from app.schemas.api import WorkerRunListResponse, WorkerRunRead

router = APIRouter(prefix="/worker-runs", tags=["worker_runs"])


def _workspace_runs_query(db: Session, workspace_id: uuid.UUID):
    return db.query(WorkerRun).join(Worker, Worker.id == WorkerRun.worker_id).filter(Worker.workspace_id == workspace_id)


@router.get("", response_model=WorkerRunListResponse)
def list_runs(
    instance_id: uuid.UUID | None = Query(default=None),
    template_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _workspace_runs_query(db, current_user.workspace_id)
    if instance_id:
        query = query.filter(WorkerRun.instance_id == instance_id)
    if template_id:
        query = query.filter(WorkerRun.template_id == template_id)
    if status:
        query = query.filter(WorkerRun.status == status)
    total = query.count()
    items = query.order_by(WorkerRun.started_at.desc()).limit(limit).all()
    return WorkerRunListResponse(items=items, total=total)


@router.get("/{run_id}", response_model=WorkerRunRead)
def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run = _workspace_runs_query(db, current_user.workspace_id).filter(WorkerRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Worker run not found")
    return run
