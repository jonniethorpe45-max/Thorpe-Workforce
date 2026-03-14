import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Campaign, User, Worker, WorkerInstance, WorkerInstanceStatus, WorkerRunStatus, WorkerStatus, WorkerTemplate
from app.schemas.api import (
    WorkerCreate,
    WorkerInstanceExecuteRequest,
    WorkerInstanceExecuteResponse,
    WorkerInstanceRead,
    WorkerInstanceUpdate,
    WorkerRead,
    WorkerRunRead,
    WorkerTemplateCreate,
    WorkerTemplateDuplicateRequest,
    WorkerTemplateInstallRequest,
    WorkerTemplatePublishRequest,
    WorkerTemplateRead,
    WorkerTemplateUpdate,
    WorkerUpdate,
)
from app.services.audit import log_audit_event
from app.services.billing import (
    ensure_creator_monetization_profile,
    require_marketplace_publish_access,
    require_paid_worker_entitlement,
    require_published_worker_capacity,
    require_template_visibility_access,
    require_worker_builder_access,
    require_worker_install_access,
    require_worker_run_access,
)
from app.services.worker_definitions import (
    build_worker_config,
    ensure_builtin_worker_templates,
    resolve_worker_definition,
)
from app.services.worker_execution import execute_worker_instance_run, queue_worker_instance_run
from app.services.worker_service import list_worker_runs, pause_worker, queue_worker_run, resume_worker, run_worker_for_campaign
from app.services.worker_templates import (
    create_worker_template,
    duplicate_worker_template,
    get_worker_template_details,
    install_worker_template,
    list_worker_templates as list_worker_templates_service,
    publish_worker_template,
    update_worker_template,
)
from app.tasks.dispatcher import enqueue_task
from app.tasks.jobs import execute_worker_instance_run_task, execute_worker_run_task

router = APIRouter(prefix="/workers", tags=["workers"])


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _get_workspace_instance(db: Session, *, instance_id: uuid.UUID, workspace_id: uuid.UUID) -> WorkerInstance:
    instance = db.get(WorkerInstance, instance_id)
    if not instance or instance.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Worker instance not found")
    return instance


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


@router.post("/templates", response_model=WorkerTemplateRead)
def create_template(
    payload: WorkerTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_worker_builder_access(db, workspace_id=current_user.workspace_id)
    require_template_visibility_access(
        db,
        workspace_id=current_user.workspace_id,
        visibility=_enum_value(payload.visibility),
    )
    ensure_builtin_worker_templates(db)
    template = create_worker_template(
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
        event_name="worker_template_created",
        payload={"template_id": str(template.id), "worker_type": template.worker_type},
    )
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates", response_model=list[WorkerTemplateRead])
def list_templates(
    include_public: bool = Query(default=True),
    worker_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_builtin_worker_templates(db)
    return list_worker_templates_service(
        db,
        workspace_id=current_user.workspace_id,
        include_workspace_templates=True,
        include_public_templates=include_public,
        include_global_non_public_templates=False,
        worker_type=worker_type,
    )


@router.get("/templates/library", response_model=list[WorkerTemplateRead])
def list_worker_templates_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_builtin_worker_templates(db)
    templates = list_worker_templates_service(
        db,
        workspace_id=current_user.workspace_id,
        include_workspace_templates=False,
        include_public_templates=True,
        include_global_non_public_templates=False,
    )
    db.commit()
    return templates


@router.get("/templates/{template_id}", response_model=WorkerTemplateRead)
def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_worker_template_details(
        db,
        template_id=template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )


@router.patch("/templates/{template_id}", response_model=WorkerTemplateRead)
def patch_template(
    template_id: uuid.UUID,
    payload: WorkerTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.get(WorkerTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    updated = update_worker_template(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        payload=payload,
    )
    db.commit()
    db.refresh(updated)
    return updated


@router.post("/templates/{template_id}/publish", response_model=WorkerTemplateRead)
def publish_template(
    template_id: uuid.UUID,
    payload: WorkerTemplatePublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.get(WorkerTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    visibility_value = _enum_value(payload.visibility)
    require_template_visibility_access(db, workspace_id=current_user.workspace_id, visibility=visibility_value)
    if visibility_value in {"public", "marketplace"}:
        require_published_worker_capacity(db, workspace_id=current_user.workspace_id)
    if visibility_value == "marketplace" or payload.is_marketplace_listed:
        require_marketplace_publish_access(db, workspace_id=current_user.workspace_id)
        ensure_creator_monetization_profile(db, user_id=current_user.id)
    published = publish_worker_template(
        db,
        template=template,
        workspace_id=current_user.workspace_id,
        payload=payload,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_template_published",
        payload={"template_id": str(template_id), "visibility": published.visibility},
    )
    db.commit()
    db.refresh(published)
    return published


@router.post("/templates/{template_id}/install", response_model=WorkerInstanceRead)
def install_template(
    template_id: uuid.UUID,
    payload: WorkerTemplateInstallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = get_worker_template_details(
        db,
        template_id=template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    require_worker_install_access(db, workspace_id=current_user.workspace_id)
    require_paid_worker_entitlement(
        db,
        workspace_id=current_user.workspace_id,
        worker_template=template,
    )
    install_result = install_worker_template(
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
        event_name="worker_template_installed",
        payload={"template_id": str(template_id), "instance_id": str(install_result.instance.id)},
    )
    db.commit()
    db.refresh(install_result.instance)
    return install_result.instance


@router.post("/templates/{template_id}/duplicate", response_model=WorkerTemplateRead)
def duplicate_template(
    template_id: uuid.UUID,
    payload: WorkerTemplateDuplicateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_template = get_worker_template_details(
        db,
        template_id=template_id,
        workspace_id=current_user.workspace_id,
        include_public=True,
        include_global_non_public=False,
    )
    duplicated = duplicate_worker_template(
        db,
        source_template=source_template,
        workspace_id=current_user.workspace_id,
        creator_user_id=current_user.id,
        name=payload.name,
        slug=payload.slug,
    )
    log_audit_event(
        db,
        workspace_id=current_user.workspace_id,
        actor_type="user",
        actor_id=str(current_user.id),
        event_name="worker_template_duplicated",
        payload={"source_template_id": str(template_id), "template_id": str(duplicated.id)},
    )
    db.commit()
    db.refresh(duplicated)
    return duplicated


@router.get("/instances", response_model=list[WorkerInstanceRead])
def list_instances(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(WorkerInstance)
        .filter(WorkerInstance.workspace_id == current_user.workspace_id)
        .order_by(WorkerInstance.created_at.desc())
        .all()
    )


@router.get("/instances/{instance_id}", response_model=WorkerInstanceRead)
def get_instance(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_workspace_instance(db, instance_id=instance_id, workspace_id=current_user.workspace_id)


@router.patch("/instances/{instance_id}", response_model=WorkerInstanceRead)
def patch_instance(
    instance_id: uuid.UUID,
    payload: WorkerInstanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id=instance_id, workspace_id=current_user.workspace_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/instances/{instance_id}/run", response_model=WorkerInstanceExecuteResponse)
def run_instance(
    instance_id: uuid.UUID,
    payload: WorkerInstanceExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id=instance_id, workspace_id=current_user.workspace_id)
    require_worker_run_access(db, workspace_id=current_user.workspace_id)
    template = db.get(WorkerTemplate, instance.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found for instance")
    require_paid_worker_entitlement(
        db,
        workspace_id=current_user.workspace_id,
        worker_template=template,
    )
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


@router.post("/instances/{instance_id}/pause", response_model=WorkerInstanceRead)
def pause_instance(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id=instance_id, workspace_id=current_user.workspace_id)
    instance.status = WorkerInstanceStatus.PAUSED.value
    instance.next_run_at = None
    db.commit()
    db.refresh(instance)
    return instance


@router.post("/instances/{instance_id}/resume", response_model=WorkerInstanceRead)
def resume_instance(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = _get_workspace_instance(db, instance_id=instance_id, workspace_id=current_user.workspace_id)
    instance.status = WorkerInstanceStatus.ACTIVE.value
    instance.next_run_at = datetime.now(UTC) + timedelta(minutes=60)
    db.commit()
    db.refresh(instance)
    return instance


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
    require_worker_run_access(db, workspace_id=current_user.workspace_id)
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
