import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Uuid, func
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
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


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

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workers.id"), nullable=False)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    input_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_text: Mapped[str | None] = mapped_column(Text)


class WorkerTemplate(Base, TimestampMixin):
    __tablename__ = "worker_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("workspaces.id"))
    template_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(50), nullable=False)
    worker_category: Mapped[str] = mapped_column(String(80), nullable=False)
    plan_version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1")
    default_config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    allowed_actions: Mapped[list[str] | None] = mapped_column(JSON)
    prompt_profile: Mapped[str | None] = mapped_column(String(80))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workspaces.id"), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    event_name: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
