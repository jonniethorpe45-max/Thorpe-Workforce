from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    FounderOSAutomation,
    FounderOSAutomationFrequency,
    FounderOSReport,
    FounderOSReportType,
    SupportRequest,
    User,
    WorkerChain,
    WorkerChainStatus,
    WorkerChainStep,
    WorkerChainTriggerType,
    WorkerInstance,
    WorkerRevenueEvent,
    WorkerRun,
    WorkerSubscription,
    WorkerTemplate,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
)
from app.schemas.api import FounderOSAutomationCreate, FounderOSAutomationUpdate, FounderOSChainRunRequest
from app.services.audit import log_audit_event
from app.services.worker_chain import ChainExecutionResult, run_worker_chain_manually
from app.services.worker_definitions import ensure_builtin_worker_templates


@dataclass(frozen=True)
class FounderChainTemplateSpec:
    key: str
    name: str
    description: str
    report_type: FounderOSReportType
    worker_template_keys: tuple[str, ...]
    suggested_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    featured_rank: int


FOUNDER_OS_CHAIN_TEMPLATES: tuple[FounderChainTemplateSpec, ...] = (
    FounderChainTemplateSpec(
        key="daily_founder_briefing",
        name="Daily Founder Briefing Chain",
        description="Summarize daily operating state, friction, and founder priorities.",
        report_type=FounderOSReportType.DAILY_BRIEFING,
        worker_template_keys=(
            "internal-user-feedback-intelligence-worker",
            "internal-marketplace-curator-worker",
            "internal-operations-coordinator-worker",
        ),
        suggested_inputs=(
            "feedback_items",
            "app_usage_notes",
            "worker_catalog",
            "install_data",
            "category_data",
            "creator_activity",
            "new_users",
            "new_workers",
            "installs",
            "runs",
            "revenue_notes",
            "open_issues",
            "strategic_priorities",
            "timeframe",
        ),
        expected_outputs=(
            "daily_summary",
            "top_metrics",
            "top_friction_points",
            "marketplace_opportunities",
            "founder_priorities",
            "blockers",
            "suggested_next_actions",
        ),
        featured_rank=1,
    ),
    FounderChainTemplateSpec(
        key="growth_campaign",
        name="Growth Campaign Chain",
        description="Turn product strategy and goals into practical campaign outputs.",
        report_type=FounderOSReportType.GROWTH_CAMPAIGN,
        worker_template_keys=(
            "internal-product-strategy-worker",
            "internal-chief-marketing-worker",
            "internal-community-manager-worker",
        ),
        suggested_inputs=(
            "product_metrics",
            "user_requests",
            "business_goals",
            "engineering_constraints",
            "planning_horizon",
            "target_audience",
            "campaign_goal",
            "platform",
            "tone",
            "key_message",
            "offer_or_cta",
            "mention_self_as_worker",
        ),
        expected_outputs=(
            "growth_strategy_summary",
            "social_posts",
            "outreach_messages",
            "campaign_plan",
            "community_replies",
            "next_steps",
        ),
        featured_rank=2,
    ),
    FounderChainTemplateSpec(
        key="creator_recruitment",
        name="Creator Recruitment Chain",
        description="Build repeatable creator acquisition outputs from marketplace signals.",
        report_type=FounderOSReportType.CREATOR_RECRUITMENT,
        worker_template_keys=(
            "internal-marketplace-curator-worker",
            "internal-creator-recruitment-worker",
            "internal-community-manager-worker",
        ),
        suggested_inputs=(
            "worker_catalog",
            "install_data",
            "category_data",
            "creator_activity",
            "target_creator_type",
            "platform",
            "recruitment_goal",
            "incentive_offer",
            "tone",
            "mention_revenue_share",
        ),
        expected_outputs=(
            "creator_opportunity_summary",
            "outreach_messages",
            "recruitment_post",
            "creator_pitch",
            "follow_up_sequence",
            "community_post_idea",
        ),
        featured_rank=4,
    ),
    FounderChainTemplateSpec(
        key="investor_update",
        name="Investor Update Chain",
        description="Convert operating context and strategy into investor-ready updates.",
        report_type=FounderOSReportType.INVESTOR_UPDATE,
        worker_template_keys=(
            "internal-operations-coordinator-worker",
            "internal-product-strategy-worker",
            "internal-investor-update-worker",
        ),
        suggested_inputs=(
            "reporting_period",
            "key_metrics",
            "wins",
            "challenges",
            "asks",
            "next_milestones",
            "product_metrics",
            "user_requests",
            "business_goals",
            "engineering_constraints",
            "planning_horizon",
        ),
        expected_outputs=(
            "executive_summary",
            "metric_highlights",
            "narrative_update",
            "risks_and_challenges",
            "asks_section",
            "next_milestones_section",
        ),
        featured_rank=3,
    ),
    FounderChainTemplateSpec(
        key="weekly_content_engine",
        name="Weekly Content Engine Chain",
        description="Generate founder-led weekly content strategy and campaign assets.",
        report_type=FounderOSReportType.WEEKLY_CONTENT_ENGINE,
        worker_template_keys=(
            "internal-product-strategy-worker",
            "internal-content-marketing-worker",
            "internal-chief-marketing-worker",
        ),
        suggested_inputs=(
            "product_metrics",
            "user_requests",
            "business_goals",
            "audience",
            "content_goal",
            "content_format",
            "core_topic",
            "tone",
            "product_context",
            "platform",
            "campaign_goal",
            "key_message",
        ),
        expected_outputs=(
            "content_strategy_summary",
            "title_options",
            "outlines",
            "draft_content",
            "social_promotions",
            "cta_block",
            "repurposing_ideas",
        ),
        featured_rank=5,
    ),
)


FOUNDER_CHAIN_TEMPLATE_BY_KEY = {item.key: item for item in FOUNDER_OS_CHAIN_TEMPLATES}
FOUNDER_CHAIN_KEYS = tuple(FOUNDER_CHAIN_TEMPLATE_BY_KEY.keys())


def _ensure_founder_user(user: User) -> None:
    if user.role not in {"owner", "admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Founder OS access requires owner/admin role")


def _build_chain_trigger_config(spec: FounderChainTemplateSpec) -> dict[str, Any]:
    return {
        "founder_os": True,
        "founder_os_template_key": spec.key,
        "founder_os_report_type": spec.report_type.value,
        "founder_os_featured_rank": spec.featured_rank,
        "founder_os_suggested_inputs": list(spec.suggested_inputs),
        "founder_os_expected_outputs": list(spec.expected_outputs),
        "founder_os_worker_template_keys": list(spec.worker_template_keys),
    }


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_internal_templates(db: Session) -> dict[str, WorkerTemplate]:
    keys = sorted({key for spec in FOUNDER_OS_CHAIN_TEMPLATES for key in spec.worker_template_keys})
    templates = db.query(WorkerTemplate).filter(WorkerTemplate.template_key.in_(tuple(keys))).all()
    template_map = {item.template_key: item for item in templates}
    missing = [key for key in keys if key not in template_map]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Founder OS worker templates are missing: {', '.join(missing)}",
        )
    for key in keys:
        template = template_map[key]
        if not template.is_active or template.status != WorkerTemplateStatus.ACTIVE.value:
            raise HTTPException(
                status_code=500,
                detail=f"Founder OS worker template is not active: {template.display_name or template.name}",
            )
    return template_map


def _normalize_trigger_config(chain: WorkerChain) -> dict[str, Any]:
    existing = chain.trigger_config_json if isinstance(chain.trigger_config_json, dict) else {}
    return dict(existing)


def ensure_founder_os_chains(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> list[WorkerChain]:
    ensure_builtin_worker_templates(db)
    template_map = _resolve_internal_templates(db)
    chains = db.query(WorkerChain).filter(WorkerChain.workspace_id == workspace_id).all()
    existing_by_key: dict[str, WorkerChain] = {}
    for chain in chains:
        config = chain.trigger_config_json if isinstance(chain.trigger_config_json, dict) else {}
        key = str(config.get("founder_os_template_key", "")).strip()
        if key:
            existing_by_key[key] = chain

    ensured: list[WorkerChain] = []
    mutated = False
    for spec in FOUNDER_OS_CHAIN_TEMPLATES:
        chain = existing_by_key.get(spec.key)
        if not chain:
            chain = WorkerChain(
                workspace_id=workspace_id,
                name=spec.name,
                description=spec.description,
                status=WorkerChainStatus.ACTIVE.value,
                trigger_type=WorkerChainTriggerType.MANUAL.value,
                trigger_config_json=_build_chain_trigger_config(spec),
            )
            db.add(chain)
            db.flush()
            mutated = True
        else:
            chain.name = spec.name
            chain.description = spec.description
            chain.status = chain.status or WorkerChainStatus.ACTIVE.value
            chain.trigger_type = chain.trigger_type or WorkerChainTriggerType.MANUAL.value
            chain.trigger_config_json = _merge_dict(_normalize_trigger_config(chain), _build_chain_trigger_config(spec))
            db.flush()

        existing_steps = (
            db.query(WorkerChainStep)
            .filter(WorkerChainStep.chain_id == chain.id)
            .order_by(WorkerChainStep.step_order.asc())
            .all()
        )
        expected_template_ids = [template_map[key].id for key in spec.worker_template_keys]
        should_replace_steps = len(existing_steps) != len(expected_template_ids)
        if not should_replace_steps:
            for idx, step in enumerate(existing_steps):
                if step.worker_template_id != expected_template_ids[idx]:
                    should_replace_steps = True
                    break

        if should_replace_steps:
            db.query(WorkerChainStep).filter(WorkerChainStep.chain_id == chain.id).delete(synchronize_session=False)
            for idx, template_key in enumerate(spec.worker_template_keys, start=1):
                template = template_map[template_key]
                db.add(
                    WorkerChainStep(
                        chain_id=chain.id,
                        step_order=idx,
                        worker_template_id=template.id,
                        step_name=f"{idx}. {template.display_name or template.name}",
                        input_mapping_json={},
                        condition_json=None,
                    )
                )
            db.flush()
            mutated = True
        ensured.append(chain)

    if mutated:
        log_audit_event(
            db,
            workspace_id=workspace_id,
            actor_type="user" if actor_user_id else "system",
            actor_id=str(actor_user_id or "system_seed"),
            event_name="founder_os_chains_ensured",
            payload={"count": len(ensured)},
        )
    return ensured


def _serialize_chain_worker_refs(db: Session, chain_id: uuid.UUID) -> list[dict[str, Any]]:
    steps = (
        db.query(WorkerChainStep)
        .filter(WorkerChainStep.chain_id == chain_id, WorkerChainStep.worker_template_id.is_not(None))
        .order_by(WorkerChainStep.step_order.asc())
        .all()
    )
    template_ids = [item.worker_template_id for item in steps if item.worker_template_id]
    if not template_ids:
        return []
    templates = db.query(WorkerTemplate).filter(WorkerTemplate.id.in_(tuple(template_ids))).all()
    template_map = {item.id: item for item in templates}
    refs: list[dict[str, Any]] = []
    for step in steps:
        if not step.worker_template_id:
            continue
        template = template_map.get(step.worker_template_id)
        if not template:
            continue
        refs.append(
            {
                "worker_template_id": template.id,
                "template_key": template.template_key,
                "slug": template.slug,
                "name": template.display_name or template.name,
                "category": template.category,
            }
        )
    return refs


def _latest_report_map(db: Session, workspace_id: uuid.UUID, chain_ids: list[uuid.UUID]) -> dict[uuid.UUID, FounderOSReport]:
    if not chain_ids:
        return {}
    reports = (
        db.query(FounderOSReport)
        .filter(FounderOSReport.workspace_id == workspace_id, FounderOSReport.chain_id.in_(tuple(chain_ids)))
        .order_by(FounderOSReport.created_at.desc())
        .all()
    )
    latest: dict[uuid.UUID, FounderOSReport] = {}
    for item in reports:
        if item.chain_id and item.chain_id not in latest:
            latest[item.chain_id] = item
    return latest


def _chain_last_run_at(db: Session, chain_id: uuid.UUID) -> datetime | None:
    return (
        db.query(func.max(WorkerRun.started_at))
        .filter(WorkerRun.trigger_source.like(f"chain:{chain_id}:run:%"))
        .scalar()
    )


def list_founder_os_chains(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> list[dict[str, Any]]:
    chains = ensure_founder_os_chains(db, workspace_id=workspace_id, actor_user_id=actor_user_id)
    chain_ids = [item.id for item in chains]
    report_map = _latest_report_map(db, workspace_id, chain_ids)
    items: list[dict[str, Any]] = []
    for chain in sorted(
        chains,
        key=lambda item: int(
            ((item.trigger_config_json or {}).get("founder_os_featured_rank", 9999))
            if isinstance(item.trigger_config_json, dict)
            else 9999
        ),
    ):
        config = chain.trigger_config_json if isinstance(chain.trigger_config_json, dict) else {}
        template_key = str(config.get("founder_os_template_key", "")).strip()
        if template_key not in FOUNDER_CHAIN_TEMPLATE_BY_KEY:
            continue
        spec = FOUNDER_CHAIN_TEMPLATE_BY_KEY[template_key]
        latest_report = report_map.get(chain.id)
        items.append(
            {
                "id": chain.id,
                "template_key": spec.key,
                "name": chain.name,
                "description": chain.description or spec.description,
                "report_type": spec.report_type.value,
                "featured_rank": spec.featured_rank,
                "workers": _serialize_chain_worker_refs(db, chain.id),
                "expected_outputs": list(spec.expected_outputs),
                "suggested_inputs": list(spec.suggested_inputs),
                "last_run_at": _chain_last_run_at(db, chain.id),
                "last_report_id": latest_report.id if latest_report else None,
                "last_report_created_at": latest_report.created_at if latest_report else None,
            }
        )
    return items


def get_founder_os_chain(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    chain_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> dict[str, Any]:
    chains = list_founder_os_chains(db, workspace_id=workspace_id, actor_user_id=actor_user_id)
    for item in chains:
        if item["id"] == chain_id:
            return item
    raise HTTPException(status_code=404, detail="Founder OS chain not found")


def _build_prefill_context(db: Session, *, workspace_id: uuid.UUID) -> dict[str, Any]:
    now = datetime.now(UTC)
    last_7_days = now - timedelta(days=7)
    start_month = datetime(now.year, now.month, 1, tzinfo=UTC)

    new_users_7d = (
        db.query(func.count(User.id))
        .filter(User.workspace_id == workspace_id, User.created_at >= last_7_days)
        .scalar()
        or 0
    )
    worker_instances = (
        db.query(func.count(WorkerInstance.id)).filter(WorkerInstance.workspace_id == workspace_id).scalar() or 0
    )
    runs_7d = (
        db.query(func.count(WorkerRun.id))
        .filter(WorkerRun.workspace_id == workspace_id, WorkerRun.created_at >= last_7_days)
        .scalar()
        or 0
    )
    installs_7d = (
        db.query(func.count(WorkerSubscription.id))
        .filter(WorkerSubscription.workspace_id == workspace_id, WorkerSubscription.created_at >= last_7_days)
        .scalar()
        or 0
    )
    revenue_month = (
        db.query(func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0))
        .filter(WorkerRevenueEvent.workspace_id == workspace_id, WorkerRevenueEvent.created_at >= start_month)
        .scalar()
        or 0
    )
    open_issue_rows = (
        db.query(SupportRequest.subject)
        .filter(
            SupportRequest.workspace_id == workspace_id,
            SupportRequest.status.in_(("open", "in_progress")),
        )
        .order_by(SupportRequest.created_at.desc())
        .limit(8)
        .all()
    )
    open_issues = [str(row[0]) for row in open_issue_rows if row and row[0]]

    category_rows = (
        db.query(WorkerTemplate.category, func.count(WorkerTemplate.id), func.coalesce(func.sum(WorkerTemplate.install_count), 0))
        .filter(
            WorkerTemplate.is_marketplace_listed.is_(True),
            WorkerTemplate.status == WorkerTemplateStatus.ACTIVE.value,
            WorkerTemplate.visibility == WorkerTemplateVisibility.MARKETPLACE.value,
        )
        .group_by(WorkerTemplate.category)
        .order_by(func.coalesce(func.sum(WorkerTemplate.install_count), 0).desc())
        .limit(10)
        .all()
    )
    category_data = [
        {"category": str(row[0]), "template_count": int(row[1] or 0), "install_count": int(row[2] or 0)}
        for row in category_rows
    ]

    creator_rows = (
        db.query(
            WorkerTemplate.creator_user_id,
            func.count(WorkerTemplate.id),
            func.coalesce(func.sum(WorkerTemplate.install_count), 0),
        )
        .filter(
            WorkerTemplate.is_marketplace_listed.is_(True),
            WorkerTemplate.creator_user_id.is_not(None),
        )
        .group_by(WorkerTemplate.creator_user_id)
        .order_by(func.coalesce(func.sum(WorkerTemplate.install_count), 0).desc())
        .limit(10)
        .all()
    )
    creator_activity = [
        {
            "creator_user_id": str(row[0]),
            "published_workers": int(row[1] or 0),
            "installs": int(row[2] or 0),
        }
        for row in creator_rows
        if row and row[0]
    ]

    worker_catalog_rows = (
        db.query(
            WorkerTemplate.id,
            WorkerTemplate.template_key,
            WorkerTemplate.slug,
            WorkerTemplate.display_name,
            WorkerTemplate.category,
            WorkerTemplate.install_count,
            WorkerTemplate.rating_avg,
        )
        .filter(
            WorkerTemplate.is_marketplace_listed.is_(True),
            WorkerTemplate.status == WorkerTemplateStatus.ACTIVE.value,
        )
        .order_by(WorkerTemplate.install_count.desc(), WorkerTemplate.rating_avg.desc())
        .limit(20)
        .all()
    )
    worker_catalog = [
        {
            "id": str(row[0]),
            "template_key": str(row[1]),
            "slug": str(row[2]) if row[2] else None,
            "name": str(row[3]),
            "category": str(row[4]),
            "install_count": int(row[5] or 0),
            "rating_avg": float(row[6] or 0.0),
        }
        for row in worker_catalog_rows
    ]

    install_rows = (
        db.query(
            WorkerTemplate.template_key,
            WorkerTemplate.display_name,
            func.count(WorkerSubscription.id),
        )
        .join(WorkerTemplate, WorkerTemplate.id == WorkerSubscription.worker_template_id)
        .filter(WorkerSubscription.workspace_id == workspace_id)
        .group_by(WorkerTemplate.template_key, WorkerTemplate.display_name)
        .order_by(func.count(WorkerSubscription.id).desc())
        .limit(10)
        .all()
    )
    install_data = [
        {"template_key": str(row[0]), "name": str(row[1]), "installs": int(row[2] or 0)}
        for row in install_rows
    ]

    product_metrics = {
        "new_users_last_7_days": int(new_users_7d),
        "installed_workers_count": int(worker_instances),
        "runs_last_7_days": int(runs_7d),
        "installs_last_7_days": int(installs_7d),
        "estimated_revenue_month_cents": int(revenue_month),
    }

    return {
        "reporting_period": now.strftime("%B %Y"),
        "timeframe": "daily",
        "new_users": int(new_users_7d),
        "new_workers": int(worker_instances),
        "installs": int(installs_7d),
        "runs": int(runs_7d),
        "revenue_notes": f"Estimated gross revenue this month: ${(int(revenue_month) / 100):.2f}",
        "open_issues": open_issues,
        "feedback_items": [],
        "app_usage_notes": [],
        "strategic_priorities": [],
        "wins": [],
        "challenges": [],
        "asks": [],
        "next_milestones": [],
        "worker_catalog": worker_catalog,
        "install_data": install_data,
        "category_data": category_data,
        "creator_activity": creator_activity,
        "product_metrics": product_metrics,
        "key_metrics": product_metrics,
        "user_requests": [],
        "business_goals": [],
        "engineering_constraints": [],
        "planning_horizon": "30d",
    }


def _serialize_step_execution_for_report(result: ChainExecutionResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for step in result.executed_steps:
        rows.append(
            {
                "step_order": step.step_order,
                "status": step.status,
                "run_id": str(step.run_id) if step.run_id else None,
                "worker_instance_id": str(step.worker_instance_id) if step.worker_instance_id else None,
                "worker_template_id": str(step.worker_template_id) if step.worker_template_id else None,
                "summary": step.summary,
                "error": step.error,
                "next_step_order": step.next_step_order,
                "skipped_reason": step.skipped_reason,
            }
        )
    return rows


def _resolve_report_summary(result: ChainExecutionResult) -> str:
    final_output = result.final_output if isinstance(result.final_output, dict) else {}
    if final_output:
        summary = str(final_output.get("summary", "")).strip()
        if summary:
            return summary
    for step in reversed(result.executed_steps):
        if step.summary:
            return step.summary
    return "Founder OS chain execution completed."


def run_founder_os_chain(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    chain_id: uuid.UUID,
    payload: FounderOSChainRunRequest,
) -> tuple[ChainExecutionResult, FounderOSReport]:
    chain = db.get(WorkerChain, chain_id)
    if not chain or chain.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Founder OS chain not found")
    config = chain.trigger_config_json if isinstance(chain.trigger_config_json, dict) else {}
    template_key = str(config.get("founder_os_template_key", "")).strip()
    if template_key not in FOUNDER_CHAIN_TEMPLATE_BY_KEY:
        raise HTTPException(status_code=400, detail="Chain is not managed by Founder OS")
    try:
        report_type = FounderOSReportType(
            str(config.get("founder_os_report_type", FounderOSReportType.DAILY_BRIEFING.value))
        )
    except ValueError:
        report_type = FounderOSReportType.DAILY_BRIEFING

    runtime_input = payload.runtime_input if isinstance(payload.runtime_input, dict) else {}
    if payload.use_prefill_context:
        runtime_input = _merge_dict(_build_prefill_context(db, workspace_id=workspace_id), runtime_input)

    result = run_worker_chain_manually(
        db,
        chain=chain,
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        runtime_input=runtime_input,
        max_steps=payload.max_steps,
    )

    report_title = payload.report_title or f"{chain.name} — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
    source_run_ids = [str(item.run_id) for item in result.executed_steps if item.run_id]
    report = FounderOSReport(
        workspace_id=workspace_id,
        chain_id=chain.id,
        report_type=report_type.value,
        title=report_title,
        summary=_resolve_report_summary(result),
        output_json={
            "final_output": result.final_output,
            "executed_steps": _serialize_step_execution_for_report(result),
            "runtime_input": runtime_input,
        },
        chain_run_id=result.chain_run_id,
        source_run_ids_json=source_run_ids,
        created_by_user_id=actor_user_id,
    )
    db.add(report)
    db.flush()

    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=str(actor_user_id),
        event_name="founder_os_chain_run_completed",
        payload={
            "chain_id": str(chain.id),
            "chain_template_key": template_key,
            "chain_run_id": result.chain_run_id,
            "report_id": str(report.id),
            "status": result.status,
        },
    )
    return result, report


def list_founder_os_reports(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    report_type: FounderOSReportType | None = None,
    chain_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[FounderOSReport], int]:
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    query = db.query(FounderOSReport).filter(FounderOSReport.workspace_id == workspace_id)
    if report_type is not None:
        query = query.filter(FounderOSReport.report_type == report_type.value)
    if chain_id is not None:
        query = query.filter(FounderOSReport.chain_id == chain_id)
    if start_date is not None:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        query = query.filter(FounderOSReport.created_at >= start_dt)
    if end_date is not None:
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=UTC)
        query = query.filter(FounderOSReport.created_at <= end_dt)
    total = query.count()
    items = query.order_by(FounderOSReport.created_at.desc()).offset(max(offset, 0)).limit(max(limit, 1)).all()
    return items, total


def get_founder_os_report(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    report_id: uuid.UUID,
) -> FounderOSReport:
    report = db.get(FounderOSReport, report_id)
    if not report or report.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Founder OS report not found")
    return report


def _next_run_for_frequency(frequency: FounderOSAutomationFrequency, *, anchor: datetime | None = None) -> datetime:
    now = anchor or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    if frequency == FounderOSAutomationFrequency.DAILY:
        return now + timedelta(days=1)
    if frequency == FounderOSAutomationFrequency.WEEKLY:
        return now + timedelta(days=7)
    return now + timedelta(days=30)


def list_founder_os_automations(db: Session, *, workspace_id: uuid.UUID) -> list[FounderOSAutomation]:
    return (
        db.query(FounderOSAutomation)
        .filter(FounderOSAutomation.workspace_id == workspace_id)
        .order_by(FounderOSAutomation.created_at.desc())
        .all()
    )


def create_founder_os_automation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    payload: FounderOSAutomationCreate,
) -> FounderOSAutomation:
    chain = db.get(WorkerChain, payload.chain_id)
    if not chain or chain.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Founder OS chain not found")
    config = chain.trigger_config_json if isinstance(chain.trigger_config_json, dict) else {}
    if str(config.get("founder_os_template_key", "")).strip() not in FOUNDER_CHAIN_KEYS:
        raise HTTPException(status_code=400, detail="Automations support Founder OS chains only")

    automation = FounderOSAutomation(
        workspace_id=workspace_id,
        chain_id=chain.id,
        frequency=payload.frequency.value,
        is_enabled=payload.is_enabled,
        next_run_at=payload.next_run_at or _next_run_for_frequency(payload.frequency),
        runtime_input_json=payload.runtime_input_json,
        created_by_user_id=actor_user_id,
    )
    db.add(automation)
    db.flush()
    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=str(actor_user_id),
        event_name="founder_os_automation_created",
        payload={"automation_id": str(automation.id), "chain_id": str(chain.id), "frequency": automation.frequency},
    )
    return automation


def update_founder_os_automation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    automation_id: uuid.UUID,
    payload: FounderOSAutomationUpdate,
) -> FounderOSAutomation:
    automation = db.get(FounderOSAutomation, automation_id)
    if not automation or automation.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Founder OS automation not found")

    updates = payload.model_dump(exclude_unset=True)
    if "frequency" in updates and payload.frequency is not None:
        automation.frequency = payload.frequency.value
        if automation.is_enabled and payload.next_run_at is None:
            automation.next_run_at = _next_run_for_frequency(payload.frequency)
    if "is_enabled" in updates and payload.is_enabled is not None:
        automation.is_enabled = bool(payload.is_enabled)
        if automation.is_enabled and automation.next_run_at is None:
            frequency = FounderOSAutomationFrequency(automation.frequency)
            automation.next_run_at = _next_run_for_frequency(frequency)
    if "next_run_at" in updates:
        automation.next_run_at = payload.next_run_at
    if "runtime_input_json" in updates:
        automation.runtime_input_json = payload.runtime_input_json

    db.flush()
    log_audit_event(
        db,
        workspace_id=workspace_id,
        actor_type="user",
        actor_id=str(actor_user_id),
        event_name="founder_os_automation_updated",
        payload={"automation_id": str(automation.id)},
    )
    return automation


def _automation_to_dict(db: Session, automation: FounderOSAutomation) -> dict[str, Any]:
    chain = db.get(WorkerChain, automation.chain_id)
    chain_name = chain.name if chain else "Unknown Chain"
    return {
        "id": automation.id,
        "workspace_id": automation.workspace_id,
        "chain_id": automation.chain_id,
        "chain_name": chain_name,
        "frequency": automation.frequency,
        "is_enabled": automation.is_enabled,
        "next_run_at": automation.next_run_at,
        "last_run_at": automation.last_run_at,
        "runtime_input_json": automation.runtime_input_json or {},
        "created_by_user_id": automation.created_by_user_id,
        "created_at": automation.created_at,
        "updated_at": automation.updated_at,
    }


def founder_os_overview(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> dict[str, Any]:
    chains = list_founder_os_chains(db, workspace_id=workspace_id, actor_user_id=actor_user_id)
    latest_reports: list[FounderOSReport] = (
        db.query(FounderOSReport)
        .filter(FounderOSReport.workspace_id == workspace_id)
        .order_by(FounderOSReport.created_at.desc())
        .limit(40)
        .all()
    )
    latest_by_type: dict[str, FounderOSReport] = {}
    for report in latest_reports:
        if report.report_type not in latest_by_type:
            latest_by_type[report.report_type] = report
    latest_reports_payload: list[FounderOSReport] = []
    for report_type in FounderOSReportType:
        report = latest_by_type.get(report_type.value)
        if report:
            latest_reports_payload.append(report)

    snapshot = _build_prefill_context(db, workspace_id=workspace_id).get("product_metrics", {})
    recommended_actions: list[str] = []
    if int(snapshot.get("runs_last_7_days", 0)) < 10:
        recommended_actions.append("Run Daily Founder Briefing to capture blockers and next actions.")
    if int(snapshot.get("installs_last_7_days", 0)) < 3:
        recommended_actions.append("Run Creator Recruitment Chain to expand marketplace supply.")
    if int(snapshot.get("estimated_revenue_month_cents", 0)) <= 0:
        recommended_actions.append("Run Growth Campaign Chain and focus on top conversion opportunities.")
    if not recommended_actions:
        recommended_actions.append("Review latest Founder OS reports and schedule your next automation cycle.")

    active_automations = [
        _automation_to_dict(db, item)
        for item in list_founder_os_automations(db, workspace_id=workspace_id)
        if item.is_enabled
    ]
    return {
        "available_chains": chains,
        "latest_reports": latest_reports_payload,
        "metrics_snapshot": snapshot,
        "recommended_next_actions": recommended_actions,
        "active_automations": active_automations,
    }


def founder_os_seed_integrity_summary() -> dict[str, Any]:
    return {
        "chain_template_count": len(FOUNDER_OS_CHAIN_TEMPLATES),
        "template_keys": [item.key for item in FOUNDER_OS_CHAIN_TEMPLATES],
        "report_types": [item.report_type.value for item in FOUNDER_OS_CHAIN_TEMPLATES],
    }
