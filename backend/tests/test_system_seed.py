from app.db.session import SessionLocal
from app.models import WorkerTemplate, WorkerTool
from app.services.system_seed import seed_system_worker_templates_and_tools
from app.services.worker_definitions import SYSTEM_TEMPLATE_SEEDS


def test_system_template_and_tool_seed_is_idempotent():
    db = SessionLocal()
    try:
        expected_template_keys = {item["template_key"] for item in SYSTEM_TEMPLATE_SEEDS}
        expected_template_names = {item["name"] for item in SYSTEM_TEMPLATE_SEEDS}
        expected_tools = {"email_sender", "calendar_scheduler", "lead_recorder"}

        summary_first = seed_system_worker_templates_and_tools(db)
        db.commit()
        assert expected_template_names.issubset(set(summary_first.template_names))
        assert expected_tools.issubset(set(summary_first.common_tool_slugs))

        templates_first = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.template_key.in_(tuple(expected_template_keys)))
            .all()
        )
        tools_first = db.query(WorkerTool).filter(WorkerTool.slug.in_(tuple(expected_tools))).all()
        assert len(templates_first) == len(expected_template_keys)
        assert len(tools_first) == len(expected_tools)

        summary_second = seed_system_worker_templates_and_tools(db)
        db.commit()
        assert summary_second.templates_created == 0
        assert summary_second.tools_created == 0

        templates_second = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.template_key.in_(tuple(expected_template_keys)))
            .all()
        )
        tools_second = db.query(WorkerTool).filter(WorkerTool.slug.in_(tuple(expected_tools))).all()
        assert len(templates_second) == len(templates_first)
        assert len(tools_second) == len(tools_first)
    finally:
        db.close()
