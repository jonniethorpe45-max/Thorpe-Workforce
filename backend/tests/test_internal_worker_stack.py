import uuid

from app.db.session import SessionLocal
from app.models import WorkerRun, WorkerRunStatus
from app.services.system_seed import seed_system_worker_templates_and_tools

INTERNAL_STACK_SLUGS = {
    "chief-marketing-worker",
    "user-feedback-intelligence-worker",
    "marketplace-curator-worker",
    "creator-recruitment-worker",
    "internal-sales-outreach-worker",
    "product-strategy-worker",
    "content-marketing-worker",
    "community-manager-worker",
    "investor-update-worker",
    "operations-coordinator-worker",
}


def test_internal_stack_public_listing_presence(client):
    with SessionLocal() as db:
        seed_system_worker_templates_and_tools(db)
        db.commit()

    res = client.get("/public-workers")
    assert res.status_code == 200
    slugs = {item["slug"] for item in res.json() if item.get("slug")}
    assert INTERNAL_STACK_SLUGS.issubset(slugs)


def test_internal_stack_install_and_run_via_worker_template_flow(client, auth_headers):
    list_res = client.get("/workers/templates?include_public=true", headers=auth_headers)
    assert list_res.status_code == 200
    templates = list_res.json()
    chief_template = next((item for item in templates if item.get("slug") == "chief-marketing-worker"), None)
    assert chief_template is not None

    install_res = client.post(
        f"/workers/templates/{chief_template['id']}/install",
        json={
            "instance_name": "Internal Stack Chief Marketing",
            "runtime_config_overrides": {},
            "memory_scope": "instance",
        },
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance = install_res.json()

    run_res = client.post(
        f"/workers/instances/{instance['id']}/run",
        json={
            "runtime_input": {
                "product_name": "Thorpe Workforce",
                "target_audience": "real estate investors",
                "campaign_goal": "attract early users",
                "platform": "LinkedIn",
                "tone": "professional",
                "offer_or_cta": "Request demo",
                "key_message": "AI workers automate business tasks",
                "mention_self_as_worker": True,
            },
            "trigger_source": "internal_stack_test",
        },
        headers=auth_headers,
    )
    assert run_res.status_code == 200
    run_payload = run_res.json()
    assert run_payload["success"] is True
    run_id = run_payload["run_id"]

    run_get_res = client.get(f"/worker-runs/{run_id}", headers=auth_headers)
    assert run_get_res.status_code == 200
    run_body = run_get_res.json()
    assert run_body["status"] in {
        WorkerRunStatus.QUEUED.value,
        WorkerRunStatus.RUNNING.value,
        WorkerRunStatus.COMPLETED.value,
    }

    with SessionLocal() as db:
        run = db.get(WorkerRun, uuid.UUID(run_id))
        assert run is not None
        assert run.status != WorkerRunStatus.FAILED.value
        if run.status == WorkerRunStatus.COMPLETED.value:
            runtime_echo = (((run.output_json or {}).get("output") or {}).get("runtime_echo") or {})
            assert runtime_echo.get("mention_self_as_worker") is True
