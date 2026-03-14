from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Worker, WorkerPricingType, WorkerTemplate, WorkerTemplateStatus, WorkerTemplateVisibility
from app.schemas.api import InternalWorkerFromTemplateCreate, InternalWorkerTemplateCreate, WorkerTemplateCreate
from app.services.worker_definitions import resolve_worker_definition
from app.services.worker_templates import create_worker_template, get_worker_template_details, list_worker_templates
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
    creator_user_id=None,
) -> WorkerTemplate:
    steps = [item.model_dump() for item in payload.steps]
    _validate_steps_and_actions(payload.allowed_actions, steps)

    definition = resolve_worker_definition(payload.worker_type)
    config_blob = {
        "config_defaults": payload.config_defaults,
        "mission_default": payload.mission_default or "",
        "execution_steps": steps,
    }
    template = create_worker_template(
        db,
        workspace_id=workspace_id,
        creator_user_id=creator_user_id,
        payload=WorkerTemplateCreate(
            name=payload.display_name,
            slug=None,
            short_description=None,
            description=None,
            category=payload.worker_category or definition.worker_category,
            worker_type=payload.worker_type,
            worker_category=payload.worker_category or definition.worker_category,
            visibility=WorkerTemplateVisibility.WORKSPACE,
            status=WorkerTemplateStatus.ACTIVE if payload.is_active else WorkerTemplateStatus.DRAFT,
            instructions=None,
            model_name=None,
            config_json=config_blob,
            capabilities_json={},
            actions_json=list(payload.allowed_actions),
            tools_json=[],
            memory_enabled=True,
            chain_enabled=False,
            is_marketplace_listed=False,
            pricing_type=WorkerPricingType.INTERNAL,
            price_cents=0,
            currency="USD",
            tags_json=[],
        ),
    )
    template.plan_version = payload.plan_version
    template.prompt_profile = payload.prompt_profile
    template.default_config_json = dict(config_blob)
    template.config_json = dict(config_blob)
    template.allowed_actions = list(payload.allowed_actions)
    template.actions_json = list(payload.allowed_actions)
    template.is_public = False
    template.is_active = payload.is_active
    template.status = WorkerTemplateStatus.ACTIVE.value if payload.is_active else WorkerTemplateStatus.DRAFT.value
    db.flush()
    return template


def list_internal_templates(db: Session, workspace_id) -> list[WorkerTemplate]:
    return list_worker_templates(
        db,
        workspace_id=workspace_id,
        include_workspace_templates=True,
        include_public_templates=False,
        include_global_non_public_templates=True,
        include_inactive=False,
    )


def create_worker_from_template(
    db: Session,
    workspace_id,
    payload: InternalWorkerFromTemplateCreate,
) -> Worker:
    template = get_worker_template_details(
        db,
        template_id=payload.template_id,
        workspace_id=workspace_id,
        include_public=False,
        include_global_non_public=True,
    )
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
