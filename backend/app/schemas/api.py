import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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
    template_key: str
    display_name: str
    worker_type: str
    worker_category: str
    plan_version: str
    default_config_json: dict[str, Any] | None = None
    allowed_actions: list[str] | None = None
    prompt_profile: str | None = None
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


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
    worker_id: uuid.UUID
    campaign_id: uuid.UUID | None = None
    run_type: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    attempts: int
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    error_text: str | None = None


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
