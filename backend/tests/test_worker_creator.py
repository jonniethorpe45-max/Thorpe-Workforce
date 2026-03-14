from app.core.config import settings


def _signup_user(client, *, email: str, company: str):
    payload = {
        "full_name": "Creator User",
        "email": email,
        "password": "Passw0rd!",
        "company_name": company,
        "website": f"https://{company.lower().replace(' ', '')}.example",
        "industry": "SaaS",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_draft(client, auth_headers, *, name: str, slug: str):
    response = client.post(
        "/workers/builder/drafts",
        headers=auth_headers,
        json={
            "name": name,
            "slug": slug,
            "description": "Draft used for worker creator tests and publish/install validation.",
            "category": "custom",
            "prompt_template": "You are an AI worker. Generate concise structured JSON outputs for the mission.",
            "input_schema": {"type": "object", "properties": {"goal": {"type": "string"}}},
            "output_schema": {"type": "object", "properties": {"summary": {"type": "string"}}},
            "tools": [{"label": "web_search", "enabled": True}],
        },
    )
    assert response.status_code == 200
    return response.json()["draft"]


def test_worker_creator_draft_crud_happy_path(client, auth_headers):
    created = _create_draft(client, auth_headers, name="Local Draft", slug="local-draft")
    draft_id = created["id"]

    list_response = client.get("/workers/builder/drafts", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    patch_response = client.patch(
        f"/workers/builder/drafts/{draft_id}",
        headers=auth_headers,
        json={
            "description": "Updated draft description with meaningful publish details.",
            "visibility": "workspace",
            "price_monthly": 49.0,
            "creator_revenue_percent": 70.0,
            "platform_revenue_percent": 30.0,
        },
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["visibility"] == "workspace"
    assert float(patched["price_monthly"]) == 49.0


def test_worker_creator_draft_workspace_isolation(client, auth_headers):
    created = _create_draft(client, auth_headers, name="Owner Draft", slug="owner-draft")
    other_headers = _signup_user(client, email="other-worker-creator@example.com", company="Other Worker Creator")

    get_response = client.get(f"/workers/builder/drafts/{created['id']}", headers=other_headers)
    assert get_response.status_code in {403, 404}

    patch_response = client.patch(
        f"/workers/builder/drafts/{created['id']}",
        headers=other_headers,
        json={"description": "Attempted cross-workspace edit"},
    )
    assert patch_response.status_code in {403, 404}


def test_worker_creator_test_publish_install_flow(client, auth_headers):
    draft = _create_draft(client, auth_headers, name="Flow Draft", slug="flow-draft")
    draft_id = draft["id"]

    test_response = client.post(
        f"/workers/builder/drafts/{draft_id}/test",
        headers=auth_headers,
        json={"inputs": {"goal": "Generate one personalized outreach idea"}},
    )
    assert test_response.status_code == 200
    tested = test_response.json()
    assert tested["run_id"]
    assert tested["status"] in {"completed", "failed"}

    publish_response = client.post(f"/workers/builder/drafts/{draft_id}/publish", headers=auth_headers, json={})
    assert publish_response.status_code == 200
    published = publish_response.json()
    assert published["is_published"] is True
    assert published["published_template_id"]

    install_response = client.post(
        f"/workers/builder/drafts/{draft_id}/install",
        headers=auth_headers,
        json={"instance_name": "Flow Draft Instance", "runtime_config_overrides": {}, "memory_scope": "instance"},
    )
    assert install_response.status_code == 200
    installed = install_response.json()
    assert installed["name"] == "Flow Draft Instance"
    assert installed["status"] == "active"

    unpublish_response = client.post(f"/workers/builder/drafts/{draft_id}/unpublish", headers=auth_headers, json={})
    assert unpublish_response.status_code == 200
    assert unpublish_response.json()["is_published"] is False


def test_worker_creator_categories_contract(client, auth_headers):
    response = client.get("/workers/builder/categories", headers=auth_headers)
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert "custom" in keys
    assert "sales" in keys
    assert "real_estate" in keys


def test_worker_creator_feature_flag_off_returns_404(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "worker_creator_enabled", False)
    response = client.get("/workers/builder/drafts", headers=auth_headers)
    assert response.status_code == 404
