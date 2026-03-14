import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Worker, WorkerTemplate
from app.schemas.api import InternalWorkerFromTemplateCreate, InternalWorkerTemplateCreate
from app.services.worker_definitions import resolve_worker_definition
from app.workers.actions import ACTION_CATALOG, list_action_catalog


def _validate_steps_and_actions(allowed_actions: list[str], steps: list[dict[str, Any]]) -> None:
    catalog_keys = set(ACTION_CATALOG.keys())
    unknown_allowed = sorted(set(allowed_actions) - catalog_keys)
    if unknown_allowed:
        raise HTTPException(status_code=400, detail=f"Unknown allowed_actions: {unknown_allowed}")

    for step in steps:
        action_key = str(step.get("action_key", "")).strip()
        if action_key not in catalog_keys:
            raise HTTPException(status_code=400, detail=f"Unknown action_key in step: {action_key}")
        if action_key not in allowed_actions:
            raise HTTPException(status_code=400, detail=f"Step action not permitted: {action_key}")


def list_builder_actions() -> list[dict[str, str]]:
    return list_action_catalog()


def create_internal_template(
    db: Session,
    workspace_id,
    payload: InternalWorkerTemplateCreate,
) -> WorkerTemplate:
    steps = [item.model_dump() for item in payload.steps]
    _validate_steps_and_actions(payload.allowed_actions, steps)

    definition = resolve_worker_definition(payload.worker_type)
    template_key = f"ws-{workspace_id}-{payload.display_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    template = WorkerTemplate(
        workspace_id=workspace_id,
        template_key=template_key,
        display_name=payload.display_name,
        worker_type=payload.worker_type,
        worker_category=payload.worker_category or definition.worker_category,
        plan_version=payload.plan_version,
        default_config_json={
            "config_defaults": payload.config_defaults,
            "mission_default": payload.mission_default or "",
            "execution_steps": steps,
        },
        allowed_actions=payload.allowed_actions,
        prompt_profile=payload.prompt_profile,
        is_public=False,
        is_active=payload.is_active,
    )
    db.add(template)
    db.flush()
    return template


def list_internal_templates(db: Session, workspace_id) -> list[WorkerTemplate]:
    return (
        db.query(WorkerTemplate)
        .filter(
            WorkerTemplate.is_active.is_(True),
            or_(WorkerTemplate.workspace_id == workspace_id, WorkerTemplate.workspace_id.is_(None)),
        )
        .order_by(WorkerTemplate.workspace_id.desc(), WorkerTemplate.created_at.desc())
        .all()
    )


def create_worker_from_template(
    db: Session,
    workspace_id,
    payload: InternalWorkerFromTemplateCreate,
) -> Worker:
    template = db.get(WorkerTemplate, payload.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    if template.workspace_id and template.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Template not available for this workspace")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template is not active")

    template_defaults = template.default_config_json if isinstance(template.default_config_json, dict) else {}
    config_defaults = template_defaults.get("config_defaults", {})
    if not isinstance(config_defaults, dict):
        config_defaults = {}
    execution_steps = template_defaults.get("execution_steps", [])
    if not isinstance(execution_steps, list):
        execution_steps = []

    allowed_actions = template.allowed_actions if isinstance(template.allowed_actions, list) else []
    _validate_steps_and_actions(allowed_actions, execution_steps)

    definition = resolve_worker_definition(template.worker_type)
    config_json = {
        **config_defaults,
        **payload.config_overrides,
        "execution_steps": execution_steps,
        "template_key": template.template_key,
    }
    worker = Worker(
        workspace_id=workspace_id,
        name=payload.name,
        worker_type=template.worker_type,
        worker_category=template.worker_category or definition.worker_category,
        mission=payload.mission,
        goal=payload.mission,
        plan_version=template.plan_version or definition.plan_version,
        allowed_actions=allowed_actions,
        template_id=template.id,
        origin_type="custom",
        is_custom_worker=True,
        is_internal=True,
        status="idle",
        tone=payload.tone,
        send_limit_per_day=payload.daily_send_limit,
        run_interval_minutes=max(payload.run_interval_minutes, 15),
        next_run_at=datetime.now(UTC) + timedelta(minutes=max(payload.run_interval_minutes, 15)),
        config_json=config_json,
    )
    db.add(worker)
    db.flush()
    return worker
