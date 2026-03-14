import uuid
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    User,
    WorkerBuilderCategory,
    WorkerInstance,
    WorkerInstanceStatus,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerTemplate,
    WorkerTemplateDraft,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
)
from app.schemas.api import (
    WorkerDraftCreate,
    WorkerDraftTestRequest,
    WorkerDraftTestResponse,
    WorkerDraftUpdate,
    WorkerTemplateCreate,
    WorkerTemplatePublishRequest,
    normalize_slug,
)
from app.services.worker_execution import WorkerExecutionEngine
from app.services.worker_templates import create_worker_template, publish_worker_template, unpublish_worker_template

ALLOWED_DRAFT_TOOLS = {"web_search", "database_lookup", "file_access", "api_call"}


def _assert_draft_access(draft: WorkerTemplateDraft, *, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    if draft.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Worker draft not found")
    if draft.creator_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only draft owner can access this draft")


def _assert_slug_unique(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    slug: str,
    exclude_draft_id: uuid.UUID | None = None,
) -> None:
    query = db.query(WorkerTemplateDraft).filter(
        WorkerTemplateDraft.workspace_id == workspace_id,
        WorkerTemplateDraft.slug == slug,
    )
    if exclude_draft_id:
        query = query.filter(WorkerTemplateDraft.id != exclude_draft_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Worker draft slug already exists in this workspace")


def _validate_category(value: WorkerBuilderCategory | str) -> str:
    allowed = {item.value for item in WorkerBuilderCategory}
    candidate = value.value if isinstance(value, WorkerBuilderCategory) else str(value).strip().lower()
    if candidate not in allowed:
        raise HTTPException(status_code=400, detail="Invalid worker draft category")
    return candidate


def _validate_prompt(value: str) -> str:
    prompt = (value or "").strip()
    if len(prompt) < 20:
        raise HTTPException(status_code=400, detail="prompt_template must be at least 20 characters")
    if len(prompt) > 8000:
        raise HTTPException(status_code=400, detail="prompt_template is too long")
    return prompt


def _validate_schema(value: dict[str, Any] | None, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an object")
    return value


def _normalize_tools(value: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if value is None:
        return []
    cleaned: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Each tool must be an object")
        label = str(item.get("label", "")).strip()
        if label not in ALLOWED_DRAFT_TOOLS:
            raise HTTPException(status_code=400, detail=f"Unsupported tool label: {label}")
        cleaned.append(
            {
                "label": label,
                "enabled": bool(item.get("enabled", True)),
                "config": item.get("config", {}) if isinstance(item.get("config"), dict) else {},
            }
        )
    return cleaned


def _enabled_tool_labels(tools_json: list[dict[str, Any]] | None) -> list[str]:
    labels: list[str] = []
    for item in tools_json or []:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("enabled", True)):
            continue
        label = str(item.get("label", "")).strip()
        if label:
            labels.append(label)
    deduped: list[str] = []
    seen: set[str] = set()
    for label in labels:
        if label in seen:
            continue
        seen.add(label)
        deduped.append(label)
    return deduped


def _to_cents(value: Any) -> int:
    if value is None:
        return 0
    amount = Decimal(str(value))
    if amount <= 0:
        return 0
    return int((amount * 100).quantize(Decimal("1")))


def _pricing_from_draft(draft: WorkerTemplateDraft) -> tuple[str, int]:
    monthly = _to_cents(draft.price_monthly)
    one_time = _to_cents(draft.price_onetime)
    if monthly > 0:
        return WorkerPricingType.SUBSCRIPTION.value, monthly
    if one_time > 0:
        return WorkerPricingType.ONE_TIME.value, one_time
    return WorkerPricingType.FREE.value, 0


def create_worker_draft(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    creator_user_id: uuid.UUID,
    payload: WorkerDraftCreate,
) -> WorkerTemplateDraft:
    slug = normalize_slug(payload.slug or payload.name)
    if not slug:
        raise HTTPException(status_code=400, detail="Slug is required")
    _assert_slug_unique(db, workspace_id=workspace_id, slug=slug)
    draft = WorkerTemplateDraft(
        workspace_id=workspace_id,
        creator_user_id=creator_user_id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        category=_validate_category(payload.category),
        prompt_template=_validate_prompt(payload.prompt_template),
        input_schema_json=_validate_schema(payload.input_schema, "input_schema"),
        output_schema_json=_validate_schema(payload.output_schema, "output_schema"),
        tools_json=_normalize_tools(payload.tools),
        visibility=WorkerTemplateVisibility.PRIVATE.value,
        is_published=False,
        creator_revenue_percent=70.0,
        platform_revenue_percent=30.0,
        tags_json=[],
        screenshots_json=[],
        usage_examples_json=[],
    )
    db.add(draft)
    db.flush()
    return draft


def list_worker_drafts(db: Session, *, workspace_id: uuid.UUID, creator_user_id: uuid.UUID) -> list[WorkerTemplateDraft]:
    return (
        db.query(WorkerTemplateDraft)
        .filter(
            WorkerTemplateDraft.workspace_id == workspace_id,
            WorkerTemplateDraft.creator_user_id == creator_user_id,
        )
        .order_by(WorkerTemplateDraft.updated_at.desc())
        .all()
    )


def get_worker_draft(
    db: Session,
    *,
    draft_id: uuid.UUID,
    workspace_id: uuid.UUID,
    creator_user_id: uuid.UUID,
) -> WorkerTemplateDraft:
    draft = db.get(WorkerTemplateDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Worker draft not found")
    _assert_draft_access(draft, workspace_id=workspace_id, user_id=creator_user_id)
    return draft


def update_worker_draft(
    db: Session,
    *,
    draft: WorkerTemplateDraft,
    workspace_id: uuid.UUID,
    creator_user_id: uuid.UUID,
    payload: WorkerDraftUpdate,
) -> WorkerTemplateDraft:
    _assert_draft_access(draft, workspace_id=workspace_id, user_id=creator_user_id)
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"]:
        draft.name = str(updates["name"]).strip()
    if "slug" in updates:
        next_slug = normalize_slug(updates["slug"] or draft.name)
        if not next_slug:
            raise HTTPException(status_code=400, detail="Slug is required")
        _assert_slug_unique(db, workspace_id=workspace_id, slug=next_slug, exclude_draft_id=draft.id)
        draft.slug = next_slug
    if "description" in updates:
        draft.description = updates["description"]
    if "category" in updates and updates["category"] is not None:
        draft.category = _validate_category(updates["category"])
    if "prompt_template" in updates and updates["prompt_template"] is not None:
        draft.prompt_template = _validate_prompt(str(updates["prompt_template"]))
    if "input_schema" in updates:
        draft.input_schema_json = _validate_schema(updates["input_schema"], "input_schema")
    if "output_schema" in updates:
        draft.output_schema_json = _validate_schema(updates["output_schema"], "output_schema")
    if "tools" in updates:
        draft.tools_json = _normalize_tools(updates["tools"])
    if "visibility" in updates and updates["visibility"] is not None:
        visibility = updates["visibility"]
        draft.visibility = visibility.value if isinstance(visibility, WorkerTemplateVisibility) else str(visibility)
    if "price_monthly" in updates:
        draft.price_monthly = updates["price_monthly"]
    if "price_onetime" in updates:
        draft.price_onetime = updates["price_onetime"]
    if "icon" in updates:
        draft.icon = updates["icon"]
    if "screenshots" in updates:
        draft.screenshots_json = list(updates["screenshots"] or [])
    if "tags" in updates:
        draft.tags_json = list(updates["tags"] or [])
    if "usage_examples" in updates:
        draft.usage_examples_json = list(updates["usage_examples"] or [])
    if "creator_revenue_percent" in updates and updates["creator_revenue_percent"] is not None:
        draft.creator_revenue_percent = updates["creator_revenue_percent"]
    if "platform_revenue_percent" in updates and updates["platform_revenue_percent"] is not None:
        draft.platform_revenue_percent = updates["platform_revenue_percent"]

    if abs(float(draft.creator_revenue_percent) + float(draft.platform_revenue_percent) - 100.0) > 0.001:
        raise HTTPException(status_code=400, detail="creator_revenue_percent and platform_revenue_percent must total 100")
    db.flush()
    return draft


def _ensure_draft_test_template(db: Session, *, draft: WorkerTemplateDraft, creator: User) -> WorkerTemplate:
    if draft.published_template_id:
        published = db.get(WorkerTemplate, draft.published_template_id)
        if published and published.workspace_id == draft.workspace_id:
            return published

    template_key = f"draft-test-{draft.id.hex[:24]}"
    existing = (
        db.query(WorkerTemplate)
        .filter(
            WorkerTemplate.workspace_id == draft.workspace_id,
            WorkerTemplate.template_key == template_key,
        )
        .first()
    )
    if existing:
        existing.name = f"{draft.name} (Draft Test)"
        existing.display_name = existing.name
        existing.short_description = (draft.description or "")[:255] or "Draft test template"
        existing.description = draft.description
        existing.category = draft.category
        existing.worker_category = draft.category
        existing.instructions = draft.prompt_template
        existing.config_json = {"draft_id": str(draft.id), "source": "builder_test", "input_schema": draft.input_schema_json or {}}
        existing.default_config_json = dict(existing.config_json)
        existing.capabilities_json = {"output_schema": draft.output_schema_json or {}}
        existing.tools_json = _enabled_tool_labels(draft.tools_json)
        existing.actions_json = ["monitor_outbound_events"]
        existing.allowed_actions = list(existing.actions_json)
        existing.visibility = WorkerTemplateVisibility.WORKSPACE.value
        existing.status = WorkerTemplateStatus.ACTIVE.value
        existing.is_public = False
        existing.is_marketplace_listed = False
        existing.pricing_type = WorkerPricingType.INTERNAL.value
        existing.price_cents = 0
        existing.currency = "USD"
        existing.icon = draft.icon
        existing.screenshots_json = list(draft.screenshots_json or [])
        existing.usage_examples_json = list(draft.usage_examples_json or [])
        existing.tags_json = list(draft.tags_json or [])
        existing.creator_revenue_percent = draft.creator_revenue_percent
        existing.platform_revenue_percent = draft.platform_revenue_percent
        db.flush()
        return existing

    payload = WorkerTemplateCreate(
        name=f"{draft.name} (Draft Test)",
        slug=None,
        short_description=(draft.description or "")[:255] or "Draft test template",
        description=draft.description,
        category=draft.category,
        worker_type="custom_worker",
        worker_category=draft.category,
        visibility=WorkerTemplateVisibility.WORKSPACE,
        status=WorkerTemplateStatus.ACTIVE,
        instructions=draft.prompt_template,
        model_name="mock-ai-v1",
        config_json={"draft_id": str(draft.id), "source": "builder_test", "input_schema": draft.input_schema_json or {}},
        capabilities_json={"output_schema": draft.output_schema_json or {}},
        actions_json=["monitor_outbound_events"],
        tools_json=_enabled_tool_labels(draft.tools_json),
        memory_enabled=True,
        chain_enabled=True,
        is_marketplace_listed=False,
        pricing_type=WorkerPricingType.INTERNAL,
        price_cents=0,
        currency="USD",
        icon=draft.icon,
        screenshots_json=list(draft.screenshots_json or []),
        usage_examples_json=list(draft.usage_examples_json or []),
        creator_revenue_percent=float(draft.creator_revenue_percent),
        platform_revenue_percent=float(draft.platform_revenue_percent),
        tags_json=list(draft.tags_json or []),
    )
    template = create_worker_template(
        db,
        workspace_id=draft.workspace_id,
        creator_user_id=creator.id,
        payload=payload,
    )
    template.template_key = template_key
    db.flush()
    return template


def test_worker_draft(
    db: Session,
    *,
    draft: WorkerTemplateDraft,
    creator: User,
    payload: WorkerDraftTestRequest,
) -> WorkerDraftTestResponse:
    _assert_draft_access(draft, workspace_id=creator.workspace_id, user_id=creator.id)
    template = _ensure_draft_test_template(db, draft=draft, creator=creator)
    instance = WorkerInstance(
        workspace_id=creator.workspace_id,
        template_id=template.id,
        owner_user_id=creator.id,
        name=f"Draft Test Instance {draft.name}",
        status=WorkerInstanceStatus.ACTIVE.value,
        runtime_config_json={"draft_id": str(draft.id), "mode": "test"},
        memory_scope=WorkerMemoryScope.INSTANCE.value,
    )
    db.add(instance)
    db.flush()
    engine = WorkerExecutionEngine()
    context = engine.build_execution_context(
        db,
        instance=instance,
        runtime_input=payload.inputs,
        trigger_source=f"draft_test:{draft.id}",
    )
    rendered_prompt = engine.assemble_worker_prompt(context)
    context.prompt = rendered_prompt
    run = engine.execute_context(context)
    output = run.output_json if isinstance(run.output_json, dict) else {}
    normalized = output.get("output", {}) if isinstance(output.get("output"), dict) else {}
    return WorkerDraftTestResponse(
        worker_draft_id=draft.id,
        run_id=run.id,
        status=run.status,
        rendered_prompt=rendered_prompt,
        execution_result=output,
        normalized_output=normalized,
    )


def publish_worker_draft(db: Session, *, draft: WorkerTemplateDraft, creator: User) -> WorkerTemplate:
    _assert_draft_access(draft, workspace_id=creator.workspace_id, user_id=creator.id)
    if not draft.description or len(draft.description.strip()) < 20:
        raise HTTPException(status_code=400, detail="description must be at least 20 characters before publish")
    if not draft.prompt_template or len(draft.prompt_template.strip()) < 20:
        raise HTTPException(status_code=400, detail="prompt_template must be at least 20 characters before publish")
    pricing_type, price_cents = _pricing_from_draft(draft)
    visibility = draft.visibility or WorkerTemplateVisibility.PRIVATE.value
    is_marketplace = visibility == WorkerTemplateVisibility.MARKETPLACE.value
    template = db.get(WorkerTemplate, draft.published_template_id) if draft.published_template_id else None
    if template and template.workspace_id != draft.workspace_id:
        template = None

    if not template:
        create_payload = WorkerTemplateCreate(
            name=draft.name,
            slug=draft.slug,
            short_description=(draft.description or "")[:255],
            description=draft.description,
            category=draft.category,
            worker_type="custom_worker",
            worker_category=draft.category,
            visibility=visibility,
            status=WorkerTemplateStatus.DRAFT,
            instructions=draft.prompt_template,
            model_name="mock-ai-v1",
            config_json={"draft_id": str(draft.id), "input_schema": draft.input_schema_json or {}},
            capabilities_json={"output_schema": draft.output_schema_json or {}},
            actions_json=["monitor_outbound_events"],
            tools_json=_enabled_tool_labels(draft.tools_json),
            memory_enabled=True,
            chain_enabled=True,
            is_marketplace_listed=is_marketplace,
            pricing_type=pricing_type,
            price_cents=price_cents,
            currency="USD",
            icon=draft.icon,
            screenshots_json=list(draft.screenshots_json or []),
            usage_examples_json=list(draft.usage_examples_json or []),
            creator_revenue_percent=float(draft.creator_revenue_percent),
            platform_revenue_percent=float(draft.platform_revenue_percent),
            tags_json=list(draft.tags_json or []),
        )
        template = create_worker_template(
            db,
            workspace_id=draft.workspace_id,
            creator_user_id=creator.id,
            payload=create_payload,
        )
    else:
        template.name = draft.name
        template.display_name = draft.name
        template.slug = draft.slug
        template.short_description = (draft.description or "")[:255]
        template.description = draft.description
        template.category = draft.category
        template.worker_type = "custom_worker"
        template.worker_category = draft.category
        template.instructions = draft.prompt_template
        template.model_name = template.model_name or "mock-ai-v1"
        template.config_json = {"draft_id": str(draft.id), "input_schema": draft.input_schema_json or {}}
        template.default_config_json = dict(template.config_json)
        template.capabilities_json = {"output_schema": draft.output_schema_json or {}}
        template.actions_json = ["monitor_outbound_events"]
        template.allowed_actions = list(template.actions_json)
        template.tools_json = _enabled_tool_labels(draft.tools_json)
        template.visibility = visibility
        template.pricing_type = pricing_type
        template.price_cents = price_cents
        template.currency = "USD"
        template.icon = draft.icon
        template.screenshots_json = list(draft.screenshots_json or [])
        template.usage_examples_json = list(draft.usage_examples_json or [])
        template.creator_revenue_percent = draft.creator_revenue_percent
        template.platform_revenue_percent = draft.platform_revenue_percent
        template.tags_json = list(draft.tags_json or [])
        template.is_marketplace_listed = is_marketplace
        db.flush()

    publish_payload = WorkerTemplatePublishRequest(
        name=template.name,
        slug=template.slug or draft.slug,
        description=template.description or draft.description or "",
        instructions=template.instructions or draft.prompt_template,
        model_name=template.model_name or "mock-ai-v1",
        config_json=dict(template.config_json or {}),
        visibility=visibility,
        is_marketplace_listed=is_marketplace,
        pricing_type=pricing_type,
        price_cents=price_cents,
        currency="USD",
        icon=template.icon,
        screenshots_json=list(template.screenshots_json or []),
        usage_examples_json=list(template.usage_examples_json or []),
    )
    published = publish_worker_template(
        db,
        template=template,
        workspace_id=draft.workspace_id,
        payload=publish_payload,
    )
    draft.published_template_id = published.id
    draft.is_published = True
    db.flush()
    return published


def unpublish_worker_draft(db: Session, *, draft: WorkerTemplateDraft, creator: User) -> WorkerTemplate:
    _assert_draft_access(draft, workspace_id=creator.workspace_id, user_id=creator.id)
    if not draft.published_template_id:
        raise HTTPException(status_code=400, detail="Draft has not been published yet")
    template = db.get(WorkerTemplate, draft.published_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Published template not found")
    result = unpublish_worker_template(db, template=template, workspace_id=draft.workspace_id, archive=False)
    draft.is_published = False
    db.flush()
    return result
