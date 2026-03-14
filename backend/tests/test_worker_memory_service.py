import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    User,
    WorkerInstance,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
    Workspace,
)
from app.schemas.api import WorkerTemplateCreate
from app.services.worker_memory import (
    build_worker_memory_bundle,
    read_worker_memory,
    store_worker_run_context,
    upsert_worker_memory,
)
from app.services.worker_templates import create_worker_template


def _create_workspace_user(db: Session, *, email: str) -> tuple[Workspace, User]:
    workspace = Workspace(company_name=f"Workspace-{email}")
    db.add(workspace)
    db.flush()
    user = User(
        workspace_id=workspace.id,
        full_name="Memory User",
        email=email,
        password_hash="test",
        role="owner",
    )
    db.add(user)
    db.flush()
    return workspace, user


def _create_template_instance(db: Session, *, workspace: Workspace, user: User, slug: str) -> WorkerInstance:
    template = create_worker_template(
        db,
        workspace_id=workspace.id,
        creator_user_id=user.id,
        payload=WorkerTemplateCreate(
            name=f"Template-{slug}",
            slug=slug,
            short_description="memory template",
            description="Template used in worker memory service tests.",
            category="ops",
            worker_type="custom_worker",
            worker_category="ops",
            visibility=WorkerTemplateVisibility.WORKSPACE,
            status=WorkerTemplateStatus.ACTIVE,
            instructions="Persist useful memory context.",
            model_name="mock-ai-v1",
            config_json={"mission": "memory"},
            capabilities_json={},
            actions_json=[],
            tools_json=[],
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
        name=f"Instance-{slug}",
        status="active",
        runtime_config_json={},
        memory_scope=WorkerMemoryScope.INSTANCE.value,
    )
    db.add(instance)
    db.flush()
    return instance


def test_worker_memory_scopes_and_workspace_boundaries():
    db = SessionLocal()
    try:
        workspace_a, user_a = _create_workspace_user(db, email="memory-a@test.com")
        workspace_b, user_b = _create_workspace_user(db, email="memory-b@test.com")
        instance_a = _create_template_instance(db, workspace=workspace_a, user=user_a, slug="memory-a")
        instance_b = _create_template_instance(db, workspace=workspace_b, user=user_b, slug="memory-b")

        upsert_worker_memory(
            db,
            workspace_id=workspace_a.id,
            memory_key="lead_profile",
            memory_value={"icp": "SaaS"},
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )
        upsert_worker_memory(
            db,
            workspace_id=workspace_a.id,
            memory_key="lead_profile",
            memory_value={"icp": "FinTech"},
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )
        upsert_worker_memory(
            db,
            workspace_id=workspace_a.id,
            memory_key="workspace_policy",
            memory_value={"send_window": "weekday"},
            scope=WorkerMemoryScope.WORKSPACE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )

        instance_records = read_worker_memory(
            db,
            workspace_id=workspace_a.id,
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance_a.id,
        )
        assert len(instance_records) == 1
        assert instance_records[0].memory_value_json == {"icp": "FinTech"}

        instance_bundle = build_worker_memory_bundle(
            db,
            workspace_id=workspace_a.id,
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )
        assert instance_bundle["lead_profile"] == {"icp": "FinTech"}
        assert "workspace_policy" not in instance_bundle

        workspace_bundle = build_worker_memory_bundle(
            db,
            workspace_id=workspace_a.id,
            scope=WorkerMemoryScope.WORKSPACE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )
        assert workspace_bundle["lead_profile"] == {"icp": "FinTech"}
        assert workspace_bundle["workspace_policy"] == {"send_window": "weekday"}

        isolated_bundle = build_worker_memory_bundle(
            db,
            workspace_id=workspace_b.id,
            scope=WorkerMemoryScope.WORKSPACE,
            instance_id=instance_b.id,
            template_id=instance_b.template_id,
        )
        assert "lead_profile" not in isolated_bundle
        assert "workspace_policy" not in isolated_bundle

        none_bundle = build_worker_memory_bundle(
            db,
            workspace_id=workspace_a.id,
            scope=WorkerMemoryScope.NONE,
            instance_id=instance_a.id,
            template_id=instance_a.template_id,
        )
        assert none_bundle == {}
    finally:
        db.close()


def test_store_worker_run_context_persists_structured_memory():
    db = SessionLocal()
    try:
        workspace, user = _create_workspace_user(db, email="memory-run@test.com")
        instance = _create_template_instance(db, workspace=workspace, user=user, slug="memory-run")
        run_id = uuid.uuid4()

        store_worker_run_context(
            db,
            workspace_id=workspace.id,
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance.id,
            template_id=instance.template_id,
            run_id=run_id,
            summary="Execution completed",
            runtime_input={"job": "sync"},
            output={"result": "ok"},
            suggested_actions=["monitor_outbound_events"],
            notes=["all_good"],
            token_usage_input=120,
            token_usage_output=60,
            cost_cents=2,
        )

        bundle = build_worker_memory_bundle(
            db,
            workspace_id=workspace.id,
            scope=WorkerMemoryScope.INSTANCE,
            instance_id=instance.id,
            template_id=instance.template_id,
        )
        assert bundle["last_run_summary"] == {"summary": "Execution completed"}
        assert bundle["last_runtime_input"] == {"job": "sync"}
        assert bundle["last_run_output"] == {"result": "ok"}
        assert bundle["last_run_metadata"]["run_id"] == str(run_id)
        assert bundle["last_run_metadata"]["cost_cents"] == 2
    finally:
        db.close()
