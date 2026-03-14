from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_internal_worker_builder_access
from app.db.session import get_db
from app.models import User
from app.schemas.api import (
    InternalWorkerFromTemplateCreate,
    InternalWorkerTemplateCreate,
    WorkerBuilderActionRead,
    WorkerRead,
    WorkerTemplateRead,
)
from app.services.audit import log_audit_event
from app.services.worker_builder import (
    create_internal_template,
    create_worker_from_template,
    list_builder_actions,
    list_internal_templates,
)
from app.services.worker_definitions import ensure_builtin_worker_templates

router = APIRouter(prefix="/workers/internal", tags=["worker_builder_internal"])


@router.get("/builder/actions", response_model=list[WorkerBuilderActionRead])
def get_available_actions(
    current_user: User = Depends(require_internal_worker_builder_access),
    db: Session = Depends(get_db),
):
    return list_builder_actions()


@router.get("/templates", response_model=list[WorkerTemplateRead])
def get_internal_templates(
    current_user: User = Depends(require_internal_worker_builder_access),
    db: Session = Depends(get_db),
):
    ensure_builtin_worker_templates(db)
    templates = list_internal_templates(db, workspace_id=current_user.workspace_id)
    db.commit()
    return templates


@router.post("/templates", response_model=WorkerTemplateRead)
def create_template(
    payload: InternalWorkerTemplateCreate,
    current_user: User = Depends(require_internal_worker_builder_access),
    db: Session = Depends(get_db),
):
    ensure_builtin_worker_templates(db)
    template = create_internal_template(db, workspace_id=current_user.workspace_id, payload=payload)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="internal_worker_template_created",
        payload={"template_id": str(template.id), "worker_type": template.worker_type, "template_key": template.template_key},
    )
    db.commit()
    db.refresh(template)
    return template


@router.post("/workers/from-template", response_model=WorkerRead)
def create_worker_from_internal_template(
    payload: InternalWorkerFromTemplateCreate,
    current_user: User = Depends(require_internal_worker_builder_access),
    db: Session = Depends(get_db),
):
    worker = create_worker_from_template(db, workspace_id=current_user.workspace_id, payload=payload)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="internal_worker_created_from_template",
        payload={"worker_id": str(worker.id), "template_id": str(payload.template_id), "worker_type": worker.worker_type},
    )
    db.commit()
    db.refresh(worker)
    return worker
