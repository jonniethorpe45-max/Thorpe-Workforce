def _template_payload(slug: str, *, status: str = "active"):
    return {
        "name": f"Chain Template {slug}",
        "slug": slug,
        "short_description": "chain template",
        "description": "Template used for worker chain orchestration integration tests.",
        "category": "ops",
        "worker_type": "custom_worker",
        "worker_category": "ops",
        "visibility": "workspace",
        "status": status,
        "instructions": "Run chain orchestration test task and return structured output.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "chain"},
        "capabilities_json": {"chain": True},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": True,
        "is_marketplace_listed": False,
        "pricing_type": "free",
        "price_cents": 0,
        "currency": "USD",
        "tags_json": ["chain"],
    }


def test_worker_chain_manual_run_with_output_passing_and_failure_branch(client, auth_headers):
    active_template_res = client.post("/workers/templates", json=_template_payload("chain-active-template"), headers=auth_headers)
    assert active_template_res.status_code == 200
    active_template = active_template_res.json()

    active_install_res = client.post(
        f"/workers/templates/{active_template['id']}/install",
        json={"instance_name": "Chain Active Instance"},
        headers=auth_headers,
    )
    assert active_install_res.status_code == 200
    active_instance = active_install_res.json()

    archived_template_res = client.post(
        "/workers/templates",
        json=_template_payload("chain-archived-template", status="archived"),
        headers=auth_headers,
    )
    assert archived_template_res.status_code == 200
    archived_template = archived_template_res.json()
    assert archived_template["is_active"] is False

    create_chain_res = client.post(
        "/worker-chains",
        json={
            "name": "Manual Chain Run",
            "description": "Chain run test",
            "status": "draft",
            "trigger_type": "manual",
            "trigger_config_json": {},
            "steps": [
                {
                    "step_order": 1,
                    "worker_instance_id": active_instance["id"],
                    "step_name": "first",
                    "input_mapping_json": {"seed_copy": "$chain_input.seed"},
                    "on_success_next_step": 2,
                },
                {
                    "step_order": 2,
                    "worker_template_id": archived_template["id"],
                    "step_name": "failing-template-step",
                    "input_mapping_json": {},
                    "on_failure_next_step": 3,
                },
                {
                    "step_order": 3,
                    "worker_instance_id": active_instance["id"],
                    "step_name": "final",
                    "input_mapping_json": {
                        "from_previous_seed": "$step_outputs.1.output.runtime_echo.seed_copy",
                    },
                },
            ],
        },
        headers=auth_headers,
    )
    assert create_chain_res.status_code == 200
    chain = create_chain_res.json()

    run_chain_res = client.post(
        f"/worker-chains/{chain['id']}/run",
        json={"runtime_input": {"seed": "alpha"}},
        headers=auth_headers,
    )
    assert run_chain_res.status_code == 200
    payload = run_chain_res.json()

    assert payload["success"] is True
    assert payload["status"] == "completed"
    assert payload["total_steps_executed"] == 3
    assert [item["status"] for item in payload["executed_steps"]] == ["completed", "failed", "completed"]
    assert payload["executed_steps"][1]["run_id"] is None
    assert "inactive" in (payload["executed_steps"][1]["error"] or "").lower()

    final_step_run_id = payload["executed_steps"][2]["run_id"]
    assert final_step_run_id is not None
    run_detail_res = client.get(f"/worker-runs/{final_step_run_id}", headers=auth_headers)
    assert run_detail_res.status_code == 200
    run_detail = run_detail_res.json()
    assert run_detail["input_json"]["from_previous_seed"] == "alpha"
    assert run_detail["triggered_by"] == "chain"
