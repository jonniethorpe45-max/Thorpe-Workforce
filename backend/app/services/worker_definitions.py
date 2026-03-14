from typing import Any

from sqlalchemy.orm import Session

from app.models import WorkerTemplate
from app.workers.definitions import WorkerDefinition, get_worker_definition, list_worker_definitions


def ensure_builtin_worker_templates(db: Session) -> None:
    for definition in list_worker_definitions(include_internal=True):
        existing = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.template_key == definition.worker_type, WorkerTemplate.workspace_id.is_(None))
            .first()
        )
        if existing:
            existing.display_name = definition.display_name
            existing.worker_type = definition.worker_type
            existing.worker_category = definition.worker_category
            existing.plan_version = definition.plan_version
            existing.default_config_json = dict(definition.default_config)
            existing.allowed_actions = list(definition.allowed_actions)
            existing.prompt_profile = definition.prompt_profile
            existing.is_public = definition.public_available
            existing.is_active = True
            existing.workspace_id = None
            continue
        db.add(
            WorkerTemplate(
                workspace_id=None,
                template_key=definition.worker_type,
                display_name=definition.display_name,
                worker_type=definition.worker_type,
                worker_category=definition.worker_category,
                plan_version=definition.plan_version,
                default_config_json=dict(definition.default_config),
                allowed_actions=list(definition.allowed_actions),
                prompt_profile=definition.prompt_profile,
                is_public=definition.public_available,
                is_active=True,
            )
        )
    db.flush()


def resolve_worker_definition(worker_type: str) -> WorkerDefinition:
    return get_worker_definition(worker_type)


def build_worker_config(
    definition: WorkerDefinition,
    *,
    target_industry: str | None,
    target_roles: list[str],
    target_locations: list[str],
    company_size_range: str | None,
    extra_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(definition.default_config)
    merged.update(
        {
            "target_industry": target_industry,
            "target_roles": target_roles,
            "target_locations": target_locations,
            "company_size_range": company_size_range,
        }
    )
    if extra_config:
        merged.update(extra_config)
    return merged
