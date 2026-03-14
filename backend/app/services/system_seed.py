from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import WorkerTemplate, WorkerTool
from app.services.subscription_plans import ensure_default_subscription_plans
from app.services.worker_definitions import SYSTEM_TEMPLATE_SEEDS, ensure_builtin_worker_templates
from app.services.worker_tools import ensure_system_worker_tools

COMMON_TOOL_SLUGS = {"email_sender", "calendar_scheduler", "lead_recorder"}


@dataclass(frozen=True)
class SystemSeedSummary:
    templates_created: int
    tools_created: int
    plans_upserted: int
    template_names: list[str]
    common_tool_slugs: list[str]


def seed_system_worker_templates_and_tools(db: Session) -> SystemSeedSummary:
    template_keys = [item["template_key"] for item in SYSTEM_TEMPLATE_SEEDS]
    before_templates = (
        db.query(WorkerTemplate.template_key)
        .filter(WorkerTemplate.template_key.in_(template_keys))
        .all()
    )
    before_tools = db.query(WorkerTool.slug).filter(WorkerTool.slug.in_(tuple(COMMON_TOOL_SLUGS))).all()

    ensure_builtin_worker_templates(db)
    ensure_system_worker_tools(db)
    plans = ensure_default_subscription_plans(db)

    after_templates = (
        db.query(WorkerTemplate.template_key, WorkerTemplate.name)
        .filter(WorkerTemplate.template_key.in_(template_keys))
        .all()
    )
    after_tools = db.query(WorkerTool.slug).filter(WorkerTool.slug.in_(tuple(COMMON_TOOL_SLUGS))).all()

    return SystemSeedSummary(
        templates_created=max(len(after_templates) - len(before_templates), 0),
        tools_created=max(len(after_tools) - len(before_tools), 0),
        plans_upserted=len(plans),
        template_names=sorted({str(item[1]) for item in after_templates if item and item[1]}),
        common_tool_slugs=sorted({str(item[0]) for item in after_tools if item and item[0]}),
    )
