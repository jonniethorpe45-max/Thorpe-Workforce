def test_create_worker(client, auth_headers):
    payload = {
        "name": "Sales Worker A",
        "goal": "Book meetings",
        "worker_type": "ai_sales_worker",
        "target_industry": "SaaS",
        "target_roles": ["VP Sales"],
        "target_locations": ["US"],
        "company_size_range": "50-500",
        "tone": "professional",
        "daily_send_limit": 30,
    }
    res = client.post("/workers", json=payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == payload["name"]
    assert res.json()["worker_type"] == "ai_sales_worker"
    assert res.json()["plan_version"] == "sales_v1"
    assert res.json()["worker_category"] == "go_to_market"
    assert "select_eligible_leads" in (res.json()["allowed_actions"] or [])


def test_worker_templates_library(client, auth_headers):
    res = client.get("/workers/templates/library", headers=auth_headers)
    assert res.status_code == 200
    templates = res.json()
    assert any(item["worker_type"] == "ai_sales_worker" for item in templates)


def test_create_campaign(client, auth_headers):
    worker = client.post(
        "/workers",
        json={
            "name": "Sales Worker B",
            "goal": "Pipeline growth",
            "target_industry": "FinTech",
            "target_roles": ["Head of Growth"],
            "target_locations": ["US"],
            "company_size_range": "25-250",
            "tone": "concise",
            "daily_send_limit": 20,
        },
        headers=auth_headers,
    ).json()
    campaign_payload = {
        "worker_id": worker["id"],
        "name": "FinTech Outbound",
        "ideal_customer_profile": "Series B fintech",
        "target_industry": "FinTech",
        "target_roles": ["Head of Growth"],
        "target_locations": ["US"],
        "company_size_min": 25,
        "company_size_max": 250,
        "cta_text": "Open to a short call next week?",
        "exclusions": ["Crypto exchanges"],
        "scheduling_settings": {"step_2_delay_days": 2},
    }
    res = client.post("/campaigns", json=campaign_payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == campaign_payload["name"]
