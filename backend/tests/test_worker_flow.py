def test_campaign_launch_creates_worker_run_and_unsubscribe_suppresses_lead(client, auth_headers):
    worker = client.post(
        "/workers",
        json={
            "name": "AI Sales Worker",
            "goal": "Book meetings from qualified leads",
            "target_industry": "SaaS",
            "target_roles": ["VP Sales"],
            "target_locations": ["US"],
            "company_size_range": "50-500",
            "tone": "professional",
            "daily_send_limit": 20,
            "run_interval_minutes": 60,
        },
        headers=auth_headers,
    ).json()
    campaign = client.post(
        "/campaigns",
        json={
            "worker_id": worker["id"],
            "name": "Outbound Mission",
            "target_industry": "SaaS",
            "target_roles": ["VP Sales"],
            "target_locations": ["US"],
            "cta_text": "Open to a short intro next week?",
            "scheduling_settings": {},
        },
        headers=auth_headers,
    ).json()
    lead = client.post(
        "/leads",
        json={
            "campaign_id": campaign["id"],
            "company_name": "Acme",
            "full_name": "Pat Jordan",
            "title": "VP Sales",
            "email": "pat@acme.com",
        },
        headers=auth_headers,
    )
    assert lead.status_code == 200

    launch_first = client.post(f"/campaigns/{campaign['id']}/launch", headers=auth_headers)
    assert launch_first.status_code == 200
    assert launch_first.json()["success"] is True
    assert launch_first.json().get("run_id")

    runs = client.get(f"/workers/{worker['id']}/runs", headers=auth_headers)
    assert runs.status_code == 200
    assert len(runs.json()) >= 1

    messages = client.get(f"/campaigns/{campaign['id']}/messages", headers=auth_headers).json()
    assert len(messages) >= 1
    approve = client.post(f"/messages/{messages[0]['id']}/approve", headers=auth_headers)
    assert approve.status_code == 200

    launch_second = client.post(f"/campaigns/{campaign['id']}/launch", headers=auth_headers)
    assert launch_second.status_code == 200
    assert launch_second.json()["success"] is True

    unsubscribe = client.post("/webhooks/email/unsubscribe", json={"email": "pat@acme.com"})
    assert unsubscribe.status_code == 200

    leads = client.get("/leads", headers=auth_headers).json()
    assert leads[0]["lead_status"] == "do_not_contact"
