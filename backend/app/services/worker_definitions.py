from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    WorkerModerationStatus,
    WorkerPricingType,
    WorkerTemplate,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
)
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
    {
        "template_key": "system-real-estate-deal-finder-worker",
        "name": "Real Estate Deal Finder Worker",
        "slug": "real-estate-deal-finder-worker",
        "short_description": "Finds high-potential real estate opportunities and prepares structured deal briefs.",
        "description": (
            "A real estate intelligence template focused on identifying deal candidates, highlighting underwriting"
            " signals, and preparing concise next-step recommendations for acquisition teams."
        ),
        "category": "real_estate",
        "worker_type": "custom_worker",
        "worker_category": "real_estate",
        "plan_version": "real_estate_v1",
        "instructions": (
            "Act as a real estate deal sourcing analyst. Prioritize actionable opportunities, summarize risk factors,"
            " and maintain clean structured notes for operator review."
        ),
        "model_name": "mock-ai-v1",
        "config_json": {
            "mission": "Source and summarize qualified real estate deal opportunities.",
            "target_markets": ["Texas", "Florida", "Arizona"],
            "asset_types": ["multifamily", "light industrial"],
            "min_cap_rate": 0.055,
        },
        "capabilities_json": {
            "deal_signal_analysis": True,
            "market_snapshot": True,
            "opportunity_scoring": True,
        },
        "actions_json": ["research_selected_leads", "record_optimization_signals"],
        "tools_json": ["lead_recorder", "internal_note_writer"],
        "tags_json": ["real-estate", "deals", "sourcing"],
    },
]

SYSTEM_TEMPLATE_SEEDS.extend(
    [
        {
            "template_key": "starter-deal-analyzer-worker",
            "name": "Deal Analyzer",
            "slug": "deal-analyzer-worker",
            "short_description": "Analyzes property opportunities and returns a structured underwriting summary.",
            "description": "Evaluates candidate deals, highlights upside and risk factors, and produces operator-ready analysis notes.",
            "category": "real_estate",
            "worker_type": "custom_worker",
            "worker_category": "real_estate",
            "plan_version": "launch_v1",
            "instructions": "Review provided property context, score attractiveness, and produce concise acquisition guidance.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Analyze property deals", "input_examples": [{"price": 1200000, "noi": 92000}]},
            "capabilities_json": {"underwriting_summary": True, "risk_scoring": True},
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["real-estate", "analysis", "underwriting"],
            "usage_examples_json": [{"input": "Multifamily listing details", "output": "Cap rate + risk summary"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 1,
        },
        {
            "template_key": "starter-listing-generator-worker",
            "name": "Listing Generator",
            "slug": "listing-generator-worker",
            "short_description": "Turns property notes into polished listing copy for agents and teams.",
            "description": "Generates structured listing drafts with value highlights, neighborhood context, and CTA-ready summaries.",
            "category": "real_estate",
            "worker_type": "custom_worker",
            "worker_category": "real_estate",
            "plan_version": "launch_v1",
            "instructions": "Generate concise listing content grounded in provided property details only.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate listing copy", "input_examples": [{"beds": 4, "baths": 3, "sqft": 2200}]},
            "capabilities_json": {"listing_copy": True, "tone_variants": True},
            "actions_json": ["generate_messages_for_selected_leads"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["real-estate", "content", "listings"],
            "usage_examples_json": [{"input": "Property attributes + neighborhood notes", "output": "MLS-ready draft"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 1900,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "featured_rank": 2,
        },
        {
            "template_key": "starter-seller-outreach-writer-worker",
            "name": "Seller Outreach Writer",
            "slug": "seller-outreach-writer-worker",
            "short_description": "Creates personalized seller outreach sequences for real estate lead generation.",
            "description": "Builds short, personalized outreach messages with compliant tone and clear next-step CTAs.",
            "category": "real_estate",
            "worker_type": "custom_worker",
            "worker_category": "real_estate",
            "plan_version": "launch_v1",
            "instructions": "Draft concise outreach messaging under 120 words with one clear CTA.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate seller outreach", "input_examples": [{"owner_type": "absentee", "zip": "75001"}]},
            "capabilities_json": {"outreach_copy": True, "follow_up_variants": True},
            "actions_json": ["generate_messages_for_selected_leads", "dispatch_messages"],
            "tools_json": ["email_sender", "internal_note_writer"],
            "tags_json": ["real-estate", "outbound", "seller-leads"],
            "usage_examples_json": [{"input": "Lead profile + property notes", "output": "3-step outreach sequence"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-blog-generator-worker",
            "name": "Blog Generator",
            "slug": "blog-generator-worker",
            "short_description": "Produces structured B2B blog drafts from brief inputs.",
            "description": "Creates SEO-aware article drafts with outlines, key points, and CTA sections for fast publishing.",
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "launch_v1",
            "instructions": "Generate practical blog drafts with clear headings and concise paragraphs.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate blog drafts", "input_examples": [{"topic": "AI SDR workflows"}]},
            "capabilities_json": {"long_form_generation": True, "outline_generation": True},
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["marketing", "content", "seo"],
            "usage_examples_json": [{"input": "Topic + target persona", "output": "1200-word first draft"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 1200,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 3,
        },
        {
            "template_key": "starter-ad-copy-generator-worker",
            "name": "Ad Copy Generator",
            "slug": "ad-copy-generator-worker",
            "short_description": "Builds ad copy variants for paid channels with crisp CTA framing.",
            "description": "Generates short-form ad variants for campaigns across awareness and conversion intents.",
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "launch_v1",
            "instructions": "Generate concise ad variants, emphasizing clarity and one conversion goal per asset.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate ad copy", "input_examples": [{"offer": "Free audit", "persona": "CMO"}]},
            "capabilities_json": {"ad_variants": True, "cta_generation": True},
            "actions_json": ["generate_messages_for_selected_leads"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["ads", "copywriting", "marketing"],
            "usage_examples_json": [{"input": "Offer + audience + channel", "output": "10 ad variants"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-seo-brief-builder-worker",
            "name": "SEO Brief Builder",
            "slug": "seo-brief-builder-worker",
            "short_description": "Creates content briefs with target terms and intent structure.",
            "description": "Assembles practical SEO briefs with search intent, section guidance, and optimization notes.",
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "launch_v1",
            "instructions": "Produce SEO briefs with explicit target query, intent, and section-level recommendations.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate SEO briefs", "input_examples": [{"keyword": "AI outbound automation"}]},
            "capabilities_json": {"seo_briefs": True, "intent_mapping": True},
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["seo", "content-strategy", "marketing"],
            "usage_examples_json": [{"input": "Primary keyword + audience", "output": "SEO article brief"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 1500,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-cold-email-writer-worker",
            "name": "Cold Email Writer",
            "slug": "cold-email-writer-worker",
            "short_description": "Drafts short personalized outbound emails with clear CTA.",
            "description": "Creates initial cold email drafts and follow-up variants grounded in lead and company context.",
            "category": "sales",
            "worker_type": "custom_worker",
            "worker_category": "sales",
            "plan_version": "launch_v1",
            "instructions": "Write concise outbound emails under 120 words and avoid unverifiable claims.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Draft outbound emails", "input_examples": [{"persona": "VP Sales", "pain_point": "pipeline visibility"}]},
            "capabilities_json": {"email_drafting": True, "followup_generation": True},
            "actions_json": ["generate_messages_for_selected_leads", "dispatch_messages"],
            "tools_json": ["email_sender", "internal_note_writer"],
            "tags_json": ["sales", "outbound", "email"],
            "usage_examples_json": [{"input": "Lead + company profile", "output": "initial + 2 follow-ups"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 4,
        },
        {
            "template_key": "starter-lead-qualification-assistant-worker",
            "name": "Lead Qualification Assistant",
            "slug": "lead-qualification-assistant-worker",
            "short_description": "Scores lead fit and recommends next best actions for reps.",
            "description": "Evaluates incoming leads against ICP criteria and produces qualification notes and routing guidance.",
            "category": "sales",
            "worker_type": "custom_worker",
            "worker_category": "sales",
            "plan_version": "launch_v1",
            "instructions": "Score lead quality against configured ICP and summarize confidence with reasons.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Score lead fit", "input_examples": [{"industry": "SaaS", "employees": 180}]},
            "capabilities_json": {"fit_scoring": True, "routing_recommendations": True},
            "actions_json": ["select_eligible_leads", "research_selected_leads", "record_optimization_signals"],
            "tools_json": ["lead_recorder", "internal_note_writer"],
            "tags_json": ["sales", "lead-qualification", "pipeline"],
            "usage_examples_json": [{"input": "Lead record set", "output": "priority tiers with rationale"}],
            "pricing_type": WorkerPricingType.SUBSCRIPTION.value,
            "price_cents": 2900,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-follow-up-sequence-generator-worker",
            "name": "Follow-Up Sequence Generator",
            "slug": "follow-up-sequence-generator-worker",
            "short_description": "Generates follow-up sequence variants based on reply context.",
            "description": "Creates scenario-aware follow-up sequences for interested, neutral, and no-response leads.",
            "category": "sales",
            "worker_type": "custom_worker",
            "worker_category": "sales",
            "plan_version": "launch_v1",
            "instructions": "Generate practical follow-up sequences and adapt tone to conversation context.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate follow-up sequences", "input_examples": [{"scenario": "no_response"}]},
            "capabilities_json": {"followup_sequences": True, "reply_context_adaptation": True},
            "actions_json": ["generate_messages_for_selected_leads", "monitor_outbound_events"],
            "tools_json": ["email_sender", "internal_note_writer"],
            "tags_json": ["sales", "follow-up", "engagement"],
            "usage_examples_json": [{"input": "Thread context", "output": "3-step follow-up plan"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 1700,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-competitor-snapshot-worker",
            "name": "Competitor Snapshot Worker",
            "slug": "competitor-snapshot-worker",
            "short_description": "Builds concise competitor snapshots and positioning notes.",
            "description": "Produces quick competitor analysis summaries with strengths, gaps, and positioning suggestions.",
            "category": "research",
            "worker_type": "custom_worker",
            "worker_category": "research",
            "plan_version": "launch_v1",
            "instructions": "Create balanced competitor snapshots using provided data and clearly mark assumptions.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Generate competitor snapshots", "input_examples": [{"competitors": ["A", "B", "C"]}]},
            "capabilities_json": {"competitor_analysis": True, "positioning_summary": True},
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["research", "competition", "positioning"],
            "usage_examples_json": [{"input": "Competitor URLs + product notes", "output": "snapshot matrix"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-market-research-worker",
            "name": "Market Research Worker",
            "slug": "market-research-worker",
            "short_description": "Generates market briefs and trend summaries for strategic planning.",
            "description": "Creates market overviews, trend signals, and opportunity hypotheses from structured inputs.",
            "category": "research",
            "worker_type": "custom_worker",
            "worker_category": "research",
            "plan_version": "launch_v1",
            "instructions": "Assemble concise market briefs with explicit evidence and assumptions.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Build market briefs", "input_examples": [{"segment": "B2B fintech"}]},
            "capabilities_json": {"market_summary": True, "trend_detection": True},
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["research", "market-intelligence", "strategy"],
            "usage_examples_json": [{"input": "Segment + geography", "output": "market brief with risks"}],
            "pricing_type": WorkerPricingType.SUBSCRIPTION.value,
            "price_cents": 3900,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 5,
        },
        {
            "template_key": "starter-sop-draft-generator-worker",
            "name": "SOP Draft Generator",
            "slug": "sop-draft-generator-worker",
            "short_description": "Turns process notes into structured SOP drafts.",
            "description": "Creates standard operating procedure drafts with roles, steps, and quality checks.",
            "category": "operations",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "launch_v1",
            "instructions": "Transform rough process notes into practical SOP documents with clear sections.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Draft SOPs", "input_examples": [{"process": "Lead handoff"}]},
            "capabilities_json": {"sop_generation": True, "qa_checklists": True},
            "actions_json": ["record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["operations", "sop", "documentation"],
            "usage_examples_json": [{"input": "Workflow notes", "output": "step-by-step SOP"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 1400,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-meeting-notes-summarizer-worker",
            "name": "Meeting Notes Summarizer",
            "slug": "meeting-notes-summarizer-worker",
            "short_description": "Summarizes meeting transcripts into decisions and actions.",
            "description": "Converts call notes and transcripts into concise summaries, risks, and owner-assigned next steps.",
            "category": "operations",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "launch_v1",
            "instructions": "Summarize notes accurately and extract concrete follow-up actions.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Summarize meetings", "input_examples": [{"type": "sales_call"}]},
            "capabilities_json": {"summarization": True, "action_extraction": True},
            "actions_json": ["record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["operations", "meetings", "summaries"],
            "usage_examples_json": [{"input": "Transcript", "output": "summary + owner action list"}],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
        {
            "template_key": "starter-task-extraction-worker",
            "name": "Task Extraction Worker",
            "slug": "task-extraction-worker",
            "short_description": "Extracts actionable tasks from freeform notes and conversations.",
            "description": "Finds commitments, deadlines, and owners from unstructured notes and outputs task-ready lists.",
            "category": "operations",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "launch_v1",
            "instructions": "Extract explicit tasks only, with owner and due-date hints when present.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "Extract tasks from notes", "input_examples": [{"source": "weekly standup notes"}]},
            "capabilities_json": {"task_extraction": True, "owner_mapping": True},
            "actions_json": ["record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["operations", "tasks", "execution"],
            "usage_examples_json": [{"input": "Unstructured notes", "output": "task list with priorities"}],
            "pricing_type": WorkerPricingType.ONE_TIME.value,
            "price_cents": 900,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
        },
    ]
)


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
    template.visibility = seed.get("visibility", WorkerTemplateVisibility.PUBLIC.value)
    template.status = WorkerTemplateStatus.ACTIVE.value
    template.instructions = seed["instructions"]
    template.model_name = seed["model_name"]
    template.default_config_json = dict(seed["config_json"])
    template.config_json = dict(seed["config_json"])
    template.capabilities_json = dict(seed["capabilities_json"])
    template.allowed_actions = list(seed["actions_json"])
    template.actions_json = list(seed["actions_json"])
    template.tools_json = list(seed["tools_json"])
    template.prompt_profile = str(seed.get("prompt_profile", "sales"))
    template.memory_enabled = True
    template.chain_enabled = bool(seed.get("chain_enabled", False))
    template.is_system_template = True
    template.is_public = True
    template.is_marketplace_listed = bool(seed.get("is_marketplace_listed", False))
    template.is_featured = bool(seed.get("is_featured", False))
    template.featured_rank = int(seed.get("featured_rank", 0) or 0)
    template.is_active = True
    template.pricing_type = str(seed.get("pricing_type", WorkerPricingType.INTERNAL.value))
    template.price_cents = int(seed.get("price_cents", 0) or 0)
    if template.pricing_type == WorkerPricingType.FREE.value:
        template.price_cents = 0
    template.currency = str(seed.get("currency", "USD")).upper()
    template.install_count = int(template.install_count or 0)
    template.rating_avg = float(template.rating_avg or 0.0)
    template.rating_count = int(template.rating_count or 0)
    template.tags_json = list(seed["tags_json"])
    template.usage_examples_json = list(seed.get("usage_examples_json", []))
    template.screenshots_json = list(seed.get("screenshots_json", []))
    template.moderation_status = WorkerModerationStatus.APPROVED.value


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
