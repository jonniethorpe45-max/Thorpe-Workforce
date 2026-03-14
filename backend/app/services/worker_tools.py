import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models import Lead, WorkerTemplate, WorkerTemplateTool, WorkerTool
from app.schemas.api import LeadCreate, MeetingBookRequest
from app.services.audit import log_audit_event
from app.services.lead_service import create_single_lead
from app.services.meeting_service import book_meeting
from app.services.message_generator import send_approved_messages


@dataclass(frozen=True)
class WorkerToolDefinition:
    name: str
    slug: str
    description: str
    category: str
    config_schema_json: dict[str, Any]
    is_system: bool = True
    is_active: bool = True


@dataclass
class WorkerToolRuntimeContext:
    db: Session
    workspace_id: uuid.UUID
    instance_id: uuid.UUID
    template_id: uuid.UUID
    worker_id: uuid.UUID
    run_id: uuid.UUID


@dataclass
class WorkerToolInvocationResult:
    tool: str
    success: bool
    output: dict[str, Any]
    error: str | None = None


ToolHandler = Callable[[WorkerToolRuntimeContext, dict[str, Any]], dict[str, Any]]


def _parse_uuid(value: Any, field_name: str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{field_name} must be a valid UUID") from exc


def _parse_datetime(value: Any, field_name: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc


SYSTEM_TOOL_DEFINITIONS: list[WorkerToolDefinition] = [
    WorkerToolDefinition(
        name="Email Sender",
        slug="email_sender",
        description="Send approved campaign emails through the connected email provider.",
        category="messaging",
        config_schema_json={
            "type": "object",
            "properties": {"campaign_id": {"type": "string", "format": "uuid"}},
            "required": ["campaign_id"],
        },
    ),
    WorkerToolDefinition(
        name="SMS Sender",
        slug="sms_sender",
        description="Dispatch SMS notifications through a provider adapter (stubbed in MVP).",
        category="messaging",
        config_schema_json={
            "type": "object",
            "properties": {"to": {"type": "string"}, "message": {"type": "string"}},
            "required": ["to", "message"],
        },
    ),
    WorkerToolDefinition(
        name="Webhook Caller",
        slug="webhook_caller",
        description="Call outbound webhooks with JSON payloads.",
        category="integration",
        config_schema_json={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "body": {"type": "object"},
                "headers": {"type": "object"},
            },
            "required": ["url"],
        },
    ),
    WorkerToolDefinition(
        name="CRM Updater",
        slug="crm_updater",
        description="Update lead enrichment/status fields as a CRM adapter.",
        category="crm",
        config_schema_json={
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "format": "uuid"},
                "enrichment_updates": {"type": "object"},
                "lead_status": {"type": "string"},
            },
            "required": ["lead_id"],
        },
    ),
    WorkerToolDefinition(
        name="Calendar Scheduler",
        slug="calendar_scheduler",
        description="Book meetings through existing calendar integration.",
        category="calendar",
        config_schema_json={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "format": "uuid"},
                "lead_id": {"type": "string", "format": "uuid"},
                "scheduled_start": {"type": "string", "format": "date-time"},
                "scheduled_end": {"type": "string", "format": "date-time"},
            },
            "required": ["campaign_id", "lead_id", "scheduled_start", "scheduled_end"],
        },
    ),
    WorkerToolDefinition(
        name="Lead Recorder",
        slug="lead_recorder",
        description="Create a lead in the workspace/campaign using existing lead service logic.",
        category="leads",
        config_schema_json={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "format": "uuid"},
                "company_name": {"type": "string"},
                "email": {"type": "string"},
                "full_name": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["company_name", "email"],
        },
    ),
    WorkerToolDefinition(
        name="Internal Note Writer",
        slug="internal_note_writer",
        description="Write internal execution notes to audit logs for ops visibility.",
        category="internal",
        config_schema_json={
            "type": "object",
            "properties": {
                "note": {"type": "string"},
                "note_type": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "required": ["note"],
        },
    ),
]


def ensure_system_worker_tools(db: Session) -> list[WorkerTool]:
    tools: list[WorkerTool] = []
    for item in SYSTEM_TOOL_DEFINITIONS:
        existing = db.query(WorkerTool).filter(WorkerTool.slug == item.slug).first()
        if existing:
            existing.name = item.name
            existing.description = item.description
            existing.category = item.category
            existing.config_schema_json = dict(item.config_schema_json)
            existing.is_system = True
            tools.append(existing)
            continue
        created = WorkerTool(
            name=item.name,
            slug=item.slug,
            description=item.description,
            category=item.category,
            config_schema_json=dict(item.config_schema_json),
            is_system=True,
            is_active=item.is_active,
        )
        db.add(created)
        tools.append(created)
    db.flush()
    return tools


def resolve_template_allowed_tool_slugs(db: Session, template: WorkerTemplate) -> list[str]:
    configured_tools = [str(item).strip() for item in (template.tools_json or []) if str(item).strip()]
    linked_tools = (
        db.query(WorkerTool.slug)
        .join(WorkerTemplateTool, WorkerTemplateTool.worker_tool_id == WorkerTool.id)
        .filter(
            WorkerTemplateTool.worker_template_id == template.id,
            WorkerTool.is_active.is_(True),
        )
        .all()
    )
    linked_slugs = [str(row[0]).strip() for row in linked_tools if row and row[0]]
    requested = []
    seen: set[str] = set()
    for slug in configured_tools + linked_slugs:
        if slug in seen:
            continue
        seen.add(slug)
        requested.append(slug)
    if not requested:
        return []
    active = (
        db.query(WorkerTool.slug)
        .filter(
            WorkerTool.slug.in_(requested),
            WorkerTool.is_active.is_(True),
        )
        .all()
    )
    active_set = {str(row[0]) for row in active if row and row[0]}
    return [slug for slug in requested if slug in active_set]


class WorkerToolRegistry:
    def __init__(self) -> None:
        self._definitions = {tool.slug: tool for tool in SYSTEM_TOOL_DEFINITIONS}
        self._handlers: dict[str, ToolHandler] = {}

    def register_handler(self, slug: str, handler: ToolHandler) -> None:
        self._handlers[slug] = handler

    def has_tool(self, slug: str) -> bool:
        return slug in self._definitions and slug in self._handlers

    def invoke(self, context: WorkerToolRuntimeContext, *, tool_slug: str, payload: dict[str, Any]) -> WorkerToolInvocationResult:
        if not self.has_tool(tool_slug):
            return WorkerToolInvocationResult(
                tool=tool_slug,
                success=False,
                output={},
                error="tool_not_registered",
            )
        try:
            output = self._handlers[tool_slug](context, payload if isinstance(payload, dict) else {})
            return WorkerToolInvocationResult(tool=tool_slug, success=True, output=output or {})
        except Exception as exc:  # noqa: BLE001
            return WorkerToolInvocationResult(tool=tool_slug, success=False, output={}, error=str(exc))


def _tool_email_sender(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    campaign_id = _parse_uuid(payload.get("campaign_id"), "campaign_id")
    sent_count = send_approved_messages(context.db, workspace_id=context.workspace_id, campaign_id=campaign_id)
    return {"campaign_id": str(campaign_id), "sent_count": sent_count}


def _tool_sms_sender(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    to = str(payload.get("to", "")).strip()
    message = str(payload.get("message", "")).strip()
    if not to or not message:
        raise ValueError("to and message are required")
    log_audit_event(
        context.db,
        workspace_id=context.workspace_id,
        actor_type="system",
        actor_id="worker_tool_runtime",
        event_name="sms_sender_not_configured",
        payload={"to": to, "preview": message[:120]},
    )
    return {"status": "not_configured", "to": to}


def _tool_webhook_caller(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url", "")).strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise ValueError("url must start with http:// or https://")
    method = str(payload.get("method", "POST")).upper()
    if method not in {"GET", "POST"}:
        raise ValueError("method must be GET or POST")
    headers = payload.get("headers", {})
    if not isinstance(headers, dict):
        headers = {}
    body = payload.get("body", {})
    data = None
    if method == "POST":
        data = json.dumps(body if isinstance(body, dict) else {}).encode("utf-8")
        headers = {"Content-Type": "application/json", **headers}
    request = Request(url=url, data=data, method=method, headers={str(k): str(v) for k, v in headers.items()})
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310
            response_body = response.read(1200).decode("utf-8", errors="replace")
            return {"status_code": int(response.status), "response_preview": response_body}
    except URLError as exc:
        raise ValueError(f"webhook request failed: {exc}") from exc


def _tool_crm_updater(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    lead_id = _parse_uuid(payload.get("lead_id"), "lead_id")
    lead = context.db.get(Lead, lead_id)
    if not lead or lead.workspace_id != context.workspace_id:
        raise ValueError("lead not found")
    updates = payload.get("enrichment_updates", {})
    if not isinstance(updates, dict):
        updates = {}
    base = lead.enrichment_json if isinstance(lead.enrichment_json, dict) else {}
    lead.enrichment_json = {**base, **updates}
    if payload.get("lead_status"):
        lead.lead_status = str(payload["lead_status"])
    context.db.flush()
    return {"lead_id": str(lead.id), "updated_fields": sorted(list(updates.keys()))}


def _tool_calendar_scheduler(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    request = MeetingBookRequest(
        campaign_id=_parse_uuid(payload.get("campaign_id"), "campaign_id"),
        lead_id=_parse_uuid(payload.get("lead_id"), "lead_id"),
        scheduled_start=_parse_datetime(payload.get("scheduled_start"), "scheduled_start"),
        scheduled_end=_parse_datetime(payload.get("scheduled_end"), "scheduled_end"),
    )
    meeting = book_meeting(
        context.db,
        workspace_id=context.workspace_id,
        actor_id=f"worker:{context.worker_id}",
        payload=request,
    )
    context.db.flush()
    return {"meeting_id": str(meeting.id), "meeting_status": meeting.meeting_status}


def _tool_lead_recorder(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    lead = create_single_lead(
        context.db,
        workspace_id=context.workspace_id,
        payload=LeadCreate(
            campaign_id=payload.get("campaign_id"),
            company_name=payload.get("company_name", ""),
            website=payload.get("website"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            full_name=payload.get("full_name"),
            title=payload.get("title"),
            email=payload.get("email", ""),
            linkedin_url=payload.get("linkedin_url"),
            location=payload.get("location"),
            company_size=payload.get("company_size"),
            lead_source=payload.get("lead_source", "worker_tool"),
            enrichment_json=payload.get("enrichment_json") if isinstance(payload.get("enrichment_json"), dict) else {},
        ),
    )
    context.db.flush()
    return {"lead_id": str(lead.id), "campaign_id": str(lead.campaign_id) if lead.campaign_id else None}


def _tool_internal_note_writer(context: WorkerToolRuntimeContext, payload: dict[str, Any]) -> dict[str, Any]:
    note = str(payload.get("note", "")).strip()
    if not note:
        raise ValueError("note is required")
    log_audit_event(
        context.db,
        workspace_id=context.workspace_id,
        actor_type="system",
        actor_id="worker_tool_runtime",
        event_name="internal_note_written",
        payload={
            "note": note,
            "note_type": str(payload.get("note_type", "general")),
            "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            "run_id": str(context.run_id),
            "instance_id": str(context.instance_id),
        },
    )
    return {"stored": True}


def get_default_worker_tool_registry() -> WorkerToolRegistry:
    registry = WorkerToolRegistry()
    registry.register_handler("email_sender", _tool_email_sender)
    registry.register_handler("sms_sender", _tool_sms_sender)
    registry.register_handler("webhook_caller", _tool_webhook_caller)
    registry.register_handler("crm_updater", _tool_crm_updater)
    registry.register_handler("calendar_scheduler", _tool_calendar_scheduler)
    registry.register_handler("lead_recorder", _tool_lead_recorder)
    registry.register_handler("internal_note_writer", _tool_internal_note_writer)
    return registry


def invoke_tool_calls(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    instance_id: uuid.UUID,
    template_id: uuid.UUID,
    worker_id: uuid.UUID,
    run_id: uuid.UUID,
    tool_calls: list[dict[str, Any]],
    allowed_tool_slugs: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry = get_default_worker_tool_registry()
    allowed_set = set(allowed_tool_slugs)
    context = WorkerToolRuntimeContext(
        db=db,
        workspace_id=workspace_id,
        instance_id=instance_id,
        template_id=template_id,
        worker_id=worker_id,
        run_id=run_id,
    )
    results: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        slug = str(call.get("tool", "")).strip()
        payload = call.get("input", {})
        if not slug:
            continue
        if slug not in allowed_set:
            rejected.append({"tool": slug, "reason": "tool_not_allowed"})
            continue
        invocation = registry.invoke(context, tool_slug=slug, payload=payload if isinstance(payload, dict) else {})
        if invocation.success:
            results.append({"tool": slug, "success": True, "output": invocation.output})
        else:
            rejected.append({"tool": slug, "reason": invocation.error or "tool_invocation_failed"})
    return results, rejected

