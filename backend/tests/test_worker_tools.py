from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    AuditLog,
    Lead,
    User,
    Worker,
    WorkerInstance,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerRun,
    WorkerRunStatus,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
    WorkerTool,
    Workspace,
)
from app.schemas.api import WorkerTemplateCreate
from app.services.worker_templates import create_worker_template
from app.services.worker_tools import ensure_system_worker_tools, invoke_tool_calls, resolve_template_allowed_tool_slugs


def _create_workspace_user(db: Session, *, email: str) -> tuple[Workspace, User]:
    workspace = Workspace(company_name=f"Tool Workspace {email}")
    db.add(workspace)
    db.flush()
    user = User(
        workspace_id=workspace.id,
        full_name="Tool User",
        email=email,
        password_hash="test",
        role="owner",
    )
    db.add(user)
    db.flush()
    return workspace, user


def test_tool_seed_and_template_allowed_resolution():
    db = SessionLocal()
    try:
        workspace, user = _create_workspace_user(db, email="tool-seed@test.com")
        seeded = ensure_system_worker_tools(db)
        slugs = {item.slug for item in seeded}
        assert {
            "email_sender",
            "sms_sender",
            "webhook_caller",
            "crm_updater",
            "calendar_scheduler",
            "lead_recorder",
            "internal_note_writer",
        }.issubset(slugs)

        template = create_worker_template(
            db,
            workspace_id=workspace.id,
            creator_user_id=user.id,
            payload=WorkerTemplateCreate(
                name="Tool Template",
                slug="tool-template",
                short_description="template with tools",
                description="Template for worker tool registry resolution tests.",
                category="ops",
                worker_type="custom_worker",
                worker_category="ops",
                visibility=WorkerTemplateVisibility.WORKSPACE,
                status=WorkerTemplateStatus.ACTIVE,
                instructions="Use tool calls carefully.",
                model_name="mock-ai-v1",
                config_json={},
                capabilities_json={},
                actions_json=[],
                tools_json=["internal_note_writer", "email_sender", "unknown_tool"],
                memory_enabled=True,
                chain_enabled=False,
                is_marketplace_listed=False,
                pricing_type=WorkerPricingType.INTERNAL,
                price_cents=0,
                currency="USD",
                tags_json=[],
            ),
        )

        allowed = resolve_template_allowed_tool_slugs(db, template)
        assert allowed == ["internal_note_writer", "email_sender"]

        email_tool = db.query(WorkerTool).filter(WorkerTool.slug == "email_sender").first()
        assert email_tool is not None
        email_tool.is_active = False
        db.flush()
        allowed_after_disable = resolve_template_allowed_tool_slugs(db, template)
        assert allowed_after_disable == ["internal_note_writer"]
    finally:
        db.close()


def test_tool_invocation_reuses_existing_services():
    db = SessionLocal()
    try:
        workspace, user = _create_workspace_user(db, email="tool-invoke@test.com")
        ensure_system_worker_tools(db)
        template = create_worker_template(
            db,
            workspace_id=workspace.id,
            creator_user_id=user.id,
            payload=WorkerTemplateCreate(
                name="Tool Runtime Template",
                slug="tool-runtime-template",
                short_description="runtime tools",
                description="Template for tool invocation tests.",
                category="ops",
                worker_type="custom_worker",
                worker_category="ops",
                visibility=WorkerTemplateVisibility.WORKSPACE,
                status=WorkerTemplateStatus.ACTIVE,
                instructions="Use allowed tools.",
                model_name="mock-ai-v1",
                config_json={},
                capabilities_json={},
                actions_json=[],
                tools_json=["lead_recorder", "crm_updater", "internal_note_writer"],
                memory_enabled=True,
                chain_enabled=False,
                is_marketplace_listed=False,
                pricing_type=WorkerPricingType.INTERNAL,
                price_cents=0,
                currency="USD",
                tags_json=[],
            ),
        )
        instance = WorkerInstance(
            workspace_id=workspace.id,
            template_id=template.id,
            owner_user_id=user.id,
            name="Tool Runtime Instance",
            status="active",
            runtime_config_json={},
            memory_scope=WorkerMemoryScope.INSTANCE.value,
        )
        db.add(instance)
        db.flush()
        worker = Worker(
            workspace_id=workspace.id,
            name="Tool Worker",
            worker_type="custom_worker",
            worker_category="ops",
            mission="Use tools",
            goal="Use tools",
            plan_version="v1",
            template_id=template.id,
            origin_type="template_install",
            is_custom_worker=True,
            is_internal=False,
            status="idle",
            tone="professional",
            send_limit_per_day=10,
            run_interval_minutes=60,
            config_json={},
        )
        db.add(worker)
        db.flush()
        run = WorkerRun(
            workspace_id=workspace.id,
            worker_id=worker.id,
            instance_id=instance.id,
            template_id=template.id,
            run_type="template_execution",
            status=WorkerRunStatus.RUNNING.value,
            input_json={},
        )
        db.add(run)
        db.flush()

        tool_results, rejected = invoke_tool_calls(
            db,
            workspace_id=workspace.id,
            instance_id=instance.id,
            template_id=template.id,
            worker_id=worker.id,
            run_id=run.id,
            allowed_tool_slugs=["lead_recorder", "crm_updater", "internal_note_writer"],
            tool_calls=[
                {
                    "tool": "lead_recorder",
                    "input": {"company_name": "Atlas", "email": "atlas@example.com", "full_name": "Taylor Atlas"},
                },
                {"tool": "internal_note_writer", "input": {"note": "Tool runtime note", "note_type": "runtime"}},
                {"tool": "email_sender", "input": {"campaign_id": "bad"}},
            ],
        )
        assert len(tool_results) == 2
        assert any(item["tool"] == "lead_recorder" and item["success"] for item in tool_results)
        assert any(item["tool"] == "internal_note_writer" and item["success"] for item in tool_results)
        assert rejected == [{"tool": "email_sender", "reason": "tool_not_allowed"}]

        lead_id = [item["output"]["lead_id"] for item in tool_results if item["tool"] == "lead_recorder"][0]
        crm_results, crm_rejected = invoke_tool_calls(
            db,
            workspace_id=workspace.id,
            instance_id=instance.id,
            template_id=template.id,
            worker_id=worker.id,
            run_id=run.id,
            allowed_tool_slugs=["crm_updater"],
            tool_calls=[{"tool": "crm_updater", "input": {"lead_id": lead_id, "enrichment_updates": {"icp_fit": "high"}}}],
        )
        assert crm_rejected == []
        assert crm_results[0]["success"] is True

        lead = db.query(Lead).filter(Lead.workspace_id == workspace.id, Lead.email == "atlas@example.com").first()
        assert lead is not None
        assert lead.enrichment_json["icp_fit"] == "high"
        note_log = (
            db.query(AuditLog)
            .filter(
                AuditLog.workspace_id == workspace.id,
                AuditLog.event_name == "internal_note_written",
            )
            .first()
        )
        assert note_log is not None
    finally:
        db.close()
