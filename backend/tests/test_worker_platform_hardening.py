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


def test_publish_install_run_flow_happy_path(client, auth_headers):
    template = _create_template(client, auth_headers, slug="hardening-publish-install-run")
    publish_res = client.post(
        f"/workers/templates/{template['id']}/publish",
        json={
            "name": template["name"],
            "slug": template["slug"],
            "description": "Publish-install-run happy path template with complete required fields.",
            "instructions": "Run safely with configured tools and return structured output.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "happy_path"},
            "visibility": "public",
            "is_marketplace_listed": False,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 200
    assert publish_res.json()["status"] == "active"

    install_res = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Hardening Happy Instance"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance_id = install_res.json()["id"]

    run_res = client.post(
        f"/workers/instances/{instance_id}/run",
        json={"runtime_input": {"source": "publish_install_run"}},
        headers=auth_headers,
    )
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]

    run_detail = client.get(f"/worker-runs/{run_id}", headers=auth_headers)
    assert run_detail.status_code == 200
    assert run_detail.json()["status"] == "completed"
    assert run_detail.json()["summary"]


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


def test_workspace_isolation_for_chain_access(client, auth_headers):
    other_headers = _signup_user(client, email="other-chain@example.com", company="Other Chain Co")
    template = _create_template(client, auth_headers, slug="hardening-chain-isolation", status="active")
    install_res = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Isolation Chain Instance"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance_id = install_res.json()["id"]

    create_chain_res = client.post(
        "/worker-chains",
        json={
            "name": "Isolation Chain",
            "description": "Workspace isolation chain",
            "status": "draft",
            "trigger_type": "manual",
            "trigger_config_json": {},
            "steps": [
                {
                    "step_order": 1,
                    "worker_instance_id": instance_id,
                    "step_name": "single-step",
                    "input_mapping_json": {},
                }
            ],
        },
        headers=auth_headers,
    )
    assert create_chain_res.status_code == 200
    chain_id = create_chain_res.json()["id"]

    cross_get = client.get(f"/worker-chains/{chain_id}", headers=other_headers)
    assert cross_get.status_code == 404

    cross_patch = client.patch(
        f"/worker-chains/{chain_id}",
        json={"description": "unauthorized update"},
        headers=other_headers,
    )
    assert cross_patch.status_code == 404

    cross_run = client.post(
        f"/worker-chains/{chain_id}/run",
        json={"runtime_input": {"seed": "unauthorized"}},
        headers=other_headers,
    )
    assert cross_run.status_code == 404


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


def test_marketplace_and_public_endpoints_do_not_expose_private_template_fields(client, auth_headers):
    template = _create_template(client, auth_headers, slug="hardening-field-exposure")
    publish_res = client.post(
        f"/marketplace/templates/{template['id']}/publish",
        json={
            "name": template["name"],
            "slug": template["slug"],
            "description": "Template used to validate public and marketplace field exposure controls.",
            "instructions": "Return structured output and keep internal template settings private.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "field_exposure"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 200

    forbidden_template_fields = {
        "workspace_id",
        "creator_user_id",
        "default_config_json",
        "config_json",
        "capabilities_json",
        "allowed_actions",
        "actions_json",
        "tools_json",
        "prompt_profile",
        "is_system_template",
        "memory_enabled",
        "chain_enabled",
    }

    marketplace_detail = client.get(f"/marketplace/templates/{template['id']}", headers=auth_headers)
    assert marketplace_detail.status_code == 200
    marketplace_template = marketplace_detail.json()["template"]
    assert forbidden_template_fields.isdisjoint(set(marketplace_template.keys()))
    if marketplace_detail.json()["reviews"]:
        review = marketplace_detail.json()["reviews"][0]
        assert "user_id" not in review
        assert "workspace_id" not in review
    if marketplace_detail.json()["tools"]:
        tool = marketplace_detail.json()["tools"][0]
        assert "config_schema_json" not in tool
        assert "is_system" not in tool

    public_detail = client.get(f"/public-workers/{template['slug']}")
    assert public_detail.status_code == 200
    public_template = public_detail.json()["template"]
    assert forbidden_template_fields.isdisjoint(set(public_template.keys()))
    if public_detail.json()["reviews"]:
        review = public_detail.json()["reviews"][0]
        assert "user_id" not in review
        assert "workspace_id" not in review
    if public_detail.json()["tools"]:
        tool = public_detail.json()["tools"][0]
        assert "config_schema_json" not in tool
        assert "is_system" not in tool


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
