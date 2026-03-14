def _build_template_payload(slug: str, *, pricing_type: str = "free", price_cents: int = 0):
    return {
        "name": f"Marketplace {slug}",
        "slug": slug,
        "short_description": "Marketplace template",
        "description": "Template used to verify marketplace backend workflows.",
        "category": "sales",
        "worker_type": "custom_worker",
        "worker_category": "go_to_market",
        "visibility": "workspace",
        "status": "draft",
        "instructions": "Produce structured output for marketplace workflow tests.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "marketplace-test"},
        "capabilities_json": {"marketplace": True},
        "actions_json": ["monitor_outbound_events"],
        "tools_json": ["internal_note_writer"],
        "memory_enabled": True,
        "chain_enabled": False,
        "is_marketplace_listed": False,
        "pricing_type": pricing_type,
        "price_cents": price_cents,
        "currency": "USD",
        "tags_json": ["sales", "automation"],
    }


def _build_publish_payload(name: str, slug: str, *, pricing_type: str = "free", price_cents: int = 0):
    return {
        "name": name,
        "slug": slug,
        "description": "This marketplace template is publish-ready with full fields and practical configuration.",
        "instructions": "Run safely, use configured tools only, and return structured run outputs for user review.",
        "model_name": "mock-ai-v1",
        "config_json": {"mission": "marketplace-test", "published": True},
        "visibility": "marketplace",
        "is_marketplace_listed": True,
        "pricing_type": pricing_type,
        "price_cents": price_cents,
        "currency": "USD",
    }


def test_marketplace_publish_install_reviews_and_revenue(client, auth_headers):
    create_res = client.post(
        "/workers/templates",
        json=_build_template_payload("marketplace-flow-template", pricing_type="free", price_cents=0),
        headers=auth_headers,
    )
    assert create_res.status_code == 200
    template = create_res.json()

    publish_res = client.post(
        f"/marketplace/templates/{template['id']}/publish",
        json=_build_publish_payload(
            name=template["name"],
            slug=template["slug"],
            pricing_type="free",
            price_cents=0,
        ),
        headers=auth_headers,
    )
    assert publish_res.status_code == 200
    assert publish_res.json()["template"]["is_marketplace_listed"] is True

    list_res = client.get(
        "/marketplace/templates?category=sales&tag=automation&pricing_type=free&min_price_cents=0&max_price_cents=5000",
        headers=auth_headers,
    )
    assert list_res.status_code == 200
    assert any(item["template"]["id"] == template["id"] for item in list_res.json())

    by_id_res = client.get(f"/marketplace/templates/{template['id']}", headers=auth_headers)
    assert by_id_res.status_code == 200
    assert by_id_res.json()["template"]["id"] == template["id"]

    by_slug_res = client.get(f"/marketplace/templates/slug/{template['slug']}", headers=auth_headers)
    assert by_slug_res.status_code == 200
    assert by_slug_res.json()["template"]["slug"] == template["slug"]

    install_res = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={"instance_name": "Installed Marketplace Worker"},
        headers=auth_headers,
    )
    assert install_res.status_code == 200
    assert install_res.json()["subscription"]["billing_status"] == "active"

    review_res = client.post(
        f"/marketplace/templates/{template['id']}/reviews",
        json={"rating": 5, "review_text": "Great worker."},
        headers=auth_headers,
    )
    assert review_res.status_code == 200

    review_update_res = client.post(
        f"/marketplace/templates/{template['id']}/reviews",
        json={"rating": 4, "review_text": "Updated score."},
        headers=auth_headers,
    )
    assert review_update_res.status_code == 200

    reviews_res = client.get(f"/marketplace/templates/{template['id']}/reviews", headers=auth_headers)
    assert reviews_res.status_code == 200
    assert len(reviews_res.json()) == 1
    assert reviews_res.json()[0]["rating"] == 4

    detail_after_review = client.get(f"/marketplace/templates/{template['id']}", headers=auth_headers)
    assert detail_after_review.status_code == 200
    assert detail_after_review.json()["average_rating"] == 4.0
    assert detail_after_review.json()["template"]["rating_count"] == 1

    revenue_res = client.get("/marketplace/creator/revenue", headers=auth_headers)
    assert revenue_res.status_code == 200
    revenue = revenue_res.json()
    assert revenue["total_gross_cents"] >= 0
    assert revenue["total_platform_fee_cents"] >= 0
    assert revenue["total_creator_payout_cents"] >= 0
    assert len(revenue["recent_events"]) >= 1
    assert any(event["revenue_type"] == "free_install" for event in revenue["recent_events"])
