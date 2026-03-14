import pytest
from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models import (
    User,
    WorkerPricingType,
    WorkerTemplateStatus,
    WorkerTemplateVisibility,
    Workspace,
)
from app.schemas.api import WorkerTemplateCreate, WorkerTemplatePublishRequest, WorkerTemplateUpdate
from app.services.worker_templates import (
    create_worker_template,
    duplicate_worker_template,
    get_worker_template_details,
    install_worker_template,
    list_worker_templates,
    publish_worker_template,
    unpublish_worker_template,
    update_worker_template,
    validate_template_publish_readiness,
)


def _create_workspace_user(db, *, email: str) -> tuple[Workspace, User]:
    workspace = Workspace(company_name=f"Company-{email}")
    db.add(workspace)
    db.flush()
    user = User(
        workspace_id=workspace.id,
        full_name="Template Owner",
        email=email,
        password_hash="test",
        role="owner",
    )
    db.add(user)
    db.flush()
    return workspace, user


def test_template_publish_and_install_flow():
    db = SessionLocal()
    try:
        owner_workspace, owner_user = _create_workspace_user(db, email="owner@test.com")
        buyer_workspace, buyer_user = _create_workspace_user(db, email="buyer@test.com")

        template = create_worker_template(
            db,
            workspace_id=owner_workspace.id,
            creator_user_id=owner_user.id,
            payload=WorkerTemplateCreate(
                name="Outbound SDR Template",
                slug="outbound-sdr-template",
                short_description="Template for outbound SDR activity",
                description="A practical outbound template.",
                category="sales",
                worker_type="custom_worker",
                worker_category="go_to_market",
                visibility=WorkerTemplateVisibility.WORKSPACE,
                status=WorkerTemplateStatus.DRAFT,
                instructions="Draft outreach emails and monitor responses.",
                model_name="gpt-4o-mini",
                config_json={"step": "draft"},
                capabilities_json={"supports": ["email"]},
                actions_json=["select_eligible_leads", "generate_messages_for_selected_leads"],
                tools_json=[],
                memory_enabled=True,
                chain_enabled=False,
                is_marketplace_listed=False,
                pricing_type=WorkerPricingType.FREE,
                price_cents=0,
                currency="USD",
                tags_json=["sales"],
            ),
        )

        readiness = validate_template_publish_readiness(
            db,
            template=template,
            workspace_id=owner_workspace.id,
        )
        assert readiness.is_ready is True

        published = publish_worker_template(
            db,
            template=template,
            workspace_id=owner_workspace.id,
            payload=WorkerTemplatePublishRequest(
                name="Outbound SDR Template",
                slug="outbound-sdr-template",
                description="A detailed outbound sales template designed for high quality personalized outreach.",
                instructions="Research accounts, draft concise personalized messages, then update outcomes after sends.",
                model_name="gpt-4o-mini",
                config_json={"step": "draft", "persona": "sdr"},
                visibility=WorkerTemplateVisibility.MARKETPLACE,
                is_marketplace_listed=True,
                pricing_type=WorkerPricingType.SUBSCRIPTION,
                price_cents=1900,
                currency="USD",
            ),
        )
        assert published.status == WorkerTemplateStatus.ACTIVE.value
        assert published.is_public is True
        assert published.is_marketplace_listed is True

        public_templates = list_worker_templates(
            db,
            workspace_id=buyer_workspace.id,
            include_workspace_templates=False,
            include_public_templates=True,
        )
        assert any(item.id == template.id for item in public_templates)

        fetched = get_worker_template_details(
            db,
            slug="outbound-sdr-template",
            workspace_id=buyer_workspace.id,
            include_public=True,
        )
        assert fetched.id == template.id

        install_result = install_worker_template(
            db,
            template=template,
            workspace_id=buyer_workspace.id,
            installer_user_id=buyer_user.id,
            instance_name="Buyer Installed Worker",
            runtime_config_overrides={"region": "NA"},
        )
        assert install_result.instance.workspace_id == buyer_workspace.id
        assert install_result.instance.template_id == template.id
        assert install_result.subscription is not None
        assert install_result.install_count_incremented is True
        assert template.install_count == 1

        unpublish_worker_template(
            db,
            template=template,
            workspace_id=owner_workspace.id,
        )
        with pytest.raises(HTTPException):
            get_worker_template_details(
                db,
                slug="outbound-sdr-template",
                workspace_id=buyer_workspace.id,
                include_public=True,
            )
    finally:
        db.close()


def test_template_duplicate_slug_and_private_visibility_guards():
    db = SessionLocal()
    try:
        workspace, user = _create_workspace_user(db, email="owner-2@test.com")
        other_workspace, _ = _create_workspace_user(db, email="other@test.com")

        template = create_worker_template(
            db,
            workspace_id=workspace.id,
            creator_user_id=user.id,
            payload=WorkerTemplateCreate(
                name="Private Worker",
                slug="private-worker",
                short_description=None,
                description=None,
                category="sales",
                worker_type="custom_worker",
                worker_category="go_to_market",
                visibility=WorkerTemplateVisibility.WORKSPACE,
                status=WorkerTemplateStatus.DRAFT,
                instructions=None,
                model_name=None,
                config_json={"a": 1},
                capabilities_json={},
                actions_json=["select_eligible_leads"],
                tools_json=[],
                memory_enabled=True,
                chain_enabled=False,
                is_marketplace_listed=False,
                pricing_type=WorkerPricingType.INTERNAL,
                price_cents=0,
                currency="USD",
                tags_json=[],
            ),
        )
        copied = duplicate_worker_template(
            db,
            source_template=template,
            workspace_id=workspace.id,
            creator_user_id=user.id,
            name="Private Worker Copy",
        )
        assert copied.id != template.id
        assert copied.workspace_id == workspace.id

        with pytest.raises(HTTPException):
            update_worker_template(
                db,
                template=template,
                workspace_id=workspace.id,
                payload=WorkerTemplateUpdate(slug=copied.slug),
            )

        external_list = list_worker_templates(
            db,
            workspace_id=other_workspace.id,
            include_workspace_templates=False,
            include_public_templates=True,
        )
        assert all(item.workspace_id != workspace.id for item in external_list)

        with pytest.raises(HTTPException):
            get_worker_template_details(
                db,
                template_id=template.id,
                workspace_id=other_workspace.id,
                include_public=True,
            )
    finally:
        db.close()
