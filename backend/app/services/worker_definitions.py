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

INTERNAL_STACK_SHARED_TAGS = [
    "thorpe-workforce",
    "internal-stack",
    "founder-os",
    "startup-ops",
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

SYSTEM_TEMPLATE_SEEDS.extend(
    [
        {
            "template_key": "internal-chief-marketing-worker",
            "name": "Chief Marketing Worker",
            "slug": "chief-marketing-worker",
            "short_description": "Builds daily startup growth campaigns with channel-ready assets and CTA guidance.",
            "description": (
                "A founder-focused marketing strategist that turns goals and audience context into practical campaign"
                " plans, social copy, outreach messages, and next-step execution guidance."
            ),
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act like a startup growth strategist for Thorpe Workforce. Produce practical campaign assets aligned"
                " to audience and platform fit. Keep messaging compelling, avoid spam patterns, and include clear CTA"
                " recommendations. If mention_self_as_worker is true, naturally include one short line that the output"
                " was generated by a Thorpe Workforce AI worker."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Generate daily marketing campaigns for Thorpe Workforce.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "target_audience": {"type": "string"},
                        "campaign_goal": {"type": "string"},
                        "platform": {"type": "string"},
                        "tone": {"type": "string"},
                        "offer_or_cta": {"type": "string"},
                        "key_message": {"type": "string"},
                        "mention_self_as_worker": {"type": "boolean"},
                    },
                    "required": [
                        "product_name",
                        "target_audience",
                        "campaign_goal",
                        "platform",
                        "tone",
                        "offer_or_cta",
                        "key_message",
                    ],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "campaign_summary": {"type": "string"},
                        "social_posts": {"type": "array"},
                        "outreach_messages": {"type": "array"},
                        "content_ideas": {"type": "array"},
                        "next_steps": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Chief Marketing Worker. Build a compelling but credible campaign with practical assets."
                    " Optimize for audience and platform fit, keep tone aligned to input, and include actionable CTAs."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "product_name": "Thorpe Workforce",
                        "target_audience": "real estate investors",
                        "campaign_goal": "attract early users",
                        "platform": "LinkedIn",
                        "tone": "professional",
                        "offer_or_cta": "Request demo",
                        "key_message": "AI workers automate business tasks",
                        "mention_self_as_worker": True,
                    }
                },
            },
            "capabilities_json": {
                "campaign_planning": True,
                "social_copy_generation": True,
                "startup_growth_strategy": True,
            },
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer", "webhook_caller"],
            "tags_json": [
                "marketing",
                "growth",
                "social-media",
                "startup",
                "campaign",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "LinkedIn launch sprint",
                    "input": {
                        "product_name": "Thorpe Workforce",
                        "target_audience": "real estate investors",
                        "campaign_goal": "attract early users",
                        "platform": "LinkedIn",
                        "tone": "professional",
                        "offer_or_cta": "Request demo",
                        "key_message": "AI workers automate business tasks",
                        "mention_self_as_worker": True,
                    },
                    "output_highlights": [
                        "5 post thread ideas",
                        "2 founder outreach variants",
                        "clear CTA sequencing",
                    ],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 6,
            "icon": "megaphone",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-user-feedback-intelligence-worker",
            "name": "User Feedback Intelligence Worker",
            "slug": "user-feedback-intelligence-worker",
            "short_description": "Clusters product feedback and prioritizes high-impact insights for roadmap decisions.",
            "description": (
                "A product insights analyst that summarizes customer feedback, surfaces friction patterns, flags churn"
                " risks, and recommends actionable priorities by likely business impact."
            ),
            "category": "research",
            "worker_type": "custom_worker",
            "worker_category": "research",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a product insights analyst. Cluster similar feedback, identify repeated blockers and requested"
                " features, and prioritize recommendations by likely impact on retention, adoption, and revenue."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Summarize user feedback and identify product insights.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "feedback_items": {"type": "array"},
                        "app_usage_notes": {"type": "array"},
                        "analysis_goal": {"type": "string"},
                        "time_period": {"type": "string"},
                    },
                    "required": ["feedback_items", "analysis_goal", "time_period"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "top_themes": {"type": "array"},
                        "friction_points": {"type": "array"},
                        "requested_features": {"type": "array"},
                        "churn_risks": {"type": "array"},
                        "recommended_actions": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are User Feedback Intelligence Worker. Synthesize feedback into themes and prioritize action"
                    " based on impact and feasibility."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "feedback_items": [
                            "Need better campaign analytics",
                            "Worker setup felt confusing",
                            "Wanted more marketplace quality signals",
                        ],
                        "app_usage_notes": ["drop-off after onboarding step 2", "repeat visits to marketplace page"],
                        "analysis_goal": "prioritize Q2 roadmap",
                        "time_period": "last 30 days",
                    }
                },
            },
            "capabilities_json": {
                "theme_clustering": True,
                "friction_analysis": True,
                "impact_prioritization": True,
            },
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["feedback", "product", "insights", "churn", "roadmap", *INTERNAL_STACK_SHARED_TAGS],
            "usage_examples_json": [
                {
                    "title": "Weekly feedback digest",
                    "input": {
                        "feedback_items": ["slow loading for worker runs", "need better review queue"],
                        "analysis_goal": "identify fast retention wins",
                        "time_period": "week_to_date",
                    },
                    "output_highlights": ["top churn risks", "quick-win recommendations", "prioritized feature demand"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "message-square",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-marketplace-curator-worker",
            "name": "Marketplace Curator Worker",
            "slug": "marketplace-curator-worker",
            "short_description": "Finds category gaps and recommends high-conversion worker opportunities.",
            "description": (
                "A marketplace strategy worker that evaluates installs and creator activity, then recommends trending"
                " categories, underserved segments, and worker packs likely to improve growth and monetization."
            ),
            "category": "automation",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act like a marketplace strategist. Analyze install patterns, category performance, and creator supply."
                " Recommend workers and bundles that can improve install velocity and revenue quality."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Analyze marketplace performance and recommend new workers, packs, and categories.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "worker_catalog": {"type": "array"},
                        "install_data": {"type": "array"},
                        "category_data": {"type": "array"},
                        "creator_activity": {"type": "array"},
                        "curation_goal": {"type": "string"},
                    },
                    "required": ["worker_catalog", "install_data", "category_data", "curation_goal"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "trending_categories": {"type": "array"},
                        "under_served_categories": {"type": "array"},
                        "recommended_new_workers": {"type": "array"},
                        "recommended_worker_packs": {"type": "array"},
                        "featured_worker_candidates": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Marketplace Curator Worker. Identify demand/supply gaps and recommend worker portfolio"
                    " moves with install and monetization potential."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "worker_catalog": ["sales-outreach-worker", "blog-generator-worker"],
                        "install_data": [{"category": "marketing", "installs": 120}],
                        "category_data": [{"category": "operations", "growth_rate": 0.22}],
                        "creator_activity": [{"creator": "alpha", "workers_published": 3}],
                        "curation_goal": "increase paid installs in 60 days",
                    }
                },
            },
            "capabilities_json": {
                "gap_analysis": True,
                "portfolio_recommendations": True,
                "bundling_strategy": True,
            },
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": [
                "marketplace",
                "curation",
                "strategy",
                "product-gap",
                "bundles",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "Marketplace growth planning",
                    "input": {"curation_goal": "expand creator monetization by category"},
                    "output_highlights": ["underserved categories", "new worker suggestions", "feature list shortlist"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "compass",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-creator-recruitment-worker",
            "name": "Creator Recruitment Worker",
            "slug": "creator-recruitment-worker",
            "short_description": "Builds creator acquisition campaigns and persuasive outreach for marketplace growth.",
            "description": (
                "A creator ecosystem manager that generates recruitment messaging, post copy, and follow-up sequences"
                " to attract strong builders into the Thorpe Workforce marketplace."
            ),
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a creator ecosystem manager. Write persuasive but credible recruitment content, highlight"
                " creator benefits clearly, and include revenue-share details only when mention_revenue_share is true."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Generate creator acquisition campaigns and outreach.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_creator_type": {"type": "string"},
                        "platform": {"type": "string"},
                        "recruitment_goal": {"type": "string"},
                        "incentive_offer": {"type": "string"},
                        "tone": {"type": "string"},
                        "mention_revenue_share": {"type": "boolean"},
                    },
                    "required": [
                        "target_creator_type",
                        "platform",
                        "recruitment_goal",
                        "incentive_offer",
                        "tone",
                    ],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "outreach_messages": {"type": "array"},
                        "recruitment_post": {"type": "string"},
                        "creator_pitch": {"type": "string"},
                        "follow_up_sequence": {"type": "array"},
                        "targeting_suggestions": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Creator Recruitment Worker. Drive quality creator acquisition with clear value framing and"
                    " actionable channel-specific outreach."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "target_creator_type": "AI automation builders",
                        "platform": "X",
                        "recruitment_goal": "increase active creators",
                        "incentive_offer": "featured launch placement",
                        "tone": "founder-friendly",
                        "mention_revenue_share": True,
                    }
                },
            },
            "capabilities_json": {
                "creator_outreach": True,
                "ecosystem_messaging": True,
                "followup_planning": True,
            },
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer", "webhook_caller"],
            "tags_json": [
                "creator",
                "recruitment",
                "outreach",
                "marketplace-growth",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "Creator pipeline outreach",
                    "input": {"target_creator_type": "prompt engineers", "platform": "LinkedIn"},
                    "output_highlights": ["creator pitch", "2 follow-up variants", "channel targeting notes"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "users",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-sales-outreach-worker",
            "name": "Sales Outreach Worker",
            "slug": "internal-sales-outreach-worker",
            "short_description": "Creates concise founder-led acquisition outreach optimized for replies.",
            "description": (
                "An early-stage sales strategist that drafts short outreach across DM and email channels with"
                " objection handling and follow-up guidance focused on conversation starts."
            ),
            "category": "sales",
            "worker_type": "custom_worker",
            "worker_category": "sales",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act like a founder-led startup sales strategist. Keep outreach concise, human, and non-pushy."
                " Optimize for responses and conversation quality rather than hard-close tactics."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Create customer acquisition outreach for early adopters.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_customer_profile": {"type": "string"},
                        "product_offer": {"type": "string"},
                        "outreach_channel": {"type": "string"},
                        "use_case": {"type": "string"},
                        "tone": {"type": "string"},
                        "objection_to_address": {"type": "string"},
                    },
                    "required": [
                        "target_customer_profile",
                        "product_offer",
                        "outreach_channel",
                        "use_case",
                        "tone",
                    ],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "primary_message": {"type": "string"},
                        "short_dm_version": {"type": "string"},
                        "email_version": {"type": "string"},
                        "follow_up_message": {"type": "string"},
                        "objection_response": {"type": "string"},
                    },
                },
                "prompt_template": (
                    "You are Sales Outreach Worker. Write concise founder-style messaging with one clear next step and"
                    " practical objection handling."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "target_customer_profile": "small real estate investment teams",
                        "product_offer": "AI workers to automate repetitive operations",
                        "outreach_channel": "email",
                        "use_case": "faster lead follow-up",
                        "tone": "helpful",
                        "objection_to_address": "we already use CRM automation",
                    }
                },
            },
            "capabilities_json": {
                "founder_led_sales_copy": True,
                "objection_handling": True,
                "followup_generation": True,
            },
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": [
                "sales",
                "outreach",
                "early-users",
                "founder-led-sales",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "Early adopter outreach",
                    "input": {"target_customer_profile": "seed-stage SaaS operators", "outreach_channel": "email"},
                    "output_highlights": ["primary message", "DM variant", "objection response"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "mail",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-product-strategy-worker",
            "name": "Product Strategy Worker",
            "slug": "product-strategy-worker",
            "short_description": "Converts product signals into prioritized roadmap recommendations.",
            "description": (
                "A startup product strategist that weighs metrics, demand, and constraints to propose quick wins,"
                " strategic bets, and deliberate deprioritization decisions."
            ),
            "category": "research",
            "worker_type": "custom_worker",
            "worker_category": "research",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a startup product strategist. Prioritize opportunities using growth, retention, revenue,"
                " and implementation effort. Clearly separate quick wins from long-term bets."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Turn usage, demand, and platform context into roadmap recommendations.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_metrics": {"type": "object"},
                        "user_requests": {"type": "array"},
                        "business_goals": {"type": "array"},
                        "engineering_constraints": {"type": "array"},
                        "planning_horizon": {"type": "string"},
                    },
                    "required": ["product_metrics", "business_goals", "planning_horizon"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "top_opportunities": {"type": "array"},
                        "roadmap_recommendations": {"type": "array"},
                        "quick_wins": {"type": "array"},
                        "strategic_bets": {"type": "array"},
                        "deprioritized_items": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Product Strategy Worker. Build an execution-ready roadmap recommendation that balances"
                    " impact and implementation constraints."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "product_metrics": {"weekly_active_workspaces": 125, "install_to_run_rate": 0.53},
                        "user_requests": ["better analytics exports", "template cloning UX improvements"],
                        "business_goals": ["increase paid installs", "improve retention"],
                        "engineering_constraints": ["small backend team", "limited frontend bandwidth"],
                        "planning_horizon": "next 90 days",
                    }
                },
            },
            "capabilities_json": {
                "roadmap_prioritization": True,
                "quick_win_identification": True,
                "strategic_tradeoff_analysis": True,
            },
            "actions_json": ["research_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["strategy", "roadmap", "product", "prioritization", "growth", *INTERNAL_STACK_SHARED_TAGS],
            "usage_examples_json": [
                {
                    "title": "Quarterly planning",
                    "input": {"planning_horizon": "quarter", "business_goals": ["retention uplift"]},
                    "output_highlights": ["quick wins", "strategic bets", "deprioritized items"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 8,
            "icon": "target",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-content-marketing-worker",
            "name": "Content Marketing Worker",
            "slug": "content-marketing-worker",
            "short_description": "Creates long-form B2B content plans and drafts with strong educational framing.",
            "description": (
                "A SaaS content strategist that generates title options, outlines, draft copy, CTA blocks, and content"
                " repurposing ideas for blog, case study, newsletter, and thought-leadership workflows."
            ),
            "category": "content",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a B2B SaaS content strategist. Produce useful and credible long-form content with educational"
                " value, clear structure, and practical CTA guidance."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Create long-form content and content plans for Thorpe Workforce.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "audience": {"type": "string"},
                        "content_goal": {"type": "string"},
                        "content_format": {"type": "string"},
                        "core_topic": {"type": "string"},
                        "tone": {"type": "string"},
                        "product_context": {"type": "string"},
                    },
                    "required": ["audience", "content_goal", "content_format", "core_topic", "tone"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "title_options": {"type": "array"},
                        "outline": {"type": "array"},
                        "draft_content": {"type": "string"},
                        "cta_block": {"type": "string"},
                        "repurposing_ideas": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Content Marketing Worker. Write high-utility B2B SaaS content with clear structure and"
                    " educational framing before product positioning."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "audience": "startup founders",
                        "content_goal": "drive top-of-funnel demand",
                        "content_format": "blog",
                        "core_topic": "operating a startup with AI workers",
                        "tone": "clear and practical",
                        "product_context": "Thorpe Workforce Founder OS",
                    }
                },
            },
            "capabilities_json": {
                "long_form_content": True,
                "seo_friendly_outlines": True,
                "repurposing_plans": True,
            },
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["content", "blog", "seo", "case-study", "newsletter", *INTERNAL_STACK_SHARED_TAGS],
            "usage_examples_json": [
                {
                    "title": "Founder story article",
                    "input": {"content_format": "case-study", "core_topic": "internal AI worker stack"},
                    "output_highlights": ["title options", "structured outline", "CTA block"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "file-text",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-community-manager-worker",
            "name": "Community Manager Worker",
            "slug": "community-manager-worker",
            "short_description": "Drafts warm, discussion-friendly community replies and engagement prompts.",
            "description": (
                "A thoughtful community assistant that crafts clear responses, alternate variants, and follow-up"
                " prompts for community channels while keeping engagement constructive and helpful."
            ),
            "category": "marketing",
            "worker_type": "custom_worker",
            "worker_category": "marketing",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act like a startup community manager. Keep responses warm, clear, and conversation-friendly."
                " Mention Thorpe Workforce naturally only when include_product_mention is true and context supports it."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Generate community replies, updates, and discussion prompts.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "community_context": {"type": "string"},
                        "incoming_question_or_topic": {"type": "string"},
                        "response_goal": {"type": "string"},
                        "tone": {"type": "string"},
                        "include_product_mention": {"type": "boolean"},
                    },
                    "required": [
                        "community_context",
                        "incoming_question_or_topic",
                        "response_goal",
                        "tone",
                    ],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "suggested_reply": {"type": "string"},
                        "alternate_reply": {"type": "string"},
                        "follow_up_question": {"type": "string"},
                        "community_post_idea": {"type": "string"},
                    },
                },
                "prompt_template": (
                    "You are Community Manager Worker. Produce thoughtful responses that encourage useful discussion and"
                    " community trust."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "community_context": "Founder Slack community for SaaS operators",
                        "incoming_question_or_topic": "How do you prioritize AI automation projects?",
                        "response_goal": "spark practical discussion",
                        "tone": "friendly and practical",
                        "include_product_mention": True,
                    }
                },
            },
            "capabilities_json": {
                "community_reply_drafting": True,
                "engagement_prompting": True,
                "tone_control": True,
            },
            "actions_json": ["generate_messages_for_selected_leads", "record_optimization_signals"],
            "tools_json": ["internal_note_writer", "webhook_caller"],
            "tags_json": [
                "community",
                "engagement",
                "moderation",
                "replies",
                "social",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "Community Q&A response",
                    "input": {"incoming_question_or_topic": "best founder metrics?"},
                    "output_highlights": ["reply variant A/B", "follow-up prompt", "community post idea"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "messages-square",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-investor-update-worker",
            "name": "Investor Update Worker",
            "slug": "investor-update-worker",
            "short_description": "Drafts concise investor updates with milestones, metrics, risks, and asks.",
            "description": (
                "A founder relations assistant that converts startup performance context into clear investor-ready"
                " updates balancing optimism, transparency, and realistic risk communication."
            ),
            "category": "automation",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a startup founder relations assistant. Write concise and confident investor updates, keep"
                " metrics grounded in provided inputs, and clearly separate wins, risks, asks, and next milestones."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Draft investor updates and milestone summaries.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reporting_period": {"type": "string"},
                        "key_metrics": {"type": "object"},
                        "wins": {"type": "array"},
                        "challenges": {"type": "array"},
                        "asks": {"type": "array"},
                        "next_milestones": {"type": "array"},
                    },
                    "required": ["reporting_period", "key_metrics", "wins", "challenges", "next_milestones"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "executive_summary": {"type": "string"},
                        "metric_highlights": {"type": "array"},
                        "narrative_update": {"type": "string"},
                        "key_risks": {"type": "array"},
                        "asks_section": {"type": "string"},
                    },
                },
                "prompt_template": (
                    "You are Investor Update Worker. Generate an investor-ready update that is concise, transparent, and"
                    " action-oriented."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "reporting_period": "March 2026",
                        "key_metrics": {"new_workspaces": 31, "marketplace_installs": 212, "mrr_estimate": 4200},
                        "wins": ["launched creator analytics", "expanded internal worker stack"],
                        "challenges": ["staging postgres migration validation pending"],
                        "asks": ["intro to growth-stage marketplace operators"],
                        "next_milestones": ["launch Founder OS campaign", "improve paid conversion flow"],
                    }
                },
            },
            "capabilities_json": {
                "investor_reporting": True,
                "metric_storytelling": True,
                "risk_highlighting": True,
            },
            "actions_json": ["record_optimization_signals"],
            "tools_json": ["internal_note_writer"],
            "tags_json": ["investor", "update", "fundraising", "metrics", "reporting", *INTERNAL_STACK_SHARED_TAGS],
            "usage_examples_json": [
                {
                    "title": "Monthly investor note",
                    "input": {"reporting_period": "monthly"},
                    "output_highlights": ["executive summary", "metrics narrative", "asks section"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "icon": "line-chart",
            "chain_enabled": True,
        },
        {
            "template_key": "internal-operations-coordinator-worker",
            "name": "Operations Coordinator Worker",
            "slug": "operations-coordinator-worker",
            "short_description": "Generates daily/weekly operating briefs with priorities, blockers, and next actions.",
            "description": (
                "A startup chief-of-staff style worker that consolidates activity metrics and open issues into concise"
                " operating updates and actionable execution plans."
            ),
            "category": "automation",
            "worker_type": "custom_worker",
            "worker_category": "operations",
            "plan_version": "founder_os_v1",
            "instructions": (
                "Act as a startup operations coordinator. Summarize clearly, identify priorities and blockers, and"
                " finish with actionable next steps mapped to strategic priorities."
            ),
            "prompt_profile": "internal_ops",
            "model_name": "mock-ai-v1",
            "config_json": {
                "mission": "Produce daily or weekly operating briefings and action lists.",
                "stack_group": "Thorpe Workforce Internal Stack",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "new_users": {"type": "integer"},
                        "new_workers": {"type": "integer"},
                        "installs": {"type": "integer"},
                        "runs": {"type": "integer"},
                        "revenue_notes": {"type": "string"},
                        "open_issues": {"type": "array"},
                        "strategic_priorities": {"type": "array"},
                        "timeframe": {"type": "string"},
                    },
                    "required": ["installs", "runs", "open_issues", "strategic_priorities", "timeframe"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "operating_summary": {"type": "string"},
                        "key_metrics_snapshot": {"type": "object"},
                        "top_priorities": {"type": "array"},
                        "blockers": {"type": "array"},
                        "suggested_next_actions": {"type": "array"},
                    },
                },
                "prompt_template": (
                    "You are Operations Coordinator Worker. Build a concise operating briefing with clear priority order,"
                    " blocker visibility, and concrete next actions."
                ),
                "example_run_payload": {
                    "runtime_input": {
                        "new_users": 18,
                        "new_workers": 9,
                        "installs": 74,
                        "runs": 301,
                        "revenue_notes": "Paid installs up 12% week-over-week",
                        "open_issues": ["2 payment failures", "1 webhook retry backlog"],
                        "strategic_priorities": ["increase run-to-value conversion", "creator growth"],
                        "timeframe": "daily",
                    }
                },
            },
            "capabilities_json": {
                "operating_briefs": True,
                "priority_management": True,
                "blocker_triage": True,
            },
            "actions_json": ["record_optimization_signals", "monitor_outbound_events"],
            "tools_json": ["internal_note_writer", "webhook_caller"],
            "tags_json": [
                "operations",
                "daily-briefing",
                "priorities",
                "execution",
                "founder-os",
                *INTERNAL_STACK_SHARED_TAGS,
            ],
            "usage_examples_json": [
                {
                    "title": "Daily founder brief",
                    "input": {"timeframe": "daily", "installs": 42, "runs": 190},
                    "output_highlights": ["operating summary", "top priorities", "suggested next actions"],
                }
            ],
            "pricing_type": WorkerPricingType.FREE.value,
            "price_cents": 0,
            "currency": "USD",
            "is_marketplace_listed": True,
            "visibility": WorkerTemplateVisibility.MARKETPLACE.value,
            "is_featured": True,
            "featured_rank": 7,
            "icon": "clipboard-check",
            "chain_enabled": True,
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
    template.icon = seed.get("icon")
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
