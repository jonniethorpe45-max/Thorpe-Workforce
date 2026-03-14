import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_worker_creator_access
from app.db.session import get_db
from app.models import User, WorkerTemplate
from app.schemas.api import (
    WorkerBuilderCategoryRead,
    WorkerDraftCreate,
    WorkerDraftCreateResponse,
    WorkerDraftListResponse,
    WorkerDraftPublishResponse,
    WorkerDraftRead,
    WorkerDraftTestRequest,
    WorkerDraftTestResponse,
    WorkerDraftUpdate,
    WorkerInstanceRead,
    WorkerTemplateInstallRequest,
)
from app.services.audit import log_audit_event
from app.services.worker_creator import (
    create_worker_draft,
    get_worker_draft,
    list_worker_drafts,
    publish_worker_draft,
    test_worker_draft,
    unpublish_worker_draft,
    update_worker_draft,
)
from app.services.worker_templates import install_worker_template

router = APIRouter(prefix="/workers/builder", tags=["worker_creator"])


@router.get("/categories", response_model=list[WorkerBuilderCategoryRead])
def list_categories(current_user: User = Depends(require_worker_creator_access)):
    _ = current_user
    return [
        {"key": "real_estate", "label": "Real Estate", "description": "Lead sourcing and listing intelligence workflows"},
        {"key": "marketing", "label": "Marketing", "description": "Campaign and content operations"},
        {"key": "finance", "label": "Finance", "description": "Financial research and operations assistants"},
        {"key": "sales", "label": "Sales", "description": "Outbound, pipeline, and follow-up assistants"},
        {"key": "ecommerce", "label": "E-commerce", "description": "Store operations and merchandising automation"},
        {"key": "content", "label": "Content", "description": "Content ideation and production assistants"},
        {"key": "research", "label": "Research", "description": "General web and data analysis workers"},
        {"key": "automation", "label": "Automation", "description": "Internal workflow automation workers"},
        {"key": "custom", "label": "Custom", "description": "General purpose custom worker"},
    ]


@router.post("/drafts", response_model=WorkerDraftCreateResponse)
def create_draft(
    payload: WorkerDraftCreate,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = create_worker_draft(
        db,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
        payload=payload,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_created",
        payload={"draft_id": str(draft.id)},
    )
    db.commit()
    db.refresh(draft)
    return WorkerDraftCreateResponse(worker_draft_id=draft.id, draft=draft)


@router.get("/drafts", response_model=WorkerDraftListResponse)
def list_drafts(current_user: User = Depends(require_worker_creator_access), db: Session = Depends(get_db)):
    drafts = list_worker_drafts(db, workspace_id=current_user.workspace_id, creator_user_id=current_user.id)
    return WorkerDraftListResponse(items=drafts, total=len(drafts))


@router.get("/drafts/{draft_id}", response_model=WorkerDraftRead)
def get_draft(draft_id: uuid.UUID, current_user: User = Depends(require_worker_creator_access), db: Session = Depends(get_db)):
    return get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )


@router.patch("/drafts/{draft_id}", response_model=WorkerDraftRead)
def patch_draft(
    draft_id: uuid.UUID,
    payload: WorkerDraftUpdate,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )
    updated = update_worker_draft(
        db,
        draft=draft,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
        payload=payload,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_updated",
        payload={"draft_id": str(draft_id)},
    )
    db.commit()
    db.refresh(updated)
    return updated


@router.post("/drafts/{draft_id}/test", response_model=WorkerDraftTestResponse)
def run_draft_test(
    draft_id: uuid.UUID,
    payload: WorkerDraftTestRequest,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )
    result = test_worker_draft(db, draft=draft, creator=current_user, payload=payload)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_tested",
        payload={"draft_id": str(draft_id), "run_id": str(result.run_id)},
    )
    db.commit()
    return result


@router.post("/drafts/{draft_id}/publish", response_model=WorkerDraftPublishResponse)
def publish_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )
    template = publish_worker_draft(db, draft=draft, creator=current_user)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_published",
        payload={"draft_id": str(draft_id), "template_id": str(template.id)},
    )
    db.commit()
    db.refresh(draft)
    db.refresh(template)
    return WorkerDraftPublishResponse(
        worker_draft_id=draft.id,
        published_template_id=template.id,
        is_published=draft.is_published,
        template=template,
    )


@router.post("/drafts/{draft_id}/unpublish", response_model=WorkerDraftPublishResponse)
def unpublish_draft(
    draft_id: uuid.UUID,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )
    template = unpublish_worker_draft(db, draft=draft, creator=current_user)
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_unpublished",
        payload={"draft_id": str(draft_id), "template_id": str(template.id)},
    )
    db.commit()
    db.refresh(draft)
    db.refresh(template)
    return WorkerDraftPublishResponse(
        worker_draft_id=draft.id,
        published_template_id=template.id,
        is_published=draft.is_published,
        template=template,
    )


@router.post("/drafts/{draft_id}/install", response_model=WorkerInstanceRead)
def install_published_draft(
    draft_id: uuid.UUID,
    payload: WorkerTemplateInstallRequest,
    current_user: User = Depends(require_worker_creator_access),
    db: Session = Depends(get_db),
):
    draft = get_worker_draft(
        db,
        draft_id=draft_id,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
    )
    if not draft.published_template_id:
        raise HTTPException(status_code=400, detail="Draft must be published before install")
    template = db.get(WorkerTemplate, draft.published_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Published template not found")
    result = install_worker_template(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        installer_user_id=current_user.id,
        instance_name=payload.instance_name,
        runtime_config_overrides=payload.runtime_config_overrides,
        schedule_expression=payload.schedule_expression,
        memory_scope=payload.memory_scope,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_creator_draft_installed",
        payload={"draft_id": str(draft_id), "instance_id": str(result.instance.id)},
    )
    db.commit()
    db.refresh(result.instance)
    return result.instance
