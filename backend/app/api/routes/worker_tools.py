from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, WorkerTool
from app.schemas.api import WorkerToolListResponse, WorkerToolRead
from app.services.worker_tools import ensure_system_worker_tools

router = APIRouter(prefix="/worker-tools", tags=["worker_tools"])


@router.get("", response_model=WorkerToolListResponse)
def list_tools(
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ = current_user  # auth guard; tools are global but only authenticated users can view.
    ensure_system_worker_tools(db)
    query = db.query(WorkerTool)
    if not include_inactive:
        query = query.filter(WorkerTool.is_active.is_(True))
    items = query.order_by(WorkerTool.category.asc(), WorkerTool.name.asc()).all()
    return WorkerToolListResponse(items=items, total=len(items))


@router.get("/{slug}", response_model=WorkerToolRead)
def get_tool(slug: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = current_user  # auth guard
    ensure_system_worker_tools(db)
    tool = db.query(WorkerTool).filter(WorkerTool.slug == slug).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Worker tool not found")
    return tool
