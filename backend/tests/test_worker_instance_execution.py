import uuid

from app.db.session import SessionLocal
from app.models import (
    User,
    WorkerInstance,
    WorkerMemory,
    WorkerMemoryScope,
    WorkerPricingType,
    WorkerRun,
    WorkerRunStatus,
    WorkerTemplateStatus,
)
from app.models import WorkerTemplateVisibility
from app.schemas.api import WorkerTemplateCreate
from app.services.worker_templates import create_worker_template


def test_execute_worker_instance_manual_route(client, auth_headers):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "tester@example.com").first()
        assert user is not None

        template = create_worker_template(
            db,
            workspace_id=user.workspace_id,
            creator_user_id=user.id,
            payload=WorkerTemplateCreate(
                name="Execution Template",
                slug="execution-template",
                short_description="Exec template",
                description="A worker template used for execution testing.",
                category="ops",
                worker_type="custom_worker",
                worker_category="ops",
                visibility=WorkerTemplateVisibility.WORKSPACE,
                status=WorkerTemplateStatus.ACTIVE,
                instructions="Use available context and return structured JSON output.",
                model_name="mock-ai-v1",
                config_json={"mission": "run"},
                capabilities_json={"can_reason": True},
                actions_json=["monitor_outbound_events"],
                tools_json=["crm_lookup"],
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
            workspace_id=user.workspace_id,
            template_id=template.id,
            owner_user_id=user.id,
            name="Execution Instance",
            status="active",
            runtime_config_json={"region": "US"},
            memory_scope=WorkerMemoryScope.INSTANCE.value,
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
    finally:
        db.close()

    execute_res = client.post(
        f"/worker-instances/{instance.id}/execute",
        json={"runtime_input": {"job": "test-run"}, "trigger_source": "unit_test"},
        headers=auth_headers,
    )
    assert execute_res.status_code == 200
    execute_payload = execute_res.json()
    assert execute_payload["success"] is True
    assert execute_payload["queued"] is False
    assert execute_payload["status"] == WorkerRunStatus.COMPLETED.value

    db = SessionLocal()
    try:
        run = db.get(WorkerRun, uuid.UUID(execute_payload["run_id"]))
        assert run is not None
        assert run.instance_id == instance.id
        assert run.status == WorkerRunStatus.COMPLETED.value
        assert run.summary
        assert run.output_json is not None
        assert run.output_json["tool_calls"] == [{"tool": "crm_lookup", "input": {"source": "mock"}}]
        assert run.output_json["rejected_tool_calls"] == [{"tool": "disallowed_tool", "reason": "tool_not_allowed"}]
        assert run.token_usage_input > 0
        assert run.token_usage_output > 0
        assert run.cost_cents > 0

        refreshed_instance = db.get(WorkerInstance, instance.id)
        assert refreshed_instance is not None
        assert refreshed_instance.last_run_at is not None
        assert refreshed_instance.status == "active"

        memory = (
            db.query(WorkerMemory)
            .filter(
                WorkerMemory.workspace_id == refreshed_instance.workspace_id,
                WorkerMemory.instance_id == refreshed_instance.id,
                WorkerMemory.memory_key == "last_runtime_input",
            )
            .first()
        )
        assert memory is not None
    finally:
        db.close()
