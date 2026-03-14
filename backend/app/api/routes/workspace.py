from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, Workspace
from app.schemas.api import WorkspaceRead, WorkspaceUpdate
from app.services.audit import log_audit_event

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("", response_model=WorkspaceRead)
def get_workspace(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = db.get(Workspace, current_user.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("", response_model=WorkspaceRead)
def update_workspace(
    payload: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = db.get(Workspace, current_user.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(workspace, field, value)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="workspace_updated",
        payload=payload.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(workspace)
    return workspace
