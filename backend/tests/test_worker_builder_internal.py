def test_internal_builder_creates_template_and_worker(client, auth_headers):
    actions_res = client.get("/workers/internal/builder/actions", headers=auth_headers)
    assert actions_res.status_code == 200
    action_keys = {item["key"] for item in actions_res.json()}
    assert "select_eligible_leads" in action_keys

    template_payload = {
        "display_name": "Custom SDR Worker",
        "worker_type": "custom_worker",
        "worker_category": "go_to_market",
        "plan_version": "custom_v1",
        "prompt_profile": "sales",
        "allowed_actions": [
            "select_eligible_leads",
            "research_selected_leads",
            "generate_messages_for_selected_leads",
            "dispatch_messages",
            "monitor_outbound_events",
            "record_optimization_signals",
        ],
        "steps": [
            {"key": "select", "action_key": "select_eligible_leads", "status": "prospecting"},
            {"key": "research", "action_key": "research_selected_leads", "status": "researching"},
            {"key": "draft", "action_key": "generate_messages_for_selected_leads", "status": "drafting"},
            {"key": "dispatch", "action_key": "dispatch_messages", "status": "sending"},
            {"key": "monitor", "action_key": "monitor_outbound_events", "status": "monitoring"},
            {"key": "optimize", "action_key": "record_optimization_signals", "status": "optimizing"},
        ],
        "config_defaults": {"target_industry": "SaaS"},
        "mission_default": "Book meetings from qualified leads",
    }
    template_res = client.post("/workers/internal/templates", json=template_payload, headers=auth_headers)
    assert template_res.status_code == 200
    template = template_res.json()
    assert template["worker_type"] == "custom_worker"
    assert template["is_public"] is False

    worker_res = client.post(
        "/workers/internal/workers/from-template",
        json={
            "template_id": template["id"],
            "name": "Custom Worker Alpha",
            "mission": "Drive qualified meetings this month",
            "tone": "professional",
            "daily_send_limit": 20,
            "run_interval_minutes": 60,
            "config_overrides": {"target_locations": ["US"]},
        },
        headers=auth_headers,
    )
    assert worker_res.status_code == 200
    worker = worker_res.json()
    assert worker["is_custom_worker"] is True
    assert worker["worker_type"] == "custom_worker"
    assert worker["template_id"] == template["id"]

    campaign_res = client.post(
        "/campaigns",
        json={
            "worker_id": worker["id"],
            "name": "Custom Worker Campaign",
            "target_industry": "SaaS",
            "target_roles": ["VP Sales"],
            "target_locations": ["US"],
            "cta_text": "Open to a short intro?",
            "scheduling_settings": {},
        },
        headers=auth_headers,
    )
    assert campaign_res.status_code == 200
    campaign = campaign_res.json()

    lead_res = client.post(
        "/leads",
        json={
            "campaign_id": campaign["id"],
            "company_name": "Atlas",
            "full_name": "Taylor Atlas",
            "title": "VP Sales",
            "email": "taylor@atlas.com",
        },
        headers=auth_headers,
    )
    assert lead_res.status_code == 200

    launch_res = client.post(f"/campaigns/{campaign['id']}/launch", headers=auth_headers)
    assert launch_res.status_code == 200
    assert launch_res.json()["success"] is True

    messages_res = client.get(f"/campaigns/{campaign['id']}/messages", headers=auth_headers)
    assert messages_res.status_code == 200
    assert len(messages_res.json()) > 0
