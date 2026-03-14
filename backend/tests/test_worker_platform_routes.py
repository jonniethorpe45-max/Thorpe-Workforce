def test_worker_platform_routes_end_to_end(client, auth_headers):
    template_payload = {
        "name": "Platform Route Template",
        "slug": "platform-route-template",
        "short_description": "Route test template",
        "description": "Template created to validate worker platform route wiring.",
        "category": "ops",
        "worker_type": "custom_worker",
        "worker_category": "ops",
        "visibility": "workspace",
        "status": "draft",
        "instructions": "Execute route integration tasks and report structured output.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "validate_routes"},
        "capabilities_json": {"route_testing": True},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": False,
        "is_marketplace_listed": False,
        "pricing_type": "free",
        "price_cents": 0,
        "currency": "USD",
        "tags_json": ["test"],
    }
    create_template_res = client.post("/workers/templates", json=template_payload, headers=auth_headers)
    assert create_template_res.status_code == 200
    template = create_template_res.json()

    list_templates_res = client.get("/workers/templates", headers=auth_headers)
    assert list_templates_res.status_code == 200
    assert any(item["id"] == template["id"] for item in list_templates_res.json())

    get_template_res = client.get(f"/workers/templates/{template['id']}", headers=auth_headers)
    assert get_template_res.status_code == 200

    patch_template_res = client.patch(
        f"/workers/templates/{template['id']}",
        json={"short_description": "Updated route template"},
        headers=auth_headers,
    )
    assert patch_template_res.status_code == 200
    assert patch_template_res.json()["short_description"] == "Updated route template"

    publish_res = client.post(
        f"/workers/templates/{template['id']}/publish",
        json={
            "name": "Platform Route Template",
            "slug": "platform-route-template",
            "description": "This is a fully configured public marketplace template for route integration testing.",
            "instructions": "Run with controlled tools and return structured output with status updates.",
            "model_name": "mock-ai-v1",
            "config_json": {"mission": "validate_routes", "mode": "publish"},
            "visibility": "marketplace",
            "is_marketplace_listed": True,
            "pricing_type": "free",
            "price_cents": 0,
            "currency": "USD",
        },
        headers=auth_headers,
    )
    assert publish_res.status_code == 200
    assert publish_res.json()["is_marketplace_listed"] is True

    install_res = client.post(
        f"/workers/templates/{template['id']}/install",
        json={"instance_name": "Route Template Instance"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    instance = install_res.json()

    duplicate_res = client.post(
        f"/workers/templates/{template['id']}/duplicate",
        json={"name": "Platform Route Template Copy"},
        headers=auth_headers,
    )
    assert duplicate_res.status_code == 200
    assert duplicate_res.json()["id"] != template["id"]

    list_instances_res = client.get("/workers/instances", headers=auth_headers)
    assert list_instances_res.status_code == 200
    assert any(item["id"] == instance["id"] for item in list_instances_res.json())

    get_instance_res = client.get(f"/workers/instances/{instance['id']}", headers=auth_headers)
    assert get_instance_res.status_code == 200

    patch_instance_res = client.patch(
        f"/workers/instances/{instance['id']}",
        json={"runtime_config_json": {"priority": "high"}},
        headers=auth_headers,
    )
    assert patch_instance_res.status_code == 200
    assert patch_instance_res.json()["runtime_config_json"]["priority"] == "high"

    pause_instance_res = client.post(f"/workers/instances/{instance['id']}/pause", headers=auth_headers)
    assert pause_instance_res.status_code == 200
    assert pause_instance_res.json()["status"] == "paused"

    resume_instance_res = client.post(f"/workers/instances/{instance['id']}/resume", headers=auth_headers)
    assert resume_instance_res.status_code == 200
    assert resume_instance_res.json()["status"] == "active"

    run_instance_res = client.post(
        f"/workers/instances/{instance['id']}/run",
        json={"runtime_input": {"source": "test_worker_platform_routes"}},
        headers=auth_headers,
    )
    assert run_instance_res.status_code == 200
    run_id = run_instance_res.json()["run_id"]

    runs_res = client.get("/worker-runs", headers=auth_headers)
    assert runs_res.status_code == 200
    assert runs_res.json()["total"] >= 1

    run_detail_res = client.get(f"/worker-runs/{run_id}", headers=auth_headers)
    assert run_detail_res.status_code == 200
    assert run_detail_res.json()["id"] == run_id

    tools_res = client.get("/worker-tools", headers=auth_headers)
    assert tools_res.status_code == 200
    assert tools_res.json()["total"] >= 7

    tool_detail_res = client.get("/worker-tools/internal_note_writer", headers=auth_headers)
    assert tool_detail_res.status_code == 200
    assert tool_detail_res.json()["slug"] == "internal_note_writer"

    chain_create_res = client.post(
        "/worker-chains",
        json={
            "name": "Route Test Chain",
            "description": "Chain route test",
            "status": "draft",
            "trigger_type": "manual",
            "trigger_config_json": {},
            "steps": [
                {
                    "step_order": 1,
                    "worker_instance_id": instance["id"],
                    "step_name": "Run installed worker",
                    "input_mapping_json": {},
                }
            ],
        },
        headers=auth_headers,
    )
    assert chain_create_res.status_code == 200
    chain = chain_create_res.json()
    assert len(chain["steps"]) == 1

    chain_list_res = client.get("/worker-chains", headers=auth_headers)
    assert chain_list_res.status_code == 200
    assert chain_list_res.json()["total"] >= 1

    chain_get_res = client.get(f"/worker-chains/{chain['id']}", headers=auth_headers)
    assert chain_get_res.status_code == 200

    chain_patch_res = client.patch(
        f"/worker-chains/{chain['id']}",
        json={"description": "Updated description"},
        headers=auth_headers,
    )
    assert chain_patch_res.status_code == 200
    assert chain_patch_res.json()["description"] == "Updated description"

    marketplace_list_res = client.get("/marketplace/templates", headers=auth_headers)
    assert marketplace_list_res.status_code == 200
    assert any(item["template"]["id"] == template["id"] for item in marketplace_list_res.json())

    marketplace_install_res = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={"instance_name": "Marketplace Install Instance"},
        headers=auth_headers,
    )
    assert marketplace_install_res.status_code == 200
    assert marketplace_install_res.json()["worker_template_id"] == template["id"]

    public_list_res = client.get("/public-workers")
    assert public_list_res.status_code == 200
    assert any(item["slug"] == "platform-route-template" for item in public_list_res.json())

    public_detail_res = client.get("/public-workers/platform-route-template")
    assert public_detail_res.status_code == 200
    assert public_detail_res.json()["template"]["id"] == template["id"]
