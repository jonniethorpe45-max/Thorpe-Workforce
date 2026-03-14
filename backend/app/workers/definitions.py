from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkerStepDefinition:
    key: str
    action_key: str
    status: str | None = None
    name: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkerDefinition:
    worker_type: str
    display_name: str
    worker_category: str
    description: str
    plan_version: str
    origin_type: str = "built_in"
    public_available: bool = False
    default_name: str = "AI Worker"
    default_config: dict[str, Any] = field(default_factory=dict)
    allowed_actions: list[str] = field(default_factory=list)
    prompt_profile: str = "sales"
    steps: list[WorkerStepDefinition] = field(default_factory=list)


SALES_WORKER_DEFINITION = WorkerDefinition(
    worker_type="ai_sales_worker",
    display_name="AI Sales Worker",
    worker_category="go_to_market",
    description="Research leads, draft outreach, and drive meetings from outbound missions.",
    plan_version="sales_v1",
    public_available=True,
    default_name="AI Sales Worker",
    default_config={
        "target_industry": None,
        "target_roles": [],
        "target_locations": [],
        "company_size_range": None,
    },
    allowed_actions=[
        "select_eligible_leads",
        "research_selected_leads",
        "generate_messages_for_selected_leads",
        "dispatch_messages",
        "monitor_outbound_events",
        "record_optimization_signals",
    ],
    prompt_profile="sales",
    steps=[
        WorkerStepDefinition(
            key="select_eligible_leads",
            name="Select eligible leads",
            action_key="select_eligible_leads",
            status="prospecting",
        ),
        WorkerStepDefinition(
            key="research_selected_leads",
            name="Research selected leads",
            action_key="research_selected_leads",
            status="researching",
        ),
        WorkerStepDefinition(
            key="generate_messages_for_selected_leads",
            name="Generate outreach messages",
            action_key="generate_messages_for_selected_leads",
            status="drafting",
        ),
        WorkerStepDefinition(
            key="dispatch_messages",
            name="Dispatch approved messages",
            action_key="dispatch_messages",
            status="sending",
        ),
        WorkerStepDefinition(
            key="monitor_outbound_events",
            name="Monitor outbound activity",
            action_key="monitor_outbound_events",
            status="monitoring",
        ),
        WorkerStepDefinition(
            key="record_optimization_signals",
            name="Record optimization signals",
            action_key="record_optimization_signals",
            status="optimizing",
        ),
    ],
)


CUSTOM_WORKER_DEFINITION = WorkerDefinition(
    worker_type="custom_worker",
    display_name="Custom Worker",
    worker_category="custom",
    description="Workspace-defined AI worker assembled from configurable plan steps.",
    plan_version="custom_v1",
    origin_type="custom",
    public_available=False,
    default_name="Custom AI Worker",
    default_config={"execution_steps": []},
    allowed_actions=[
        "select_eligible_leads",
        "research_selected_leads",
        "generate_messages_for_selected_leads",
        "dispatch_messages",
        "monitor_outbound_events",
        "record_optimization_signals",
    ],
    prompt_profile="sales",
    steps=[],
)

RECRUITING_WORKER_DEFINITION = WorkerDefinition(
    worker_type="ai_recruiting_worker",
    display_name="AI Recruiting Worker",
    worker_category="talent",
    description="Future built-in worker for sourcing and outreach to candidates.",
    plan_version="recruiting_v1",
    public_available=False,
    default_name="AI Recruiting Worker",
    default_config={},
    allowed_actions=[],
    prompt_profile="sales",
    steps=[],
)

SUPPORT_WORKER_DEFINITION = WorkerDefinition(
    worker_type="ai_support_worker",
    display_name="AI Support Worker",
    worker_category="support",
    description="Future built-in worker for triage and support response optimization.",
    plan_version="support_v1",
    public_available=False,
    default_name="AI Support Worker",
    default_config={},
    allowed_actions=[],
    prompt_profile="sales",
    steps=[],
)

RESEARCH_WORKER_DEFINITION = WorkerDefinition(
    worker_type="ai_research_worker",
    display_name="AI Research Worker",
    worker_category="research",
    description="Future built-in worker for domain and account research automation.",
    plan_version="research_v1",
    public_available=False,
    default_name="AI Research Worker",
    default_config={},
    allowed_actions=[],
    prompt_profile="sales",
    steps=[],
)


_BUILT_IN_DEFINITIONS: dict[str, WorkerDefinition] = {
    SALES_WORKER_DEFINITION.worker_type: SALES_WORKER_DEFINITION,
    CUSTOM_WORKER_DEFINITION.worker_type: CUSTOM_WORKER_DEFINITION,
    RECRUITING_WORKER_DEFINITION.worker_type: RECRUITING_WORKER_DEFINITION,
    SUPPORT_WORKER_DEFINITION.worker_type: SUPPORT_WORKER_DEFINITION,
    RESEARCH_WORKER_DEFINITION.worker_type: RESEARCH_WORKER_DEFINITION,
}


def get_worker_definition(worker_type: str) -> WorkerDefinition:
    definition = _BUILT_IN_DEFINITIONS.get(worker_type)
    if not definition:
        raise ValueError(f"Unsupported worker_type: {worker_type}")
    return definition


def list_worker_definitions(include_internal: bool = False) -> list[WorkerDefinition]:
    if include_internal:
        return list(_BUILT_IN_DEFINITIONS.values())
    return [definition for definition in _BUILT_IN_DEFINITIONS.values() if definition.public_available]
