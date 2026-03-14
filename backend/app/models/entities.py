import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Numeric,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkerStatus(StrEnum):
    IDLE = "idle"
    PROSPECTING = "prospecting"
    RESEARCHING = "researching"
    DRAFTING = "drafting"
    AWAITING_APPROVAL = "awaiting_approval"
    SENDING = "sending"
    MONITORING = "monitoring"
    OPTIMIZING = "optimizing"
    PAUSED = "paused"
    ERROR = "error"


class WorkerRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkerTemplateVisibility(StrEnum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    PUBLIC = "public"
    MARKETPLACE = "marketplace"


class WorkerTemplateStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkerPricingType(StrEnum):
    FREE = "free"
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    INTERNAL = "internal"


class WorkerInstanceStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class WorkerMemoryScope(StrEnum):
    NONE = "none"
    INSTANCE = "instance"
    WORKSPACE = "workspace"


class WorkerRunTriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    API = "api"
    CHAIN = "chain"
    EVENT = "event"


class WorkerChainStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WorkerChainTriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    API = "api"


class WorkerBuilderCategory(StrEnum):
    REAL_ESTATE = "real_estate"
    MARKETING = "marketing"
    FINANCE = "finance"
    SALES = "sales"
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    RESEARCH = "research"
    AUTOMATION = "automation"
    CUSTOM = "custom"


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class WorkspaceSubscriptionStatus(StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class BillingEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class WorkerAccessType(StrEnum):
    FREE = "free"
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    BUNDLED = "bundled"


class WorkerEntitlementStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REFUNDED = "refunded"
    CANCELED = "canceled"
    PENDING = "pending"


class LeadStatus(StrEnum):
    NEW = "new"
    RESEARCHING = "researching"
    READY_FOR_OUTREACH = "ready_for_outreach"
    CONTACTED = "contacted"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    REPLIED_POSITIVE = "replied_positive"
    REPLIED_NEUTRAL = "replied_neutral"
    REPLIED_NEGATIVE = "replied_negative"
    MEETING_BOOKED = "meeting_booked"
    CLOSED_LOST = "closed_lost"
    DO_NOT_CONTACT = "do_not_contact"


class ReplyIntent(StrEnum):
    INTERESTED = "interested"
    NOT_NOW = "not_now"
    NOT_INTERESTED = "not_interested"
    REFERRAL = "referral"
    QUESTION = "question"
    UNSUBSCRIBE = "unsubscribe"
    OUT_OF_OFFICE = "out_of_office"
    UNKNOWN = "unknown"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(120))
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter", nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="owner", nullable=False)


class CreatorMonetizationProfile(Base, TimestampMixin):
    __tablename__ = "creator_monetization_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_creator_monetization_profiles_user_id"),
        Index("ix_creator_monetization_profiles_payouts_enabled", "payouts_enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    stripe_account_id: Mapped[str | None] = mapped_column(String(255))
    payouts_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tax_profile_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SubscriptionPlan(Base, TimestampMixin):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_subscription_plans_code"),
        Index("ix_subscription_plans_code_active", "code", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    monthly_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annual_price_cents: Mapped[int | None] = mapped_column(Integer)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id_annual: Mapped[str | None] = mapped_column(String(255))
    max_worker_drafts: Mapped[int | None] = mapped_column(Integer)
    max_published_workers: Mapped[int | None] = mapped_column(Integer)
    max_worker_installs_per_workspace: Mapped[int | None] = mapped_column(Integer)
    max_worker_runs_per_month: Mapped[int | None] = mapped_column(Integer)
    allow_worker_builder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_marketplace_publishing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_private_workers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_public_workers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_marketplace_install: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_team_features: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkspaceSubscription(Base, TimestampMixin):
    __tablename__ = "workspace_subscriptions"
    __table_args__ = (
        Index("ix_workspace_subscriptions_workspace_status", "workspace_id", "status"),
        Index("ix_workspace_subscriptions_customer_id", "stripe_customer_id"),
        Index("ix_workspace_subscriptions_subscription_id", "stripe_subscription_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("subscription_plans.id"))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), default=WorkspaceSubscriptionStatus.ACTIVE.value, nullable=False)
    billing_interval: Mapped[str] = mapped_column(String(20), default=BillingInterval.MONTHLY.value, nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BillingEventLog(Base):
    __tablename__ = "billing_event_logs"
    __table_args__ = (
        UniqueConstraint("stripe_event_id", name="uq_billing_event_logs_stripe_event_id"),
        Index("ix_billing_event_logs_event_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default=BillingEventStatus.RECEIVED.value, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConnectedAccount(Base, TimestampMixin):
    __tablename__ = "connected_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Worker(Base, TimestampMixin):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), default="ai_sales_worker", nullable=False)
    worker_category: Mapped[str] = mapped_column(String(80), default="go_to_market", nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False, default="")
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    plan_version: Mapped[str] = mapped_column(String(40), default="v1", nullable=False)
    allowed_actions: Mapped[list[str] | None] = mapped_column(JSON)
    template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_templates.id"))
    origin_type: Mapped[str] = mapped_column(String(40), default="built_in", nullable=False)
    is_custom_worker: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=WorkerStatus.IDLE.value, nullable=False)
    tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    send_limit_per_day: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    run_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_text: Mapped[str | None] = mapped_column(Text)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workers.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_industry: Mapped[str | None] = mapped_column(String(120))
    target_roles: Mapped[list[str] | None] = mapped_column(JSON)
    target_locations: Mapped[list[str] | None] = mapped_column(JSON)
    company_size_min: Mapped[int | None] = mapped_column(Integer)
    company_size_max: Mapped[int | None] = mapped_column(Integer)
    cta_text: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    full_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(120))
    company_size: Mapped[int | None] = mapped_column(Integer)
    lead_source: Mapped[str | None] = mapped_column(String(120))
    lead_status: Mapped[str] = mapped_column(String(50), default=LeadStatus.NEW.value, nullable=False)
    enrichment_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class CompanyResearch(Base):
    __tablename__ = "company_research"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=False, unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    pain_points: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    personalization_hook: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by_model: Mapped[str] = mapped_column(String(120), default="mock-v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmailSequence(Base, TimestampMixin):
    __tablename__ = "email_sequences"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"), nullable=False)
    sequence_name: Mapped[str] = mapped_column(String(120), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GeneratedMessage(Base, TimestampMixin):
    __tablename__ = "generated_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"), nullable=False)
    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=False)
    sequence_step: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_line: Mapped[str] = mapped_column(String(255), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    approval_status: Mapped[str] = mapped_column(String(50), default=ApprovalStatus.PENDING.value, nullable=False)


class SentEmail(Base, TimestampMixin):
    __tablename__ = "sent_emails"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"), nullable=False)
    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=False)
    generated_message_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("generated_messages.id"), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    open_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bounce_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Reply(Base):
    __tablename__ = "replies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sent_email_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sent_emails.id"), nullable=False)
    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=False)
    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(50))
    intent_classification: Mapped[str] = mapped_column(String(50), default=ReplyIntent.UNKNOWN.value, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"), nullable=False)
    lead_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=False)
    calendar_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(String(255))
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)


class WorkerRun(Base):
    __tablename__ = "worker_runs"
    __table_args__ = (
        Index("ix_worker_runs_workspace_id", "workspace_id"),
        Index("ix_worker_runs_instance_id", "instance_id"),
        Index("ix_worker_runs_template_id", "template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id"), nullable=False)
    instance_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_instances.id"))
    template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_templates.id"))
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(40), default=WorkerRunTriggerType.MANUAL.value, nullable=False)
    trigger_source: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    token_usage_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_usage_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text)


class WorkerTemplate(Base, TimestampMixin):
    __tablename__ = "worker_templates"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_worker_templates_workspace_slug"),
        CheckConstraint("creator_revenue_percent >= 0 AND creator_revenue_percent <= 100", name="ck_worker_templates_creator_revenue_percent"),
        CheckConstraint("platform_revenue_percent >= 0 AND platform_revenue_percent <= 100", name="ck_worker_templates_platform_revenue_percent"),
        Index("ix_worker_templates_slug", "slug"),
        Index("ix_worker_templates_visibility_status", "visibility", "status"),
        Index("ix_worker_templates_marketplace_listed", "is_marketplace_listed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    creator_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    slug: Mapped[str | None] = mapped_column(String(160))
    template_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default="general", nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    worker_category: Mapped[str] = mapped_column(String(80), nullable=False)
    plan_version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1")
    visibility: Mapped[str] = mapped_column(String(30), default=WorkerTemplateVisibility.WORKSPACE.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=WorkerTemplateStatus.ACTIVE.value, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(120))
    default_config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    capabilities_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    allowed_actions: Mapped[list[str] | None] = mapped_column(JSON)
    actions_json: Mapped[list[str] | None] = mapped_column(JSON)
    tools_json: Mapped[list[str] | None] = mapped_column(JSON)
    prompt_profile: Mapped[str | None] = mapped_column(String(80))
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    chain_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_marketplace_listed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pricing_type: Mapped[str] = mapped_column(String(30), default=WorkerPricingType.INTERNAL.value, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    icon: Mapped[str | None] = mapped_column(String(255))
    screenshots_json: Mapped[list[str] | None] = mapped_column(JSON)
    usage_examples_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    creator_revenue_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=70.0, nullable=False)
    platform_revenue_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=30.0, nullable=False)
    install_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags_json: Mapped[list[str] | None] = mapped_column(JSON)


class WorkerTemplateDraft(Base, TimestampMixin):
    __tablename__ = "worker_template_drafts"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_worker_template_drafts_workspace_slug"),
        CheckConstraint("creator_revenue_percent >= 0 AND creator_revenue_percent <= 100", name="ck_worker_template_drafts_creator_revenue_percent"),
        CheckConstraint("platform_revenue_percent >= 0 AND platform_revenue_percent <= 100", name="ck_worker_template_drafts_platform_revenue_percent"),
        Index("ix_worker_template_drafts_workspace_creator", "workspace_id", "creator_user_id"),
        Index("ix_worker_template_drafts_category", "category"),
        Index("ix_worker_template_drafts_published", "is_published"),
        Index("ix_worker_template_drafts_slug", "slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    creator_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    published_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_templates.id"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default=WorkerBuilderCategory.CUSTOM.value, nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tools_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    visibility: Mapped[str] = mapped_column(String(30), default=WorkerTemplateVisibility.PRIVATE.value, nullable=False)
    price_monthly: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_onetime: Mapped[float | None] = mapped_column(Numeric(10, 2))
    icon: Mapped[str | None] = mapped_column(String(255))
    screenshots_json: Mapped[list[str] | None] = mapped_column(JSON)
    tags_json: Mapped[list[str] | None] = mapped_column(JSON)
    usage_examples_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creator_revenue_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=70.0, nullable=False)
    platform_revenue_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=30.0, nullable=False)


class WorkerInstance(Base, TimestampMixin):
    __tablename__ = "worker_instances"
    __table_args__ = (
        Index("ix_worker_instances_workspace_status", "workspace_id", "status"),
        Index("ix_worker_instances_template_id", "template_id"),
        Index("ix_worker_instances_next_run_at", "next_run_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_templates.id"), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    legacy_worker_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workers.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=WorkerInstanceStatus.ACTIVE.value, nullable=False)
    runtime_config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    schedule_expression: Mapped[str | None] = mapped_column(String(120))
    memory_scope: Mapped[str] = mapped_column(String(20), default=WorkerMemoryScope.INSTANCE.value, nullable=False)


class WorkerMemory(Base, TimestampMixin):
    __tablename__ = "worker_memory"
    __table_args__ = (
        Index("ix_worker_memory_workspace_key", "workspace_id", "memory_key"),
        Index("ix_worker_memory_instance_id", "instance_id"),
        Index("ix_worker_memory_template_id", "template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    instance_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_instances.id"))
    template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_templates.id"))
    memory_key: Mapped[str] = mapped_column(String(255), nullable=False)
    memory_value_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), default="episodic", nullable=False)


class WorkerChain(Base, TimestampMixin):
    __tablename__ = "worker_chains"
    __table_args__ = (
        Index("ix_worker_chains_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default=WorkerChainStatus.DRAFT.value, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(40), default=WorkerChainTriggerType.MANUAL.value, nullable=False)
    trigger_config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class WorkerChainStep(Base, TimestampMixin):
    __tablename__ = "worker_chain_steps"
    __table_args__ = (
        UniqueConstraint("chain_id", "step_order", name="uq_worker_chain_steps_chain_order"),
        CheckConstraint(
            "(worker_instance_id IS NOT NULL) OR (worker_template_id IS NOT NULL)",
            name="ck_worker_chain_steps_worker_ref",
        ),
        Index("ix_worker_chain_steps_chain_id", "chain_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    chain_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_chains.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_instance_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_instances.id"))
    worker_template_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("worker_templates.id"))
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input_mapping_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    condition_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    on_success_next_step: Mapped[int | None] = mapped_column(Integer)
    on_failure_next_step: Mapped[int | None] = mapped_column(Integer)


class WorkerTool(Base, TimestampMixin):
    __tablename__ = "worker_tools"
    __table_args__ = (
        Index("ix_worker_tools_category_active", "category", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    config_schema_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkerTemplateTool(Base):
    __tablename__ = "worker_template_tools"
    __table_args__ = (
        UniqueConstraint("worker_template_id", "worker_tool_id", name="uq_worker_template_tool_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    worker_template_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_templates.id"), nullable=False)
    worker_tool_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_tools.id"), nullable=False)


class WorkerSubscription(Base, TimestampMixin):
    __tablename__ = "worker_subscriptions"
    __table_args__ = (
        Index("ix_worker_subscriptions_workspace_active", "workspace_id", "is_active"),
        Index("ix_worker_subscriptions_template_id", "worker_template_id"),
        Index("ix_worker_subscriptions_status", "status"),
        Index("ix_worker_subscriptions_checkout_session", "stripe_checkout_session_id"),
        Index("ix_worker_subscriptions_stripe_subscription", "stripe_subscription_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    worker_template_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_templates.id"), nullable=False)
    purchaser_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    billing_status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    access_type: Mapped[str] = mapped_column(String(30), default=WorkerAccessType.FREE.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=WorkerEntitlementStatus.ACTIVE.value, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkerRevenueEvent(Base):
    __tablename__ = "worker_revenue_events"
    __table_args__ = (
        Index("ix_worker_revenue_events_template", "worker_template_id"),
        Index("ix_worker_revenue_events_workspace", "workspace_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    worker_template_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_templates.id"), nullable=False)
    creator_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    revenue_type: Mapped[str] = mapped_column(String(40), nullable=False)
    gross_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creator_payout_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(60))
    reference_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WorkerReview(Base, TimestampMixin):
    __tablename__ = "worker_reviews"
    __table_args__ = (
        UniqueConstraint("worker_template_id", "user_id", "workspace_id", name="uq_worker_reviews_template_user_workspace"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_worker_reviews_rating_range"),
        Index("ix_worker_reviews_template_id", "worker_template_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    worker_template_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("worker_templates.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    event_name: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
