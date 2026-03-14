from typing import Any

from sqlalchemy.orm import Session

from app.models import WorkerPricingType, WorkerTemplate, WorkerTemplateStatus, WorkerTemplateVisibility
from app.workers.definitions import WorkerDefinition, get_worker_definition, list_worker_definitions


CORE_OUTBOUND_ACTIONS = [
    "select_eligible_leads",
    "research_selected_leads",
    "generate_messages_for_selected_leads",
    "dispatch_messages",
    "monitor_outbound_events",
    "record_optimization_signals",
]

SYSTEM_TEMPLATE_SEEDS: list[dict[str, Any]] = [
    {
        "template_key": "system-sales-outreach-worker",
        "name": "Sales Outreach Worker",
        "slug": "sales-outreach-worker",
        "short_description": "Runs outbound research, drafts outreach, and supports follow-through to meetings.",
        "description": (
            "A production-ready outbound mission template that researches qualified accounts, drafts personalized"
            " outreach, and maintains delivery/reply awareness for the sales team."
        ),
        "category": "sales",
        "worker_type": "ai_sales_worker",
        "worker_category": "go_to_market",
        "plan_version": "sales_v1",
        "instructions": (
            "Operate as an AI outbound teammate. Prioritize relevant prospects, produce concise and professional"
            " messages, keep clear notes, and suggest next best actions after each run."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Generate qualified pipeline conversations from outbound campaigns.",
            "target_industry": "B2B SaaS",
            "target_roles": ["VP Sales", "Head of Growth", "Revenue Operations"],
            "target_locations": ["United States"],
            "company_size_range": "50-1000",
        },
        "capabilities_json": {
            "lead_research": True,
            "personalized_outreach": True,
            "reply_monitoring": True,
            "meeting_signal_detection": True,
        },
        "actions_json": CORE_OUTBOUND_ACTIONS,
        "tools_json": ["email_sender", "lead_recorder", "calendar_scheduler", "internal_note_writer"],
        "tags_json": ["sales", "outbound", "pipeline"],
    },
    {
        "template_key": "system-lead-finder-worker",
        "name": "Lead Finder Worker",
        "slug": "lead-finder-worker",
        "short_description": "Continuously identifies and enriches likely-fit leads for campaign queues.",
        "description": (
            "A prospect discovery template focused on identifying qualified leads, documenting fit signals,"
            " and preparing clean lead records for downstream outreach."
        ),
        "category": "prospecting",
        "worker_type": "ai_research_worker",
        "worker_category": "research",
        "plan_version": "research_v1",
        "instructions": (
            "Find high-fit lead profiles aligned with the mission configuration. Prefer quality over volume,"
            " record concise rationale, and surface only actionable prospects."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Discover qualified leads and create research-backed lead records.",
            "target_industry": "B2B Software",
            "ideal_seniority": ["Director", "VP", "Head"],
            "regions": ["North America"],
        },
        "capabilities_json": {
            "prospect_discovery": True,
            "lead_enrichment": True,
            "fit_scoring": True,
        },
        "actions_json": ["select_eligible_leads", "research_selected_leads", "record_optimization_signals"],
        "tools_json": ["lead_recorder", "internal_note_writer"],
        "tags_json": ["lead-gen", "prospecting", "research"],
    },
    {
        "template_key": "system-customer-support-worker",
        "name": "Customer Support Worker",
        "slug": "customer-support-worker",
        "short_description": "Triage-oriented support assistant for recurring issue detection and response drafting.",
        "description": (
            "A support operations template that helps classify incoming issues, draft useful response guidance,"
            " and flag urgent escalation paths."
        ),
        "category": "support",
        "worker_type": "ai_support_worker",
        "worker_category": "support",
        "plan_version": "support_v1",
        "instructions": (
            "Act as a support co-pilot. Summarize issues clearly, recommend concise customer-safe responses,"
            " and label priority/risk for handoff to human owners."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Improve support response quality and escalation clarity.",
            "default_priority_policy": "prioritize billing, outage, and data-risk incidents",
        },
        "capabilities_json": {
            "issue_classification": True,
            "response_drafting": True,
            "escalation_flagging": True,
        },
        "actions_json": ["monitor_outbound_events", "record_optimization_signals"],
        "tools_json": ["internal_note_writer"],
        "tags_json": ["support", "triage", "customer-success"],
    },
    {
        "template_key": "system-marketing-campaign-worker",
        "name": "Marketing Campaign Worker",
        "slug": "marketing-campaign-worker",
        "short_description": "Plans and drafts campaign messaging variants with channel-safe execution notes.",
        "description": (
            "A campaign operations template for drafting variant messaging, maintaining experiment context,"
            " and supporting repeatable campaign optimization loops."
        ),
        "category": "marketing",
        "worker_type": "custom_worker",
        "worker_category": "marketing",
        "plan_version": "marketing_v1",
        "instructions": (
            "Support campaign experimentation with concise messaging variants and clear rationale."
            " Keep outputs structured so operators can approve and launch quickly."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Generate and optimize campaign messaging with measurable iteration notes.",
            "channels": ["email"],
            "tone": "helpful and direct",
        },
        "capabilities_json": {
            "message_variant_generation": True,
            "campaign_optimization_signals": True,
        },
        "actions_json": ["generate_messages_for_selected_leads", "dispatch_messages", "record_optimization_signals"],
        "tools_json": ["email_sender", "internal_note_writer"],
        "tags_json": ["marketing", "campaigns", "optimization"],
    },
    {
        "template_key": "system-meeting-booker-worker",
        "name": "Meeting Booker Worker",
        "slug": "meeting-booker-worker",
        "short_description": "Coordinates meeting-booking follow-through for qualified, interested conversations.",
        "description": (
            "A scheduling-focused template that tracks positive reply intent, prepares booking-ready context,"
            " and coordinates calendar actions for fast handoff."
        ),
        "category": "meetings",
        "worker_type": "custom_worker",
        "worker_category": "operations",
        "plan_version": "meetings_v1",
        "instructions": (
            "Monitor interested signals, summarize context for booking, and coordinate meeting workflows"
            " while preserving clear run notes for account owners."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Convert interested conversations into scheduled meetings efficiently.",
            "meeting_duration_minutes": 30,
            "timezone": "UTC",
        },
        "capabilities_json": {
            "interest_signal_triage": True,
            "meeting_workflow_support": True,
            "calendar_coordination": True,
        },
        "actions_json": ["monitor_outbound_events", "dispatch_messages", "record_optimization_signals"],
        "tools_json": ["calendar_scheduler", "email_sender", "internal_note_writer"],
        "tags_json": ["meetings", "scheduling", "pipeline"],
    },
]


def _upsert_definition_template(db: Session, definition: WorkerDefinition) -> None:
    template = (
        db.query(WorkerTemplate)
        .filter(WorkerTemplate.template_key == definition.worker_type, WorkerTemplate.workspace_id.is_(None))
        .first()
    )
    if not template:
        template = WorkerTemplate(
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
        db.add(template)
        return
    template.display_name = definition.display_name
    template.worker_type = definition.worker_type
    template.worker_category = definition.worker_category
    template.plan_version = definition.plan_version
    template.default_config_json = dict(definition.default_config)
    template.allowed_actions = list(definition.allowed_actions)
    template.prompt_profile = definition.prompt_profile
    template.is_public = definition.public_available
    template.is_active = True
    template.workspace_id = None


def _upsert_system_template(db: Session, seed: dict[str, Any]) -> None:
    template = db.query(WorkerTemplate).filter(WorkerTemplate.template_key == seed["template_key"]).first()
    if not template:
        template = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.workspace_id.is_(None), WorkerTemplate.slug == seed["slug"])
            .first()
        )
    if not template:
        template = WorkerTemplate(template_key=seed["template_key"])
        db.add(template)

    template.workspace_id = None
    template.creator_user_id = None
    template.name = seed["name"]
    template.slug = seed["slug"]
    template.template_key = seed["template_key"]
    template.display_name = seed["name"]
    template.short_description = seed["short_description"]
    template.description = seed["description"]
    template.category = seed["category"]
    template.worker_type = seed["worker_type"]
    template.worker_category = seed["worker_category"]
    template.plan_version = seed["plan_version"]
    template.visibility = WorkerTemplateVisibility.PUBLIC.value
    template.status = WorkerTemplateStatus.ACTIVE.value
    template.instructions = seed["instructions"]
    template.model_name = seed["model_name"]
    template.default_config_json = dict(seed["config_json"])
    template.config_json = dict(seed["config_json"])
    template.capabilities_json = dict(seed["capabilities_json"])
    template.allowed_actions = list(seed["actions_json"])
    template.actions_json = list(seed["actions_json"])
    template.tools_json = list(seed["tools_json"])
    template.prompt_profile = "sales"
    template.memory_enabled = True
    template.chain_enabled = False
    template.is_system_template = True
    template.is_public = True
    template.is_marketplace_listed = False
    template.is_active = True
    template.pricing_type = WorkerPricingType.INTERNAL.value
    template.price_cents = 0
    template.currency = "USD"
    template.install_count = int(template.install_count or 0)
    template.rating_avg = float(template.rating_avg or 0.0)
    template.rating_count = int(template.rating_count or 0)
    template.tags_json = list(seed["tags_json"])


def ensure_builtin_worker_templates(db: Session) -> None:
    for definition in list_worker_definitions(include_internal=True):
        _upsert_definition_template(db, definition)
    for seed in SYSTEM_TEMPLATE_SEEDS:
        _upsert_system_template(db, seed)
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
