import uuid
from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import (
    WorkerChainStatus,
    WorkerChainTriggerType,
    WorkerInstanceStatus,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerRunStatus,
    WorkerRunTriggerType,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
)


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(value: str) -> str:
    slug = (value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9\-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def validate_slug_uniqueness(slug: str | None, existing_slugs: set[str]) -> None:
    if not slug:
        return
    if slug in existing_slugs:
        raise ValueError(f"Slug already exists: {slug}")


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"


class SignUpRequest(BaseSchema):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str
    website: str | None = None
    industry: str | None = None


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class UserRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime


class WorkspaceRead(BaseSchema):
    id: uuid.UUID
    company_name: str
    website: str | None = None
    industry: str | None = None
    subscription_plan: str
    created_at: datetime
    updated_at: datetime


class WorkspaceUpdate(BaseSchema):
    company_name: str | None = None
    website: str | None = None
    industry: str | None = None
    subscription_plan: str | None = None


class WorkerCreate(BaseSchema):
    name: str
    goal: str
    worker_type: str = "ai_sales_worker"
    template_id: uuid.UUID | None = None
    target_industry: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    company_size_range: str | None = None
    tone: str = "professional"
    daily_send_limit: int = 40
    run_interval_minutes: int = 60


class WorkerUpdate(BaseSchema):
    name: str | None = None
    mission: str | None = None
    goal: str | None = None
    tone: str | None = None
    daily_send_limit: int | None = None
    run_interval_minutes: int | None = None
    status: str | None = None
    plan_version: str | None = None
    allowed_actions: list[str] | None = None
    is_internal: bool | None = None
    config_json: dict[str, Any] | None = None


class WorkerRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    worker_type: str
    worker_category: str
    mission: str
    goal: str
    plan_version: str
    allowed_actions: list[str] | None = None
    template_id: uuid.UUID | None = None
    origin_type: str
    is_custom_worker: bool
    is_internal: bool
    status: str
    tone: str
    send_limit_per_day: int
    run_interval_minutes: int
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_error_text: str | None = None
    config_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class WorkerTemplateRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    creator_user_id: uuid.UUID | None = None
    name: str
    slug: str | None = None
    template_key: str
    display_name: str
    short_description: str | None = None
    description: str | None = None
    category: str
    worker_type: str
    worker_category: str
    plan_version: str
    visibility: WorkerTemplateVisibility = WorkerTemplateVisibility.WORKSPACE
    status: WorkerTemplateStatus = WorkerTemplateStatus.ACTIVE
    instructions: str | None = None
    model_name: str | None = None
    default_config_json: dict[str, Any] | None = None
    config_json: dict[str, Any] | None = None
    capabilities_json: dict[str, Any] | None = None
    allowed_actions: list[str] | None = None
    actions_json: list[str] | None = None
    tools_json: list[str] | None = None
    prompt_profile: str | None = None
    memory_enabled: bool = True
    chain_enabled: bool = False
    is_system_template: bool = False
    is_public: bool
    is_marketplace_listed: bool = False
    is_active: bool
    pricing_type: WorkerPricingType = WorkerPricingType.INTERNAL
    price_cents: int = 0
    currency: str = "USD"
    install_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    tags_json: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class WorkerTemplateCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=160)
    short_description: str | None = Field(default=None, max_length=255)
    description: str | None = None
    category: str = Field(default="general", min_length=2, max_length=80)
    worker_type: str
    worker_category: str = Field(default="general", min_length=2, max_length=80)
    visibility: WorkerTemplateVisibility = WorkerTemplateVisibility.WORKSPACE
    status: WorkerTemplateStatus = WorkerTemplateStatus.DRAFT
    instructions: str | None = None
    model_name: str | None = Field(default=None, max_length=120)
    config_json: dict[str, Any] = Field(default_factory=dict)
    capabilities_json: dict[str, Any] = Field(default_factory=dict)
    actions_json: list[str] = Field(default_factory=list)
    tools_json: list[str] = Field(default_factory=list)
    memory_enabled: bool = True
    chain_enabled: bool = False
    is_marketplace_listed: bool = False
    pricing_type: WorkerPricingType = WorkerPricingType.INTERNAL
    price_cents: int = 0
    currency: str = Field(default="USD", min_length=3, max_length=10)
    tags_json: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug must contain alphanumeric characters")
        if not SLUG_PATTERN.match(normalized):
            raise ValueError("Slug must be lowercase letters, numbers, and single hyphens")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.pricing_type == WorkerPricingType.FREE and self.price_cents != 0:
            raise ValueError("price_cents must be 0 when pricing_type is free")
        if self.pricing_type in {WorkerPricingType.SUBSCRIPTION, WorkerPricingType.ONE_TIME} and self.price_cents <= 0:
            raise ValueError("price_cents must be > 0 for paid pricing types")
        if self.is_marketplace_listed and self.pricing_type != WorkerPricingType.FREE and self.price_cents <= 0:
            raise ValueError("Marketplace listed paid templates require valid pricing")
        return self

    def assert_slug_unique(self, existing_slugs: set[str]) -> None:
        validate_slug_uniqueness(self.slug, existing_slugs)


class WorkerTemplateUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=160)
    short_description: str | None = Field(default=None, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    worker_category: str | None = Field(default=None, min_length=2, max_length=80)
    visibility: WorkerTemplateVisibility | None = None
    status: WorkerTemplateStatus | None = None
    instructions: str | None = None
    model_name: str | None = Field(default=None, max_length=120)
    config_json: dict[str, Any] | None = None
    capabilities_json: dict[str, Any] | None = None
    actions_json: list[str] | None = None
    tools_json: list[str] | None = None
    memory_enabled: bool | None = None
    chain_enabled: bool | None = None
    is_marketplace_listed: bool | None = None
    pricing_type: WorkerPricingType | None = None
    price_cents: int | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    tags_json: list[str] | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug must contain alphanumeric characters")
        if not SLUG_PATTERN.match(normalized):
            raise ValueError("Slug must be lowercase letters, numbers, and single hyphens")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.upper()

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.pricing_type == WorkerPricingType.FREE and self.price_cents not in {None, 0}:
            raise ValueError("price_cents must be 0 when pricing_type is free")
        if self.pricing_type in {WorkerPricingType.SUBSCRIPTION, WorkerPricingType.ONE_TIME} and (
            self.price_cents is not None and self.price_cents <= 0
        ):
            raise ValueError("price_cents must be > 0 for paid pricing types")
        if self.is_marketplace_listed and self.pricing_type in {WorkerPricingType.SUBSCRIPTION, WorkerPricingType.ONE_TIME}:
            if self.price_cents is None or self.price_cents <= 0:
                raise ValueError("Marketplace listed paid templates require valid pricing")
        return self

    def assert_slug_unique(self, existing_slugs: set[str]) -> None:
        validate_slug_uniqueness(self.slug, existing_slugs)


class WorkerTemplatePublishRequest(BaseSchema):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=20)
    instructions: str = Field(min_length=20)
    model_name: str = Field(min_length=2, max_length=120)
    config_json: dict[str, Any] = Field(default_factory=dict)
    visibility: WorkerTemplateVisibility = WorkerTemplateVisibility.PUBLIC
    is_marketplace_listed: bool = False
    pricing_type: WorkerPricingType = WorkerPricingType.FREE
    price_cents: int = 0
    currency: str = Field(default="USD", min_length=3, max_length=10)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug must contain alphanumeric characters")
        if not SLUG_PATTERN.match(normalized):
            raise ValueError("Slug must be lowercase letters, numbers, and single hyphens")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_publish_requirements(self):
        if len(self.config_json) == 0:
            raise ValueError("config_json must contain meaningful configuration before publish")
        if self.is_marketplace_listed and self.pricing_type != WorkerPricingType.FREE and self.price_cents <= 0:
            raise ValueError("Marketplace listed paid templates require valid pricing")
        if self.pricing_type == WorkerPricingType.FREE and self.price_cents != 0:
            raise ValueError("Free pricing requires price_cents = 0")
        return self

    def assert_slug_unique(self, existing_slugs: set[str]) -> None:
        validate_slug_uniqueness(self.slug, existing_slugs)


class WorkerTemplateInstallRequest(BaseSchema):
    instance_name: str | None = Field(default=None, min_length=2, max_length=120)
    runtime_config_overrides: dict[str, Any] = Field(default_factory=dict)
    schedule_expression: str | None = Field(default=None, max_length=120)
    memory_scope: WorkerMemoryScope = WorkerMemoryScope.INSTANCE


class WorkerTemplateDuplicateRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=2, max_length=160)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_slug(value)
        if not normalized:
            raise ValueError("Slug must contain alphanumeric characters")
        if not SLUG_PATTERN.match(normalized):
            raise ValueError("Slug must be lowercase letters, numbers, and single hyphens")
        return normalized


class WorkerBuilderActionRead(BaseSchema):
    key: str
    name: str
    description: str
    default_status: str


class WorkerBuilderStepInput(BaseSchema):
    key: str
    action_key: str
    name: str | None = None
    status: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class InternalWorkerTemplateCreate(BaseSchema):
    display_name: str
    worker_type: str = "custom_worker"
    worker_category: str = "custom"
    plan_version: str = "v1"
    prompt_profile: str = "sales"
    allowed_actions: list[str]
    steps: list[WorkerBuilderStepInput]
    config_defaults: dict[str, Any] = Field(default_factory=dict)
    mission_default: str | None = None
    is_active: bool = True


class InternalWorkerFromTemplateCreate(BaseSchema):
    template_id: uuid.UUID
    name: str
    mission: str
    tone: str = "professional"
    daily_send_limit: int = 40
    run_interval_minutes: int = 60
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class WorkerRunRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID | None = None
    worker_id: uuid.UUID
    instance_id: uuid.UUID | None = None
    template_id: uuid.UUID | None = None
    campaign_id: uuid.UUID | None = None
    run_type: str
    triggered_by: WorkerRunTriggerType = WorkerRunTriggerType.MANUAL
    trigger_source: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    status: WorkerRunStatus
    attempts: int
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    summary: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    token_usage_input: int = 0
    token_usage_output: int = 0
    cost_cents: int = 0
    created_at: datetime | None = None
    error_text: str | None = None


class WorkerRunListResponse(BaseSchema):
    items: list[WorkerRunRead]
    total: int


class WorkerInstanceRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    template_id: uuid.UUID
    owner_user_id: uuid.UUID | None = None
    legacy_worker_id: uuid.UUID | None = None
    name: str
    status: WorkerInstanceStatus
    runtime_config_json: dict[str, Any] | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    schedule_expression: str | None = None
    memory_scope: WorkerMemoryScope
    created_at: datetime
    updated_at: datetime


class WorkerInstanceUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    status: WorkerInstanceStatus | None = None
    runtime_config_json: dict[str, Any] | None = None
    next_run_at: datetime | None = None
    schedule_expression: str | None = Field(default=None, max_length=120)
    memory_scope: WorkerMemoryScope | None = None


class WorkerInstanceExecuteRequest(BaseSchema):
    runtime_input: dict[str, Any] = Field(default_factory=dict)
    trigger_source: str | None = Field(default=None, max_length=255)


class WorkerInstanceExecuteResponse(BaseSchema):
    success: bool
    queued: bool
    run_id: uuid.UUID
    task_id: str | None = None
    status: WorkerRunStatus


class WorkerChainStepCreate(BaseSchema):
    step_order: int = Field(ge=1)
    worker_instance_id: uuid.UUID | None = None
    worker_template_id: uuid.UUID | None = None
    step_name: str = Field(min_length=2, max_length=120)
    input_mapping_json: dict[str, Any] = Field(default_factory=dict)
    condition_json: dict[str, Any] | None = None
    on_success_next_step: int | None = Field(default=None, ge=1)
    on_failure_next_step: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_worker_reference(self):
        if not self.worker_instance_id and not self.worker_template_id:
            raise ValueError("Each chain step must reference worker_instance_id or worker_template_id")
        return self


class WorkerChainStepRead(BaseSchema):
    id: uuid.UUID
    chain_id: uuid.UUID
    step_order: int
    worker_instance_id: uuid.UUID | None = None
    worker_template_id: uuid.UUID | None = None
    step_name: str
    input_mapping_json: dict[str, Any] | None = None
    condition_json: dict[str, Any] | None = None
    on_success_next_step: int | None = None
    on_failure_next_step: int | None = None
    created_at: datetime
    updated_at: datetime


class WorkerChainCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    status: WorkerChainStatus = WorkerChainStatus.DRAFT
    trigger_type: WorkerChainTriggerType = WorkerChainTriggerType.MANUAL
    trigger_config_json: dict[str, Any] = Field(default_factory=dict)
    steps: list[WorkerChainStepCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_step_order(self):
        if not self.steps:
            return self
        orders = [item.step_order for item in self.steps]
        if len(set(orders)) != len(orders):
            raise ValueError("Worker chain step_order values must be unique")
        return self


class WorkerChainUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    status: WorkerChainStatus | None = None
    trigger_type: WorkerChainTriggerType | None = None
    trigger_config_json: dict[str, Any] | None = None
    steps: list[WorkerChainStepCreate] | None = None

    @model_validator(mode="after")
    def validate_step_order(self):
        if not self.steps:
            return self
        orders = [item.step_order for item in self.steps]
        if len(set(orders)) != len(orders):
            raise ValueError("Worker chain step_order values must be unique")
        return self


class WorkerChainRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    status: WorkerChainStatus
    trigger_type: WorkerChainTriggerType
    trigger_config_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    steps: list[WorkerChainStepRead] = Field(default_factory=list)


class WorkerChainListResponse(BaseSchema):
    items: list[WorkerChainRead]
    total: int


class WorkerReviewCreate(BaseSchema):
    rating: int = Field(ge=1, le=5)
    review_text: str | None = None


class WorkerReviewRead(BaseSchema):
    id: uuid.UUID
    worker_template_id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    review_text: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkerToolRead(BaseSchema):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    category: str
    config_schema_json: dict[str, Any] | None = None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WorkerToolListResponse(BaseSchema):
    items: list[WorkerToolRead]
    total: int


class WorkerSubscriptionRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    worker_template_id: uuid.UUID
    purchaser_user_id: uuid.UUID | None = None
    billing_status: str
    price_cents: int
    currency: str
    started_at: datetime
    ends_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MarketplaceListingRead(BaseSchema):
    template: WorkerTemplateRead
    is_installed: bool = False
    subscription: WorkerSubscriptionRead | None = None


class MarketplaceInstallResponse(BaseSchema):
    success: bool = True
    worker_template_id: uuid.UUID
    subscription: WorkerSubscriptionRead
    message: str = "Template installed successfully"


class PublicWorkerListItem(BaseSchema):
    id: uuid.UUID
    slug: str
    name: str
    short_description: str | None = None
    category: str
    pricing_type: WorkerPricingType
    price_cents: int
    currency: str
    rating_avg: float = 0.0
    rating_count: int = 0
    install_count: int = 0
    tags_json: list[str] | None = None


class PublicWorkerDetailRead(BaseSchema):
    template: WorkerTemplateRead
    reviews: list[WorkerReviewRead] = Field(default_factory=list)
    tools: list[WorkerToolRead] = Field(default_factory=list)
    average_rating: float = 0.0
    installs: int = 0


class CampaignCreate(BaseSchema):
    worker_id: uuid.UUID | None = None
    name: str
    ideal_customer_profile: str | None = None
    target_industry: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    company_size_min: int | None = None
    company_size_max: int | None = None
    cta_text: str | None = None
    exclusions: list[str] = Field(default_factory=list)
    scheduling_settings: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseSchema):
    name: str | None = None
    target_industry: str | None = None
    target_roles: list[str] | None = None
    target_locations: list[str] | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    cta_text: str | None = None
    status: str | None = None


class CampaignRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    worker_id: uuid.UUID | None = None
    name: str
    target_industry: str | None = None
    target_roles: list[str] | None = None
    target_locations: list[str] | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    cta_text: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class LeadCreate(BaseSchema):
    campaign_id: uuid.UUID | None = None
    company_name: str
    website: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    title: str | None = None
    email: EmailStr
    linkedin_url: str | None = None
    location: str | None = None
    company_size: int | None = None
    lead_source: str | None = None
    enrichment_json: dict[str, Any] | None = None


class LeadUpdate(BaseSchema):
    title: str | None = None
    location: str | None = None
    company_size: int | None = None
    lead_status: str | None = None
    enrichment_json: dict[str, Any] | None = None


class LeadRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    campaign_id: uuid.UUID | None = None
    company_name: str
    website: str | None = None
    full_name: str | None = None
    title: str | None = None
    email: EmailStr
    location: str | None = None
    company_size: int | None = None
    lead_source: str | None = None
    lead_status: str
    enrichment_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseSchema):
    id: uuid.UUID
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    sequence_step: int
    subject_line: str
    body_text: str
    personalization_json: dict[str, Any] | None = None
    approval_status: str
    created_at: datetime
    updated_at: datetime


class ReplyRead(BaseSchema):
    id: uuid.UUID
    sent_email_id: uuid.UUID
    lead_id: uuid.UUID
    reply_text: str
    sentiment: str | None = None
    intent_classification: str
    requires_human_review: bool
    created_at: datetime


class MeetingBookRequest(BaseSchema):
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime


class MeetingRead(BaseSchema):
    id: uuid.UUID
    workspace_id: uuid.UUID
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    calendar_provider: str
    external_event_id: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    meeting_status: str
    created_at: datetime
    updated_at: datetime


class AnalyticsOverview(BaseSchema):
    active_workers: int
    campaigns: int
    leads_found: int
    leads_researched: int
    messages_awaiting_approval: int
    emails_sent: int
    replies: int
    interested_replies: int
    meetings_booked: int
    recent_activity: list[dict[str, Any]]
    recent_worker_runs: list[dict[str, Any]]


class CampaignAnalytics(BaseSchema):
    campaign_id: uuid.UUID
    sent: int
    replies: int
    meetings: int
    positive_reply_rate: float


class WorkerAnalytics(BaseSchema):
    worker_id: uuid.UUID
    runs: int
    successful_runs: int
    failed_runs: int
    status: str


class WebhookPayload(BaseSchema):
    provider_message_id: str | None = None
    email: str | None = None
    event: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class CalendarConnectRequest(BaseSchema):
    auth_code: str | None = None
    redirect_uri: str | None = None
