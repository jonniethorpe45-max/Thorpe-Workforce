import uuid
from typing import Any, Callable

from sqlalchemy import func

from app.models import Lead, Reply, SentEmail
from app.services.analytics_recorder import record_worker_signal
from app.services.lead_researcher import research_lead
from app.services.message_generator import generate_initial_sequence, send_approved_messages
from app.workers.plan import WorkerRunContext, WorkerStep
from app.workers.planner import WorkerPlanner

ActionHandler = Callable[[WorkerRunContext, WorkerStep], dict[str, Any]]


class WorkerActionRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, action_key: str, handler: ActionHandler) -> None:
        self._handlers[action_key] = handler

    def execute(self, action_key: str, context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
        handler = self._handlers.get(action_key)
        if not handler:
            raise ValueError(f"No action handler registered for: {action_key}")
        return handler(context, step)


def _select_eligible_leads(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    plan_data = WorkerPlanner().build_execution_plan(context.db, context.worker, context.campaign)
    context.selected_lead_ids = list(plan_data.get("lead_ids", []))
    context.skipped_leads = list(plan_data.get("skipped_leads", []))
    return {
        "selected_leads": len(context.selected_lead_ids),
        "skipped_leads": context.skipped_leads,
        "suppressed_candidates": len(context.skipped_leads),
    }


def _research_selected_leads(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    researched = 0
    for lead_id in context.selected_lead_ids:
        parsed_lead_id = uuid.UUID(lead_id) if isinstance(lead_id, str) else lead_id
        lead = context.db.get(Lead, parsed_lead_id)
        if not lead:
            continue
        research_lead(
            context.db,
            lead,
            industry_hint=context.campaign.target_industry,
            worker_type=context.worker.worker_type,
        )
        researched += 1
    return {"researched": researched}


def _generate_messages_for_selected_leads(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    generated_count = 0
    for lead_id in context.selected_lead_ids:
        parsed_lead_id = uuid.UUID(lead_id) if isinstance(lead_id, str) else lead_id
        lead = context.db.get(Lead, parsed_lead_id)
        if not lead:
            continue
        generated = generate_initial_sequence(
            context.db,
            campaign=context.campaign,
            lead=lead,
            require_approval=context.require_manual_approval,
            worker_type=context.worker.worker_type,
        )
        generated_count += len(generated)
    return {"drafts_generated": generated_count}


def _dispatch_messages(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    if context.require_manual_approval:
        return {"emails_sent": 0, "approval_mode": "manual"}
    sent = send_approved_messages(
        context.db,
        workspace_id=context.worker.workspace_id,
        campaign_id=context.campaign.id,
    )
    return {"emails_sent": sent, "approval_mode": "auto"}


def _monitor_outbound_events(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    delivered = (
        context.db.query(func.count(SentEmail.id))
        .filter(
            SentEmail.workspace_id == context.worker.workspace_id,
            SentEmail.campaign_id == context.campaign.id,
            SentEmail.delivery_status.in_(["sent", "delivered", "replied"]),
        )
        .scalar()
        or 0
    )
    replies = (
        context.db.query(func.count(Reply.id))
        .join(SentEmail, Reply.sent_email_id == SentEmail.id)
        .filter(SentEmail.workspace_id == context.worker.workspace_id, SentEmail.campaign_id == context.campaign.id)
        .scalar()
        or 0
    )
    return {"delivered_or_sent": delivered, "reply_events": replies}


def _record_optimization_signals(context: WorkerRunContext, step: WorkerStep) -> dict[str, Any]:
    if not context.selected_lead_ids:
        record_worker_signal(
            context.db,
            workspace_id=context.worker.workspace_id,
            actor_id=str(context.worker.id),
            signal_name="no_eligible_leads",
            payload={"campaign_id": str(context.campaign.id)},
        )
        return {"optimization_signal": "no_eligible_leads"}
    if int(context.metrics.get("emails_sent", 0)) == 0 and bool(context.require_manual_approval):
        record_worker_signal(
            context.db,
            workspace_id=context.worker.workspace_id,
            actor_id=str(context.worker.id),
            signal_name="approval_queue_waiting",
            payload={"campaign_id": str(context.campaign.id), "selected_leads": len(context.selected_lead_ids)},
        )
        return {"optimization_signal": "approval_queue_waiting"}
    record_worker_signal(
        context.db,
        workspace_id=context.worker.workspace_id,
        actor_id=str(context.worker.id),
        signal_name="run_healthy",
        payload={"campaign_id": str(context.campaign.id)},
    )
    return {"optimization_signal": "run_healthy"}


def get_default_worker_action_registry() -> WorkerActionRegistry:
    registry = WorkerActionRegistry()
    registry.register("select_eligible_leads", _select_eligible_leads)
    registry.register("research_selected_leads", _research_selected_leads)
    registry.register("generate_messages_for_selected_leads", _generate_messages_for_selected_leads)
    registry.register("dispatch_messages", _dispatch_messages)
    registry.register("monitor_outbound_events", _monitor_outbound_events)
    registry.register("record_optimization_signals", _record_optimization_signals)
    return registry
