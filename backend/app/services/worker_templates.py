import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import (
    WorkerInstance,
    WorkerInstanceStatus,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerSubscription,
    WorkerTemplate,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
)
from app.schemas.api import WorkerTemplateCreate, WorkerTemplatePublishRequest, WorkerTemplateUpdate, normalize_slug

PUBLIC_VISIBILITY_VALUES = {
    WorkerTemplateVisibility.PUBLIC.value,
    WorkerTemplateVisibility.MARKETPLACE.value,
}
MARKETPLACE_VISIBILITY_VALUES = {WorkerTemplateVisibility.MARKETPLACE.value}


@dataclass(frozen=True)
class TemplatePublishReadiness:
    is_ready: bool
    errors: list[str]


@dataclass(frozen=True)
class TemplateInstallResult:
    instance: WorkerInstance
    subscription: WorkerSubscription | None
    install_count_incremented: bool


def _visibility_value(value: WorkerTemplateVisibility | str | None) -> str:
    if isinstance(value, WorkerTemplateVisibility):
        return value.value
    return str(value or WorkerTemplateVisibility.WORKSPACE.value)


def _status_value(value: WorkerTemplateStatus | str | None) -> str:
    if isinstance(value, WorkerTemplateStatus):
        return value.value
    return str(value or WorkerTemplateStatus.DRAFT.value)


def _pricing_value(value: WorkerPricingType | str | None) -> str:
    if isinstance(value, WorkerPricingType):
        return value.value
    return str(value or WorkerPricingType.INTERNAL.value)


def _is_publicly_visible(template: WorkerTemplate) -> bool:
    if not template.is_active:
        return False
    if template.status != WorkerTemplateStatus.ACTIVE.value:
        return False
    return template.visibility in PUBLIC_VISIBILITY_VALUES or bool(template.is_public)


def _is_marketplace_visible(template: WorkerTemplate) -> bool:
    if not _is_publicly_visible(template):
        return False
    if template.is_marketplace_listed:
        return True
    return template.visibility in MARKETPLACE_VISIBILITY_VALUES


def _assert_slug_unique(
    db: Session,
    *,
    slug: str | None,
    workspace_id: uuid.UUID | None,
    exclude_template_id: uuid.UUID | None = None,
) -> None:
    if not slug:
        return
    query = db.query(WorkerTemplate).filter(WorkerTemplate.slug == slug)
    if workspace_id is None:
        query = query.filter(WorkerTemplate.workspace_id.is_(None))
    else:
        query = query.filter(WorkerTemplate.workspace_id == workspace_id)
    if exclude_template_id:
        query = query.filter(WorkerTemplate.id != exclude_template_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Template slug already exists in this scope")


def _derive_public_flags(visibility: str, *, is_marketplace_listed: bool) -> tuple[bool, bool]:
    public = visibility in PUBLIC_VISIBILITY_VALUES
    marketplace = is_marketplace_listed or visibility in MARKETPLACE_VISIBILITY_VALUES
    return public, marketplace


def _derive_is_active(status: str) -> bool:
    return status != WorkerTemplateStatus.ARCHIVED.value


def _generate_template_key(
    *,
    worker_type: str,
    workspace_id: uuid.UUID | None,
    slug: str | None,
    name: str,
) -> str:
    base = normalize_slug(slug or name) or worker_type
    scope = "global" if workspace_id is None else str(workspace_id).split("-")[0]
    suffix = uuid.uuid4().hex[:8]
    prefix = f"{scope}-{worker_type}-"
    max_base_len = max(8, 80 - len(prefix) - len(suffix) - 1)
    safe_base = base[:max_base_len]
    return f"{prefix}{safe_base}-{suffix}"


def _assert_owned_template_access(template: WorkerTemplate, workspace_id: uuid.UUID) -> None:
    if template.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Template does not belong to this workspace")


def _assert_can_view_template(
    template: WorkerTemplate,
    *,
    workspace_id: uuid.UUID | None,
    include_public: bool,
    include_global_non_public: bool,
) -> None:
    if workspace_id and template.workspace_id == workspace_id:
        return
    if include_global_non_public and template.workspace_id is None:
        return
    if include_public and _is_publicly_visible(template):
        return
    raise HTTPException(status_code=404, detail="Worker template not found")


def create_worker_template(
    db: Session,
    *,
    workspace_id: uuid.UUID | None,
    creator_user_id: uuid.UUID | None,
    payload: WorkerTemplateCreate,
    is_system_template: bool = False,
) -> WorkerTemplate:
    slug = payload.slug
    _assert_slug_unique(db, slug=slug, workspace_id=workspace_id)

    visibility = _visibility_value(payload.visibility)
    status = _status_value(payload.status)
    pricing_type = _pricing_value(payload.pricing_type)
    is_public, is_marketplace_listed = _derive_public_flags(
        visibility,
        is_marketplace_listed=payload.is_marketplace_listed,
    )
    template = WorkerTemplate(
        workspace_id=workspace_id,
        creator_user_id=creator_user_id,
        name=payload.name,
        slug=slug,
        template_key=_generate_template_key(
            worker_type=payload.worker_type,
            workspace_id=workspace_id,
            slug=slug,
            name=payload.name,
        ),
        display_name=payload.name,
        short_description=payload.short_description,
        description=payload.description,
        category=payload.category,
        worker_type=payload.worker_type,
        worker_category=payload.worker_category,
        plan_version="v1",
        visibility=visibility,
        status=status,
        instructions=payload.instructions,
        model_name=payload.model_name,
        default_config_json=dict(payload.config_json),
        config_json=dict(payload.config_json),
        capabilities_json=dict(payload.capabilities_json),
        allowed_actions=list(payload.actions_json),
        actions_json=list(payload.actions_json),
        tools_json=list(payload.tools_json),
        memory_enabled=payload.memory_enabled,
        chain_enabled=payload.chain_enabled,
        is_system_template=is_system_template,
        is_public=is_public,
        is_marketplace_listed=is_marketplace_listed,
        is_active=_derive_is_active(status),
        pricing_type=pricing_type,
        price_cents=payload.price_cents,
        currency=payload.currency.upper(),
        icon=payload.icon,
        screenshots_json=list(payload.screenshots_json),
        usage_examples_json=list(payload.usage_examples_json),
        creator_revenue_percent=payload.creator_revenue_percent,
        platform_revenue_percent=payload.platform_revenue_percent,
        install_count=0,
        rating_avg=0.0,
        rating_count=0,
        tags_json=list(payload.tags_json),
    )
    db.add(template)
    db.flush()
    return template


def update_worker_template(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    payload: WorkerTemplateUpdate,
) -> WorkerTemplate:
    _assert_owned_template_access(template, workspace_id)
    updates = payload.model_dump(exclude_unset=True)

    if "slug" in updates:
        _assert_slug_unique(db, slug=updates["slug"], workspace_id=workspace_id, exclude_template_id=template.id)

    for field in [
        "name",
        "slug",
        "short_description",
        "description",
        "category",
        "worker_category",
        "instructions",
        "model_name",
        "config_json",
        "capabilities_json",
        "actions_json",
        "tools_json",
        "memory_enabled",
        "chain_enabled",
        "price_cents",
        "currency",
        "icon",
        "screenshots_json",
        "usage_examples_json",
        "creator_revenue_percent",
        "platform_revenue_percent",
        "tags_json",
    ]:
        if field in updates:
            setattr(template, field, updates[field])

    if "name" in updates and updates["name"]:
        template.display_name = updates["name"]
    if "config_json" in updates and isinstance(template.config_json, dict):
        template.default_config_json = dict(template.config_json)
    if "actions_json" in updates and isinstance(template.actions_json, list):
        template.allowed_actions = list(template.actions_json)
    if "currency" in updates and template.currency:
        template.currency = template.currency.upper()

    if "pricing_type" in updates:
        template.pricing_type = _pricing_value(updates["pricing_type"])
    if template.pricing_type == WorkerPricingType.FREE.value:
        template.price_cents = 0

    if "status" in updates:
        template.status = _status_value(updates["status"])
    if "visibility" in updates:
        template.visibility = _visibility_value(updates["visibility"])
    if "is_marketplace_listed" in updates:
        template.is_marketplace_listed = bool(updates["is_marketplace_listed"])

    template.is_active = _derive_is_active(template.status)
    template.is_public, template.is_marketplace_listed = _derive_public_flags(
        template.visibility,
        is_marketplace_listed=template.is_marketplace_listed,
    )
    db.flush()
    return template


def duplicate_worker_template(
    db: Session,
    *,
    source_template: WorkerTemplate,
    workspace_id: uuid.UUID,
    creator_user_id: uuid.UUID,
    name: str | None = None,
    slug: str | None = None,
) -> WorkerTemplate:
    copy_name = (name or f"{source_template.name or source_template.display_name} Copy").strip()
    copy_slug = normalize_slug(slug or f"{copy_name}-{uuid.uuid4().hex[:4]}")
    _assert_slug_unique(db, slug=copy_slug, workspace_id=workspace_id)

    duplicate = WorkerTemplate(
        workspace_id=workspace_id,
        creator_user_id=creator_user_id,
        name=copy_name,
        slug=copy_slug,
        template_key=_generate_template_key(
            worker_type=source_template.worker_type,
            workspace_id=workspace_id,
            slug=copy_slug,
            name=copy_name,
        ),
        display_name=copy_name,
        short_description=source_template.short_description,
        description=source_template.description,
        category=source_template.category,
        worker_type=source_template.worker_type,
        worker_category=source_template.worker_category,
        plan_version=source_template.plan_version,
        visibility=WorkerTemplateVisibility.WORKSPACE.value,
        status=WorkerTemplateStatus.DRAFT.value,
        instructions=source_template.instructions,
        model_name=source_template.model_name,
        default_config_json=dict(source_template.default_config_json or {}),
        config_json=dict(source_template.config_json or {}),
        capabilities_json=dict(source_template.capabilities_json or {}),
        allowed_actions=list(source_template.allowed_actions or []),
        actions_json=list(source_template.actions_json or []),
        tools_json=list(source_template.tools_json or []),
        prompt_profile=source_template.prompt_profile,
        memory_enabled=source_template.memory_enabled,
        chain_enabled=source_template.chain_enabled,
        is_system_template=False,
        is_public=False,
        is_marketplace_listed=False,
        is_active=True,
        pricing_type=source_template.pricing_type,
        price_cents=source_template.price_cents if source_template.pricing_type != WorkerPricingType.FREE.value else 0,
        currency=(source_template.currency or "USD").upper(),
        icon=source_template.icon,
        screenshots_json=list(source_template.screenshots_json or []),
        usage_examples_json=list(source_template.usage_examples_json or []),
        creator_revenue_percent=source_template.creator_revenue_percent,
        platform_revenue_percent=source_template.platform_revenue_percent,
        install_count=0,
        rating_avg=0.0,
        rating_count=0,
        tags_json=list(source_template.tags_json or []),
    )
    db.add(duplicate)
    db.flush()
    return duplicate


def validate_template_publish_readiness(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    payload: WorkerTemplatePublishRequest | None = None,
) -> TemplatePublishReadiness:
    _assert_owned_template_access(template, workspace_id)

    candidate = {
        "name": (payload.name if payload else template.name) or template.display_name or "",
        "slug": payload.slug if payload else template.slug,
        "description": payload.description if payload else template.description,
        "instructions": payload.instructions if payload else template.instructions,
        "model_name": payload.model_name if payload else template.model_name,
        "config_json": payload.config_json if payload else template.config_json,
        "visibility": _visibility_value(payload.visibility if payload else template.visibility),
        "pricing_type": _pricing_value(payload.pricing_type if payload else template.pricing_type),
        "price_cents": payload.price_cents if payload else template.price_cents,
        "is_marketplace_listed": payload.is_marketplace_listed if payload else template.is_marketplace_listed,
    }

    errors: list[str] = []
    if not candidate["name"] or len(str(candidate["name"]).strip()) < 2:
        errors.append("name is required")
    if not candidate["slug"]:
        errors.append("slug is required")
    else:
        try:
            _assert_slug_unique(
                db,
                slug=str(candidate["slug"]),
                workspace_id=workspace_id,
                exclude_template_id=template.id,
            )
        except HTTPException:
            errors.append("slug must be unique within workspace")
        if candidate["visibility"] in PUBLIC_VISIBILITY_VALUES:
            public_slug_conflict = (
                db.query(WorkerTemplate)
                .filter(
                    WorkerTemplate.slug == str(candidate["slug"]),
                    WorkerTemplate.id != template.id,
                    or_(
                        WorkerTemplate.visibility.in_(tuple(PUBLIC_VISIBILITY_VALUES)),
                        WorkerTemplate.is_public.is_(True),
                    ),
                )
                .first()
            )
            if public_slug_conflict:
                errors.append("slug must be globally unique for public templates")
    if not candidate["description"] or len(str(candidate["description"]).strip()) < 20:
        errors.append("description must be at least 20 characters")
    if not candidate["instructions"] or len(str(candidate["instructions"]).strip()) < 20:
        errors.append("instructions must be at least 20 characters")
    if not candidate["model_name"] or len(str(candidate["model_name"]).strip()) < 2:
        errors.append("model_name is required")
    if not isinstance(candidate["config_json"], dict) or len(candidate["config_json"]) == 0:
        errors.append("config_json must contain meaningful configuration")
    if candidate["is_marketplace_listed"] and candidate["pricing_type"] != WorkerPricingType.FREE.value:
        if int(candidate["price_cents"] or 0) <= 0:
            errors.append("paid marketplace templates require price_cents > 0")

    return TemplatePublishReadiness(is_ready=len(errors) == 0, errors=errors)


def publish_worker_template(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    payload: WorkerTemplatePublishRequest,
) -> WorkerTemplate:
    readiness = validate_template_publish_readiness(db, template=template, workspace_id=workspace_id, payload=payload)
    if not readiness.is_ready:
        raise HTTPException(status_code=400, detail={"message": "Template is not publish-ready", "errors": readiness.errors})

    with db.begin_nested():
        template.name = payload.name
        template.display_name = payload.name
        template.slug = payload.slug
        template.description = payload.description
        template.instructions = payload.instructions
        template.model_name = payload.model_name
        template.config_json = dict(payload.config_json)
        template.default_config_json = dict(payload.config_json)
        template.visibility = _visibility_value(payload.visibility)
        template.status = WorkerTemplateStatus.ACTIVE.value
        template.pricing_type = _pricing_value(payload.pricing_type)
        template.price_cents = payload.price_cents
        template.currency = payload.currency.upper()
        template.is_marketplace_listed = bool(payload.is_marketplace_listed)
        template.icon = payload.icon
        template.screenshots_json = list(payload.screenshots_json)
        template.usage_examples_json = list(payload.usage_examples_json)
        if template.pricing_type == WorkerPricingType.FREE.value:
            template.price_cents = 0
        template.is_active = True
        template.is_public, template.is_marketplace_listed = _derive_public_flags(
            template.visibility,
            is_marketplace_listed=template.is_marketplace_listed,
        )
        db.flush()
    return template


def unpublish_worker_template(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    archive: bool = False,
) -> WorkerTemplate:
    _assert_owned_template_access(template, workspace_id)
    with db.begin_nested():
        template.visibility = WorkerTemplateVisibility.WORKSPACE.value
        template.is_public = False
        template.is_marketplace_listed = False
        template.status = WorkerTemplateStatus.ARCHIVED.value if archive else WorkerTemplateStatus.DRAFT.value
        template.is_active = _derive_is_active(template.status)
        db.flush()
    return template


def get_worker_template_details(
    db: Session,
    *,
    template_id: uuid.UUID | None = None,
    slug: str | None = None,
    workspace_id: uuid.UUID | None = None,
    include_public: bool = True,
    include_global_non_public: bool = False,
) -> WorkerTemplate:
    if not template_id and not slug:
        raise HTTPException(status_code=400, detail="template_id or slug is required")

    query = db.query(WorkerTemplate)
    if template_id:
        template = query.filter(WorkerTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Worker template not found")
        _assert_can_view_template(
            template,
            workspace_id=workspace_id,
            include_public=include_public,
            include_global_non_public=include_global_non_public,
        )
        return template

    normalized_slug = normalize_slug(slug or "")
    candidates = query.filter(WorkerTemplate.slug == normalized_slug).all()
    if not candidates:
        raise HTTPException(status_code=404, detail="Worker template not found")
    for candidate in candidates:
        try:
            _assert_can_view_template(
                candidate,
                workspace_id=workspace_id,
                include_public=include_public,
                include_global_non_public=include_global_non_public,
            )
            return candidate
        except HTTPException:
            continue
    raise HTTPException(status_code=404, detail="Worker template not found")


def list_worker_templates(
    db: Session,
    *,
    workspace_id: uuid.UUID | None,
    include_workspace_templates: bool = True,
    include_public_templates: bool = True,
    include_global_non_public_templates: bool = False,
    marketplace_only: bool = False,
    include_inactive: bool = False,
    worker_type: str | None = None,
) -> list[WorkerTemplate]:
    filters: list[Any] = []
    audience_filters: list[Any] = []

    if include_workspace_templates and workspace_id is not None:
        audience_filters.append(WorkerTemplate.workspace_id == workspace_id)

    if include_global_non_public_templates:
        audience_filters.append(WorkerTemplate.workspace_id.is_(None))

    if include_public_templates:
        public_filter = and_(
            or_(
                WorkerTemplate.visibility.in_(tuple(PUBLIC_VISIBILITY_VALUES)),
                WorkerTemplate.is_public.is_(True),  # compatibility for older records
            ),
            WorkerTemplate.status == WorkerTemplateStatus.ACTIVE.value,
        )
        audience_filters.append(public_filter)

    if not audience_filters:
        return []

    filters.append(or_(*audience_filters))
    if worker_type:
        filters.append(WorkerTemplate.worker_type == worker_type)
    if not include_inactive:
        filters.append(WorkerTemplate.is_active.is_(True))
    if marketplace_only:
        filters.append(
            and_(
                WorkerTemplate.is_marketplace_listed.is_(True),
                WorkerTemplate.status == WorkerTemplateStatus.ACTIVE.value,
            )
        )

    return (
        db.query(WorkerTemplate)
        .filter(*filters)
        .order_by(WorkerTemplate.workspace_id.desc(), WorkerTemplate.created_at.desc())
        .all()
    )


def install_worker_template(
    db: Session,
    *,
    template: WorkerTemplate,
    workspace_id: uuid.UUID,
    installer_user_id: uuid.UUID | None,
    instance_name: str | None = None,
    runtime_config_overrides: dict[str, Any] | None = None,
    schedule_expression: str | None = None,
    memory_scope: WorkerMemoryScope | str = WorkerMemoryScope.INSTANCE,
) -> TemplateInstallResult:
    if not _is_publicly_visible(template) and template.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Template is not installable for this workspace")
    if not template.is_active or template.status != WorkerTemplateStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Template must be active to install")

    subscription: WorkerSubscription | None = None
    should_increment_install_count = False

    with db.begin_nested():
        allowed_scopes = {item.value for item in WorkerMemoryScope}
        resolved_memory_scope = memory_scope.value if isinstance(memory_scope, WorkerMemoryScope) else str(memory_scope)
        if resolved_memory_scope not in allowed_scopes:
            raise HTTPException(status_code=400, detail="Invalid memory_scope")

        runtime_config = dict(template.config_json or template.default_config_json or {})
        if runtime_config_overrides:
            runtime_config.update(runtime_config_overrides)

        resolved_name = (instance_name or template.name or template.display_name).strip()
        if not resolved_name:
            resolved_name = "Installed Worker"

        instance = WorkerInstance(
            workspace_id=workspace_id,
            template_id=template.id,
            owner_user_id=installer_user_id,
            name=resolved_name,
            status=WorkerInstanceStatus.ACTIVE.value,
            runtime_config_json=runtime_config,
            schedule_expression=schedule_expression,
            memory_scope=resolved_memory_scope,
        )
        db.add(instance)

        if _is_marketplace_visible(template) and template.pricing_type != WorkerPricingType.INTERNAL.value:
            subscription = (
                db.query(WorkerSubscription)
                .filter(
                    WorkerSubscription.workspace_id == workspace_id,
                    WorkerSubscription.worker_template_id == template.id,
                    WorkerSubscription.is_active.is_(True),
                )
                .first()
            )
            if not subscription:
                subscription = WorkerSubscription(
                    workspace_id=workspace_id,
                    worker_template_id=template.id,
                    purchaser_user_id=installer_user_id,
                    billing_status="active",
                    price_cents=template.price_cents,
                    currency=template.currency or "USD",
                    started_at=datetime.now(UTC),
                    is_active=True,
                )
                db.add(subscription)

        should_increment_install_count = template.workspace_id != workspace_id and (
            _is_publicly_visible(template) or template.is_marketplace_listed
        )
        if should_increment_install_count:
            template.install_count = int(template.install_count or 0) + 1

        db.flush()
    return TemplateInstallResult(
        instance=instance,
        subscription=subscription,
        install_count_incremented=should_increment_install_count,
    )
