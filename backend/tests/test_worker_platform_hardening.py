def _signup_user(client, *, email: str, company: str):
    signup_payload = {
        "full_name": "Workspace User",
        "email": email,
        "password": "Passw0rd!",
        "company_name": company,
        "website": f"https://{company.lower().replace(' ', '')}.example",
        "industry": "SaaS",
    }
    response = client.post("/auth/signup", json=signup_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_template(client, auth_headers, *, slug: str, status: str = "draft", visibility: str = "workspace"):
    payload = {
        "name": f"Hardening Template {slug}",
        "slug": slug,
        "short_description": "Hardening template",
        "description": "Template created for AI Workforce OS hardening tests.",
        "category": "ops",
        "worker_type": "custom_worker",
        "worker_category": "ops",
        "visibility": visibility,
        "status": status,
        "instructions": "Execute configured worker tasks and return structured output.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "hardening"},
        "capabilities_json": {"validation": True},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": True,
        "is_marketplace_listed": False,
        "pricing_type": "free",
        "price_cents": 0,
        "currency": "USD",
        "tags_json": ["hardening"],
    }
    response = client.post("/workers/templates", json=payload, headers=auth_headers)
    assert response.status_code == 200
    return response.json()


def test_publish_validation_rejects_invalid_marketplace_pricing(client, auth_headers):
    template = _create_template(client, auth_headers, slug="hardening-publish-pricing")
    publish_res = client.post(
        f"/workers/templates/{template['id']}/publish",
        json={
            "name": template["name"],
            "slug": template["slug"],
            "description": "Publish validation checks should prevent invalid paid pricing for marketplace templates.",
            "instructions": "Run with robust guardrails and valid publishing rules.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "publish"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "subscription",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 422


def test_worker_install_and_run_workspace_scoping_protection(client, auth_headers):
    other_headers = _signup_user(client, email="other-scope@example.com", company="Other Scope Co")
    template = _create_template(client, auth_headers, slug="hardening-workspace-install", status="active")

    cross_install = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Unauthorized Install"},
        headers=other_headers,
    )
    assert cross_install.status_code in {403, 404}

    install_res = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Authorized Install"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance_id = install_res.json()["id"]

    run_res = client.post(
        f"/workers/instances/{instance_id}/run",
        json={"runtime_input": {"source": "workspace_scope_test"}},
        headers=auth_headers,
    )
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]

    run_detail_cross_workspace = client.get(f"/worker-runs/{run_id}", headers=other_headers)
    assert run_detail_cross_workspace.status_code == 404


def test_marketplace_and_public_visibility_rules(client, auth_headers):
    hidden = _create_template(client, auth_headers, slug="hardening-hidden-template", status="active", visibility="workspace")

    marketplace_list = client.get("/marketplace/templates", headers=auth_headers)
    assert marketplace_list.status_code == 200
    assert all(item["template"]["id"] != hidden["id"] for item in marketplace_list.json())

    marketplace_detail = client.get(f"/marketplace/templates/{hidden['id']}", headers=auth_headers)
    assert marketplace_detail.status_code == 404

    public_list = client.get("/public-workers")
    assert public_list.status_code == 200
    assert all(item["id"] != hidden["id"] for item in public_list.json())


def test_review_rating_validation(client, auth_headers):
    template = _create_template(client, auth_headers, slug="hardening-review-validation")
    publish_res = client.post(
        f"/marketplace/templates/{template['id']}/publish",
        json={
            "name": template["name"],
            "slug": template["slug"],
            "description": "Review validation template for marketplace rating checks.",
            "instructions": "Return structured output and respect marketplace validation rules.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "reviews"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 200

    invalid_review = client.post(
        f"/marketplace/templates/{template['id']}/reviews",
        json={"rating": 6, "review_text": "Too high"},
        headers=auth_headers,
    )
    assert invalid_review.status_code == 422


def test_basic_chain_execution_happy_path(client, auth_headers):
    template = _create_template(client, auth_headers, slug="hardening-chain-happy", status="active")
    install_res = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Happy Chain Instance"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance = install_res.json()

    create_chain_res = client.post(
        "/worker-chains",
        json={
            "name": "Hardening Happy Chain",
            "description": "Happy path chain execution",
            "status": "draft",
            "trigger_type": "manual",
            "trigger_config_json": {},
            "steps": [
                {
                    "step_order": 1,
                    "worker_instance_id": instance["id"],
                    "step_name": "start",
                    "input_mapping_json": {"seed_copy": "$chain_input.seed"},
                    "on_success_next_step": 2,
                },
                {
                    "step_order": 2,
                    "worker_instance_id": instance["id"],
                    "step_name": "finish",
                    "input_mapping_json": {
                        "from_previous_seed": "$step_outputs.1.output.runtime_echo.seed_copy",
                    },
                },
            ],
        },
        headers=auth_headers,
    )
    assert create_chain_res.status_code == 200
    chain_id = create_chain_res.json()["id"]

    run_chain_res = client.post(
        f"/worker-chains/{chain_id}/run",
        json={"runtime_input": {"seed": "happy"}},
        headers=auth_headers,
    )
    assert run_chain_res.status_code == 200
    payload = run_chain_res.json()
    assert payload["success"] is True
    assert payload["status"] == "completed"
    assert [item["status"] for item in payload["executed_steps"]] == ["completed", "completed"]
    assert all(item["run_id"] for item in payload["executed_steps"])

    second_run_id = payload["executed_steps"][1]["run_id"]
    detail_res = client.get(f"/worker-runs/{second_run_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["input_json"]["from_previous_seed"] == "happy"


def test_startup_health_and_route_registration(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = set(openapi.json()["paths"].keys())
    required_paths = {
        "/workers/templates",
        "/workers/templates/{template_id}/publish",
        "/workers/instances/{instance_id}/run",
        "/worker-runs",
        "/worker-chains/{chain_id}/run",
        "/marketplace/templates",
        "/public-workers",
    }
    for path in required_paths:
        assert path in paths

    # Ensure route registration does not break legacy worker-instance endpoint used by existing clients.
    assert "/worker-instances/{instance_id}/execute" in paths
