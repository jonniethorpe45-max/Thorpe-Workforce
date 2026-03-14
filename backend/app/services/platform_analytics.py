import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    CreatorMonetizationProfile,
    SubscriptionPlan,
    User,
    WorkerEntitlementStatus,
    WorkerInstance,
    WorkerModerationStatus,
    WorkerReport,
    WorkerReportStatus,
    WorkerRevenueEvent,
    WorkerRun,
    WorkerSubscription,
    WorkerTemplate,
    WorkerTemplateVisibility,
    Workspace,
    WorkspaceSubscription,
)
from app.services.billing import get_workspace_entitlements


def _parse_range_days(range_value: str | None) -> int:
    candidate = (range_value or "30d").strip().lower()
    mapping = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}
    return mapping.get(candidate, 30)


def resolve_date_window(
    *,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> tuple[datetime, datetime]:
    if start_date and end_date:
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=UTC)
        return start_dt, end_dt
    days = _parse_range_days(range_value)
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=days - 1)
    return start_dt, end_dt


def _series_from_rows(
    rows: list[tuple[Any, int | float]],
    *,
    start: datetime,
    end: datetime,
    default_value: int | float = 0,
) -> list[dict[str, Any]]:
    values: dict[str, int | float] = {}
    for raw_day, raw_value in rows:
        day_str = str(raw_day)
        values[day_str] = float(raw_value) if isinstance(raw_value, float) else int(raw_value or 0)
    points: list[dict[str, Any]] = []
    cursor = start.date()
    end_day = end.date()
    while cursor <= end_day:
        key = cursor.isoformat()
        points.append({"date": key, "value": values.get(key, default_value)})
        cursor += timedelta(days=1)
    return points


def creator_dashboard_summary(
    db: Session,
    *,
    creator_user_id: uuid.UUID,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> dict[str, Any]:
    start_dt, end_dt = resolve_date_window(range_value=range_value, start_date=start_date, end_date=end_date)
    published_workers_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            WorkerTemplate.visibility.in_(
                (
                    WorkerTemplateVisibility.PUBLIC.value,
                    WorkerTemplateVisibility.MARKETPLACE.value,
                )
            ),
        )
        .scalar()
        or 0
    )
    paid_workers_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            WorkerTemplate.pricing_type.in_(("one_time", "subscription")),
            WorkerTemplate.price_cents > 0,
        )
        .scalar()
        or 0
    )
    free_workers_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            or_(WorkerTemplate.pricing_type.in_(("free", "internal")), WorkerTemplate.price_cents <= 0),
        )
        .scalar()
        or 0
    )
    total_installs = (
        db.query(func.coalesce(func.sum(WorkerTemplate.install_count), 0))
        .filter(WorkerTemplate.creator_user_id == creator_user_id)
        .scalar()
        or 0
    )
    total_runs = (
        db.query(func.count(WorkerRun.id))
        .join(WorkerTemplate, WorkerRun.template_id == WorkerTemplate.id)
        .filter(WorkerTemplate.creator_user_id == creator_user_id)
        .scalar()
        or 0
    )
    active_workers_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            WorkerTemplate.is_active.is_(True),
            WorkerTemplate.status == "active",
        )
        .scalar()
        or 0
    )
    gross, platform_share, creator_share = (
        db.query(
            func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.platform_fee_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
        )
        .filter(
            WorkerRevenueEvent.creator_user_id == creator_user_id,
            WorkerRevenueEvent.created_at >= start_dt,
            WorkerRevenueEvent.created_at <= end_dt,
        )
        .one()
    )
    install_trend_rows = (
        db.query(func.date(WorkerSubscription.created_at), func.count(WorkerSubscription.id))
        .join(WorkerTemplate, WorkerSubscription.worker_template_id == WorkerTemplate.id)
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            WorkerSubscription.created_at >= start_dt,
            WorkerSubscription.created_at <= end_dt,
        )
        .group_by(func.date(WorkerSubscription.created_at))
        .all()
    )
    run_trend_rows = (
        db.query(func.date(WorkerRun.created_at), func.count(WorkerRun.id))
        .join(WorkerTemplate, WorkerRun.template_id == WorkerTemplate.id)
        .filter(
            WorkerTemplate.creator_user_id == creator_user_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
        )
        .group_by(func.date(WorkerRun.created_at))
        .all()
    )
    return {
        "published_workers_count": int(published_workers_count),
        "total_installs": int(total_installs),
        "total_runs": int(total_runs),
        "active_workers_count": int(active_workers_count),
        "paid_workers_count": int(paid_workers_count),
        "free_workers_count": int(free_workers_count),
        "estimated_total_revenue": int(gross or 0),
        "estimated_platform_share": int(platform_share or 0),
        "estimated_creator_share": int(creator_share or 0),
        "recent_install_trend": _series_from_rows(install_trend_rows, start=start_dt, end=end_dt),
        "recent_run_trend": _series_from_rows(run_trend_rows, start=start_dt, end=end_dt),
    }


def creator_workers_list(db: Session, *, creator_user_id: uuid.UUID) -> list[dict[str, Any]]:
    templates = (
        db.query(WorkerTemplate)
        .filter(WorkerTemplate.creator_user_id == creator_user_id)
        .order_by(WorkerTemplate.created_at.desc())
        .all()
    )
    template_ids = [item.id for item in templates]
    if not template_ids:
        return []
    run_rows = (
        db.query(WorkerRun.template_id, func.count(WorkerRun.id), func.count(func.distinct(WorkerRun.workspace_id)))
        .filter(WorkerRun.template_id.in_(template_ids))
        .group_by(WorkerRun.template_id)
        .all()
    )
    run_map = {row[0]: {"runs": int(row[1] or 0), "active_workspaces": int(row[2] or 0)} for row in run_rows}
    purchase_rows = (
        db.query(
            WorkerSubscription.worker_template_id,
            func.count(WorkerSubscription.id),
            func.coalesce(func.sum(WorkerSubscription.price_cents), 0),
        )
        .filter(
            WorkerSubscription.worker_template_id.in_(template_ids),
            WorkerSubscription.status.in_(
                (
                    WorkerEntitlementStatus.ACTIVE.value,
                    WorkerEntitlementStatus.PENDING.value,
                )
            ),
        )
        .group_by(WorkerSubscription.worker_template_id)
        .all()
    )
    purchase_map = {row[0]: {"purchases": int(row[1] or 0), "revenue": int(row[2] or 0)} for row in purchase_rows}
    items: list[dict[str, Any]] = []
    for template in templates:
        run_info = run_map.get(template.id, {"runs": 0, "active_workspaces": 0})
        purchase_info = purchase_map.get(template.id, {"purchases": 0, "revenue": 0})
        items.append(
            {
                "worker_template_id": template.id,
                "name": template.display_name or template.name,
                "slug": template.slug,
                "category": template.category,
                "pricing_type": template.pricing_type,
                "installs": int(template.install_count or 0),
                "runs": int(run_info["runs"]),
                "active_workspaces": int(run_info["active_workspaces"]),
                "purchase_count": int(purchase_info["purchases"]),
                "estimated_revenue": int(purchase_info["revenue"]),
                "moderation_status": template.moderation_status,
                "created_at": template.created_at,
                "published_at": template.updated_at if template.status == "active" else None,
            }
        )
    return items


def creator_worker_analytics(
    db: Session,
    *,
    creator_user_id: uuid.UUID,
    worker_template_id: uuid.UUID,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> dict[str, Any]:
    template = db.get(WorkerTemplate, worker_template_id)
    if not template or template.creator_user_id != creator_user_id:
        raise HTTPException(status_code=404, detail="Worker template not found")
    start_dt, end_dt = resolve_date_window(range_value=range_value, start_date=start_date, end_date=end_date)
    install_rows = (
        db.query(func.date(WorkerSubscription.created_at), func.count(WorkerSubscription.id))
        .filter(
            WorkerSubscription.worker_template_id == worker_template_id,
            WorkerSubscription.created_at >= start_dt,
            WorkerSubscription.created_at <= end_dt,
        )
        .group_by(func.date(WorkerSubscription.created_at))
        .all()
    )
    run_rows = (
        db.query(func.date(WorkerRun.created_at), func.count(WorkerRun.id))
        .filter(
            WorkerRun.template_id == worker_template_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
        )
        .group_by(func.date(WorkerRun.created_at))
        .all()
    )
    active_ws_rows = (
        db.query(func.date(WorkerRun.created_at), func.count(func.distinct(WorkerRun.workspace_id)))
        .filter(
            WorkerRun.template_id == worker_template_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
        )
        .group_by(func.date(WorkerRun.created_at))
        .all()
    )
    purchase_rows = (
        db.query(func.date(WorkerSubscription.created_at), func.count(WorkerSubscription.id))
        .filter(
            WorkerSubscription.worker_template_id == worker_template_id,
            WorkerSubscription.created_at >= start_dt,
            WorkerSubscription.created_at <= end_dt,
            WorkerSubscription.price_cents > 0,
        )
        .group_by(func.date(WorkerSubscription.created_at))
        .all()
    )
    revenue_rows = (
        db.query(func.date(WorkerRevenueEvent.created_at), func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0))
        .filter(
            WorkerRevenueEvent.worker_template_id == worker_template_id,
            WorkerRevenueEvent.created_at >= start_dt,
            WorkerRevenueEvent.created_at <= end_dt,
        )
        .group_by(func.date(WorkerRevenueEvent.created_at))
        .all()
    )
    recent_failures = (
        db.query(WorkerRun.id, WorkerRun.error_message, WorkerRun.created_at)
        .filter(
            WorkerRun.template_id == worker_template_id,
            WorkerRun.status == "failed",
        )
        .order_by(WorkerRun.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "worker_template_id": worker_template_id,
        "installs_over_time": _series_from_rows(install_rows, start=start_dt, end=end_dt),
        "runs_over_time": _series_from_rows(run_rows, start=start_dt, end=end_dt),
        "active_workspaces_over_time": _series_from_rows(active_ws_rows, start=start_dt, end=end_dt),
        "purchases_over_time": _series_from_rows(purchase_rows, start=start_dt, end=end_dt),
        "revenue_over_time": _series_from_rows(revenue_rows, start=start_dt, end=end_dt),
        "recent_failures": [
            {"run_id": str(row[0]), "error_message": row[1], "created_at": row[2]} for row in recent_failures
        ],
    }


def creator_payouts_summary(
    db: Session,
    *,
    creator_user_id: uuid.UUID,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> dict[str, Any]:
    start_dt, end_dt = resolve_date_window(range_value=range_value, start_date=start_date, end_date=end_date)
    gross, creator_share, platform_share = (
        db.query(
            func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
            func.coalesce(func.sum(WorkerRevenueEvent.platform_fee_cents), 0),
        )
        .filter(
            WorkerRevenueEvent.creator_user_id == creator_user_id,
            WorkerRevenueEvent.created_at >= start_dt,
            WorkerRevenueEvent.created_at <= end_dt,
        )
        .one()
    )
    pending = (
        db.query(func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0))
        .filter(
            WorkerRevenueEvent.creator_user_id == creator_user_id,
            WorkerRevenueEvent.revenue_type.in_(("purchase_pending", "pending")),
            WorkerRevenueEvent.created_at >= start_dt,
            WorkerRevenueEvent.created_at <= end_dt,
        )
        .scalar()
        or 0
    )
    return {
        "estimated_gross_revenue": int(gross or 0),
        "estimated_creator_share": int(creator_share or 0),
        "estimated_platform_share": int(platform_share or 0),
        "pending_payout_estimate": int(pending or 0),
        "paid_out_estimate": 0,
        "refund_estimate": 0,
        "disclaimer": "Revenue values are estimates for platform reporting and not finalized accounting.",
    }


def creator_activity(db: Session, *, creator_user_id: uuid.UUID, limit: int = 50) -> list[dict[str, Any]]:
    events = (
        db.query(AuditLog)
        .filter(AuditLog.actor_id == str(creator_user_id))
        .order_by(AuditLog.created_at.desc())
        .limit(max(limit, 1))
        .all()
    )
    return [
        {"event_name": item.event_name, "created_at": item.created_at, "payload": item.payload_json or {}}
        for item in events
    ]


def workspace_summary(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> dict[str, Any]:
    start_dt, end_dt = resolve_date_window(range_value=range_value, start_date=start_date, end_date=end_date)
    installed_workers_count = (
        db.query(func.count(WorkerInstance.id)).filter(WorkerInstance.workspace_id == workspace_id).scalar() or 0
    )
    published_workers_count = (
        db.query(func.count(WorkerTemplate.id))
        .filter(
            WorkerTemplate.workspace_id == workspace_id,
            WorkerTemplate.visibility.in_(
                (
                    WorkerTemplateVisibility.PUBLIC.value,
                    WorkerTemplateVisibility.MARKETPLACE.value,
                )
            ),
        )
        .scalar()
        or 0
    )
    total_runs = db.query(func.count(WorkerRun.id)).filter(WorkerRun.workspace_id == workspace_id).scalar() or 0
    runs_this_period = (
        db.query(func.count(WorkerRun.id))
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
        )
        .scalar()
        or 0
    )
    chain_runs_this_period = (
        db.query(func.count(WorkerRun.id))
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
            or_(WorkerRun.triggered_by == "chain", WorkerRun.run_type == "chain_execution"),
        )
        .scalar()
        or 0
    )
    success_runs = (
        db.query(func.count(WorkerRun.id))
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
            WorkerRun.status.in_(("completed", "success")),
        )
        .scalar()
        or 0
    )
    failed_runs = (
        db.query(func.count(WorkerRun.id))
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
            WorkerRun.status == "failed",
        )
        .scalar()
        or 0
    )
    success_rate = float(success_runs / runs_this_period) if runs_this_period else 0.0
    top_used_rows = (
        db.query(
            WorkerTemplate.id,
            WorkerTemplate.display_name,
            func.count(WorkerRun.id),
        )
        .join(WorkerInstance, WorkerRun.instance_id == WorkerInstance.id)
        .join(WorkerTemplate, WorkerInstance.template_id == WorkerTemplate.id)
        .filter(WorkerRun.workspace_id == workspace_id)
        .group_by(WorkerTemplate.id, WorkerTemplate.display_name)
        .order_by(func.count(WorkerRun.id).desc())
        .limit(10)
        .all()
    )
    ent = get_workspace_entitlements(db, workspace_id=workspace_id)
    percent_used: dict[str, float] = {}
    for key, limit_key in (
        ("worker_drafts", "max_worker_drafts"),
        ("published_workers", "max_published_workers"),
        ("worker_installs", "max_worker_installs_per_workspace"),
        ("worker_runs_month", "max_worker_runs_per_month"),
    ):
        limit = ent.limits.get(limit_key)
        usage = ent.usage.get(key, 0)
        if limit is None or int(limit) <= 0:
            percent_used[key] = 0.0
        else:
            percent_used[key] = min((usage / float(limit)) * 100.0, 100.0)
    return {
        "installed_workers_count": int(installed_workers_count),
        "published_workers_count": int(published_workers_count),
        "total_runs": int(total_runs),
        "runs_this_period": int(runs_this_period),
        "chain_runs_this_period": int(chain_runs_this_period),
        "success_rate": success_rate,
        "failed_runs": int(failed_runs),
        "top_used_workers": [
            {"worker_template_id": str(row[0]), "name": row[1], "runs": int(row[2] or 0)} for row in top_used_rows
        ],
        "plan": ent.plan,
        "limits": ent.limits,
        "usage": ent.usage,
        "percent_of_limit_used": percent_used,
    }


def workspace_activity(db: Session, *, workspace_id: uuid.UUID, limit: int = 50) -> list[dict[str, Any]]:
    events = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(max(limit, 1))
        .all()
    )
    return [{"event_name": item.event_name, "created_at": item.created_at, "payload": item.payload_json or {}} for item in events]


def workspace_usage_history(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    range_value: str | None,
    start_date: date | None,
    end_date: date | None,
) -> list[dict[str, Any]]:
    start_dt, end_dt = resolve_date_window(range_value=range_value, start_date=start_date, end_date=end_date)
    run_rows = (
        db.query(
            func.date(WorkerRun.created_at),
            func.count(WorkerRun.id),
            func.sum(case((WorkerRun.status.in_(("completed", "success")), 1), else_=0)),
            func.sum(case((WorkerRun.status == "failed", 1), else_=0)),
            func.sum(case((or_(WorkerRun.triggered_by == "chain", WorkerRun.run_type == "chain_execution"), 1), else_=0)),
        )
        .filter(
            WorkerRun.workspace_id == workspace_id,
            WorkerRun.created_at >= start_dt,
            WorkerRun.created_at <= end_dt,
        )
        .group_by(func.date(WorkerRun.created_at))
        .all()
    )
    install_rows = (
        db.query(func.date(WorkerInstance.created_at), func.count(WorkerInstance.id))
        .filter(
            WorkerInstance.workspace_id == workspace_id,
            WorkerInstance.created_at >= start_dt,
            WorkerInstance.created_at <= end_dt,
        )
        .group_by(func.date(WorkerInstance.created_at))
        .all()
    )
    run_map: dict[str, dict[str, int]] = {}
    for row in run_rows:
        day = str(row[0])
        run_map[day] = {
            "worker_runs": int(row[1] or 0),
            "successful_runs": int(row[2] or 0),
            "failed_runs": int(row[3] or 0),
            "chain_runs": int(row[4] or 0),
        }
    install_map = {str(row[0]): int(row[1] or 0) for row in install_rows}
    points: list[dict[str, Any]] = []
    cursor = start_dt.date()
    while cursor <= end_dt.date():
        day = cursor.isoformat()
        run_day = run_map.get(day, {"worker_runs": 0, "successful_runs": 0, "failed_runs": 0, "chain_runs": 0})
        points.append(
            {
                "date": day,
                "worker_runs": run_day["worker_runs"],
                "chain_runs": run_day["chain_runs"],
                "installs": install_map.get(day, 0),
                "successful_runs": run_day["successful_runs"],
                "failed_runs": run_day["failed_runs"],
            }
        )
        cursor += timedelta(days=1)
    return points


def admin_platform_summary(db: Session) -> dict[str, Any]:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_workspaces = db.query(func.count(Workspace.id)).scalar() or 0
    total_subscriptions_active = (
        db.query(func.count(WorkspaceSubscription.id))
        .filter(WorkspaceSubscription.status.in_(("active", "trialing", "past_due")))
        .scalar()
        or 0
    )
    plan_counts_rows = (
        db.query(SubscriptionPlan.code, func.count(WorkspaceSubscription.id))
        .join(WorkspaceSubscription, WorkspaceSubscription.plan_id == SubscriptionPlan.id)
        .filter(WorkspaceSubscription.status.in_(("active", "trialing", "past_due")))
        .group_by(SubscriptionPlan.code)
        .all()
    )
    subscriptions_by_plan = {row[0]: int(row[1] or 0) for row in plan_counts_rows}
    total_published_workers = (
        db.query(func.count(WorkerTemplate.id))
        .filter(WorkerTemplate.visibility.in_(("public", "marketplace")))
        .scalar()
        or 0
    )
    total_marketplace_workers = (
        db.query(func.count(WorkerTemplate.id))
        .filter(WorkerTemplate.visibility == "marketplace")
        .scalar()
        or 0
    )
    total_public_workers = (
        db.query(func.count(WorkerTemplate.id))
        .filter(WorkerTemplate.visibility == "public")
        .scalar()
        or 0
    )
    total_installs = db.query(func.coalesce(func.sum(WorkerTemplate.install_count), 0)).scalar() or 0
    total_runs = db.query(func.count(WorkerRun.id)).scalar() or 0
    total_paid_purchases = (
        db.query(func.count(WorkerSubscription.id))
        .filter(WorkerSubscription.price_cents > 0, WorkerSubscription.status.in_(("active", "pending")))
        .scalar()
        or 0
    )
    estimated_mrr = (
        db.query(func.coalesce(func.sum(SubscriptionPlan.monthly_price_cents), 0))
        .join(WorkspaceSubscription, WorkspaceSubscription.plan_id == SubscriptionPlan.id)
        .filter(WorkspaceSubscription.status.in_(("active", "trialing", "past_due")))
        .scalar()
        or 0
    )
    estimated_arr = int(estimated_mrr) * 12
    top_workers_rows = (
        db.query(
            WorkerTemplate.id,
            WorkerTemplate.display_name,
            WorkerTemplate.install_count,
            func.count(WorkerRun.id),
        )
        .outerjoin(WorkerRun, WorkerRun.template_id == WorkerTemplate.id)
        .group_by(WorkerTemplate.id, WorkerTemplate.display_name, WorkerTemplate.install_count)
        .order_by(func.count(WorkerRun.id).desc(), WorkerTemplate.install_count.desc())
        .limit(10)
        .all()
    )
    top_creators_rows = (
        db.query(
            User.id,
            User.full_name,
            User.email,
            func.count(func.distinct(WorkerTemplate.id)),
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
        )
        .join(WorkerTemplate, WorkerTemplate.creator_user_id == User.id)
        .outerjoin(WorkerRevenueEvent, WorkerRevenueEvent.creator_user_id == User.id)
        .group_by(User.id, User.full_name, User.email)
        .order_by(func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0).desc())
        .limit(10)
        .all()
    )
    return {
        "total_users": int(total_users),
        "total_workspaces": int(total_workspaces),
        "total_subscriptions_active": int(total_subscriptions_active),
        "subscriptions_by_plan": subscriptions_by_plan,
        "total_published_workers": int(total_published_workers),
        "total_marketplace_workers": int(total_marketplace_workers),
        "total_public_workers": int(total_public_workers),
        "total_installs": int(total_installs),
        "total_runs": int(total_runs),
        "total_paid_purchases": int(total_paid_purchases),
        "estimated_mrr": int(estimated_mrr),
        "estimated_arr_run_rate": int(estimated_arr),
        "top_workers": [
            {
                "worker_template_id": str(row[0]),
                "name": row[1],
                "installs": int(row[2] or 0),
                "runs": int(row[3] or 0),
            }
            for row in top_workers_rows
        ],
        "top_creators": [
            {
                "creator_user_id": str(row[0]),
                "name": row[1],
                "email": row[2],
                "published_workers": int(row[3] or 0),
                "estimated_revenue": int(row[4] or 0),
            }
            for row in top_creators_rows
        ],
    }


def admin_workers_list(
    db: Session,
    *,
    moderation_status: str | None,
    category: str | None,
    pricing_type: str | None,
    creator_user_id: uuid.UUID | None,
    visibility: str | None,
    flagged_only: bool,
) -> list[dict[str, Any]]:
    query = db.query(WorkerTemplate)
    if moderation_status:
        query = query.filter(WorkerTemplate.moderation_status == moderation_status)
    if category:
        query = query.filter(WorkerTemplate.category == category)
    if pricing_type:
        query = query.filter(WorkerTemplate.pricing_type == pricing_type)
    if creator_user_id:
        query = query.filter(WorkerTemplate.creator_user_id == creator_user_id)
    if visibility:
        query = query.filter(WorkerTemplate.visibility == visibility)
    if flagged_only:
        query = query.filter(WorkerTemplate.report_count > 0)
    templates = query.order_by(WorkerTemplate.updated_at.desc()).limit(500).all()
    template_ids = [item.id for item in templates]
    run_rows = (
        db.query(WorkerRun.template_id, func.count(WorkerRun.id))
        .filter(WorkerRun.template_id.in_(template_ids) if template_ids else False)
        .group_by(WorkerRun.template_id)
        .all()
    )
    run_map = {row[0]: int(row[1] or 0) for row in run_rows}
    return [
        {
            "worker_template_id": item.id,
            "name": item.display_name or item.name,
            "slug": item.slug,
            "category": item.category,
            "pricing_type": item.pricing_type,
            "visibility": item.visibility,
            "moderation_status": item.moderation_status,
            "report_count": int(item.report_count or 0),
            "installs": int(item.install_count or 0),
            "runs": run_map.get(item.id, 0),
            "creator_user_id": item.creator_user_id,
        }
        for item in templates
    ]


def admin_worker_detail(db: Session, *, worker_template_id: uuid.UUID) -> dict[str, Any]:
    template = db.get(WorkerTemplate, worker_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    creator = db.get(User, template.creator_user_id) if template.creator_user_id else None
    installs = int(template.install_count or 0)
    runs = (
        db.query(func.count(WorkerRun.id))
        .filter(WorkerRun.template_id == worker_template_id)
        .scalar()
        or 0
    )
    estimated_revenue = (
        db.query(func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0))
        .filter(WorkerRevenueEvent.worker_template_id == worker_template_id)
        .scalar()
        or 0
    )
    recent_reports = (
        db.query(WorkerReport)
        .filter(WorkerReport.worker_template_id == worker_template_id)
        .order_by(WorkerReport.created_at.desc())
        .limit(20)
        .all()
    )
    recent_activity = (
        db.query(AuditLog)
        .filter(AuditLog.payload_json.is_not(None))
        .order_by(AuditLog.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "template": template,
        "creator": creator,
        "installs": int(installs),
        "runs": int(runs),
        "estimated_revenue": int(estimated_revenue or 0),
        "moderation_status": template.moderation_status,
        "report_count": int(template.report_count or 0),
        "recent_reports": [
            {
                "report_id": str(report.id),
                "reason": report.reason,
                "status": report.status,
                "created_at": report.created_at,
                "details": report.details,
            }
            for report in recent_reports
        ],
        "recent_activity": [
            {"event_name": item.event_name, "created_at": item.created_at, "payload": item.payload_json or {}}
            for item in recent_activity
        ],
    }


def moderate_worker(
    db: Session,
    *,
    worker_template_id: uuid.UUID,
    reviewer_user_id: uuid.UUID,
    action: str,
    moderation_notes: str | None,
) -> WorkerTemplate:
    template = db.get(WorkerTemplate, worker_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    normalized = (action or "").strip().lower()
    mapping = {
        "approve": WorkerModerationStatus.APPROVED.value,
        "reject": WorkerModerationStatus.REJECTED.value,
        "hide": WorkerModerationStatus.HIDDEN.value,
        "unhide": WorkerModerationStatus.APPROVED.value,
        "request_changes": WorkerModerationStatus.PENDING_REVIEW.value,
    }
    if normalized not in mapping:
        raise HTTPException(status_code=400, detail="Unsupported moderation action")
    template.moderation_status = mapping[normalized]
    template.moderation_notes = moderation_notes
    template.reviewed_by_user_id = reviewer_user_id
    template.reviewed_at = datetime.now(UTC)
    db.flush()
    return template


def admin_creators_list(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(
            User.id,
            User.email,
            User.full_name,
            func.count(func.distinct(WorkerTemplate.id)),
            func.coalesce(func.sum(WorkerTemplate.install_count), 0),
            func.count(WorkerRun.id),
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
            func.coalesce(func.sum(WorkerTemplate.report_count), 0),
            func.max(case((CreatorMonetizationProfile.payouts_enabled.is_(True), 1), else_=0)),
            func.max(case((CreatorMonetizationProfile.onboarding_complete.is_(True), 1), else_=0)),
        )
        .join(WorkerTemplate, WorkerTemplate.creator_user_id == User.id)
        .outerjoin(WorkerRun, WorkerRun.template_id == WorkerTemplate.id)
        .outerjoin(WorkerRevenueEvent, WorkerRevenueEvent.creator_user_id == User.id)
        .outerjoin(CreatorMonetizationProfile, CreatorMonetizationProfile.user_id == User.id)
        .group_by(User.id, User.email, User.full_name)
        .order_by(func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0).desc())
        .all()
    )
    return [
        {
            "creator_user_id": row[0],
            "email": row[1],
            "full_name": row[2],
            "published_workers": int(row[3] or 0),
            "installs": int(row[4] or 0),
            "runs": int(row[5] or 0),
            "estimated_revenue": int(row[6] or 0),
            "moderation_issues_count": int(row[7] or 0),
            "payouts_enabled": bool(row[8]),
            "onboarding_complete": bool(row[9]),
        }
        for row in rows
    ]


def admin_billing_summary(db: Session) -> dict[str, Any]:
    active_rows = (
        db.query(SubscriptionPlan.code, func.count(WorkspaceSubscription.id))
        .join(WorkspaceSubscription, WorkspaceSubscription.plan_id == SubscriptionPlan.id)
        .filter(WorkspaceSubscription.status.in_(("active", "trialing", "past_due")))
        .group_by(SubscriptionPlan.code)
        .all()
    )
    active_subscriptions_by_plan = {row[0]: int(row[1] or 0) for row in active_rows}
    churned_subscriptions_count = (
        db.query(func.count(WorkspaceSubscription.id))
        .filter(WorkspaceSubscription.status.in_(("canceled", "unpaid")))
        .scalar()
        or 0
    )
    failed_payments_count = (
        db.query(func.count(WorkspaceSubscription.id))
        .filter(WorkspaceSubscription.status.in_(("past_due", "incomplete", "incomplete_expired", "unpaid")))
        .scalar()
        or 0
    )
    estimated_platform_revenue = (
        db.query(func.coalesce(func.sum(WorkerRevenueEvent.platform_fee_cents), 0)).scalar()
        or 0
    )
    top_workers = (
        db.query(
            WorkerTemplate.id,
            WorkerTemplate.display_name,
            func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0),
        )
        .join(WorkerRevenueEvent, WorkerRevenueEvent.worker_template_id == WorkerTemplate.id)
        .group_by(WorkerTemplate.id, WorkerTemplate.display_name)
        .order_by(func.coalesce(func.sum(WorkerRevenueEvent.gross_cents), 0).desc())
        .limit(10)
        .all()
    )
    top_creators = (
        db.query(
            User.id,
            User.email,
            func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0),
        )
        .join(WorkerRevenueEvent, WorkerRevenueEvent.creator_user_id == User.id)
        .group_by(User.id, User.email)
        .order_by(func.coalesce(func.sum(WorkerRevenueEvent.creator_payout_cents), 0).desc())
        .limit(10)
        .all()
    )
    return {
        "active_subscriptions_by_plan": active_subscriptions_by_plan,
        "churned_subscriptions_count": int(churned_subscriptions_count),
        "failed_payments_count": int(failed_payments_count),
        "estimated_platform_revenue": int(estimated_platform_revenue or 0),
        "top_grossing_workers": [
            {"worker_template_id": str(row[0]), "name": row[1], "gross_revenue": int(row[2] or 0)}
            for row in top_workers
        ],
        "top_grossing_creators": [
            {"creator_user_id": str(row[0]), "email": row[1], "creator_revenue": int(row[2] or 0)}
            for row in top_creators
        ],
    }


def create_worker_report(
    db: Session,
    *,
    worker_template_id: uuid.UUID,
    reporter_user_id: uuid.UUID,
    workspace_id: uuid.UUID | None,
    reason: str,
    details: str | None,
) -> WorkerReport:
    template = db.get(WorkerTemplate, worker_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Worker template not found")
    report = WorkerReport(
        worker_template_id=worker_template_id,
        reporter_user_id=reporter_user_id,
        workspace_id=workspace_id,
        reason=(reason or "").strip(),
        details=details,
        status=WorkerReportStatus.OPEN.value,
    )
    db.add(report)
    template.report_count = int(template.report_count or 0) + 1
    db.flush()
    return report


def is_public_worker_visible(template: WorkerTemplate) -> bool:
    if template.moderation_status in {WorkerModerationStatus.REJECTED.value, WorkerModerationStatus.HIDDEN.value}:
        return False
    return True
