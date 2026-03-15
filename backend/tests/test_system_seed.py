from app.db.session import SessionLocal
from app.models import WorkerTemplate, WorkerTool
from app.services.system_seed import seed_system_worker_templates_and_tools
from app.services.worker_definitions import SYSTEM_TEMPLATE_SEEDS

INTERNAL_STACK_KEYS = {
    "internal-chief-marketing-worker",
    "internal-user-feedback-intelligence-worker",
    "internal-marketplace-curator-worker",
    "internal-creator-recruitment-worker",
    "internal-sales-outreach-worker",
    "internal-product-strategy-worker",
    "internal-content-marketing-worker",
    "internal-community-manager-worker",
    "internal-investor-update-worker",
    "internal-operations-coordinator-worker",
}
INTERNAL_STACK_SHARED_TAGS = {"thorpe-workforce", "internal-stack", "founder-os", "startup-ops"}
INTERNAL_STACK_ALLOWED_CATEGORIES = {"marketing", "research", "automation", "sales", "content"}


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


def test_internal_worker_stack_seed_integrity():
    db = SessionLocal()
    try:
        seed_system_worker_templates_and_tools(db)
        db.commit()

        templates = (
            db.query(WorkerTemplate)
            .filter(WorkerTemplate.template_key.in_(tuple(INTERNAL_STACK_KEYS)))
            .order_by(WorkerTemplate.template_key.asc())
            .all()
        )
        assert len(templates) == len(INTERNAL_STACK_KEYS)

        slugs = [item.slug for item in templates if item.slug]
        assert len(slugs) == len(set(slugs))

        template_keys = {item.template_key for item in templates}
        assert template_keys == INTERNAL_STACK_KEYS
        assert all(item.category in INTERNAL_STACK_ALLOWED_CATEGORIES for item in templates)
        assert all(item.visibility == "marketplace" for item in templates)
        assert all(item.is_marketplace_listed for item in templates)
        assert all(item.pricing_type == "free" and item.price_cents == 0 for item in templates)

        for template in templates:
            tags = set(template.tags_json or [])
            assert INTERNAL_STACK_SHARED_TAGS.issubset(tags)
            assert isinstance(template.config_json, dict)
            assert "input_schema" in template.config_json
            assert "output_schema" in template.config_json
            assert "prompt_template" in template.config_json
            assert "example_run_payload" in template.config_json

        chief_marketing = next(item for item in templates if item.template_key == "internal-chief-marketing-worker")
        chief_input = ((chief_marketing.config_json or {}).get("input_schema") or {}).get("properties") or {}
        assert chief_input.get("mention_self_as_worker", {}).get("type") == "boolean"

        community = next(item for item in templates if item.template_key == "internal-community-manager-worker")
        community_input = ((community.config_json or {}).get("input_schema") or {}).get("properties") or {}
        assert community_input.get("include_product_mention", {}).get("type") == "boolean"
    finally:
        db.close()
