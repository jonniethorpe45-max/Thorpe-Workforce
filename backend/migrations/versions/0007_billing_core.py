"""billing core tables and entitlements

Revision ID: 0007_billing_core
Revises: 0006_worker_creator_drafts
Create Date: 2026-03-15 01:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_billing_core"
down_revision = "0006_worker_creator_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "creator_monetization_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=255), nullable=True),
        sa.Column("payouts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tax_profile_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", name="uq_creator_monetization_profiles_user_id"),
    )
    op.create_index(
        "ix_creator_monetization_profiles_payouts_enabled",
        "creator_monetization_profiles",
        ["payouts_enabled"],
        unique=False,
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("monthly_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("annual_price_cents", sa.Integer(), nullable=True),
        sa.Column("stripe_price_id_monthly", sa.String(length=255), nullable=True),
        sa.Column("stripe_price_id_annual", sa.String(length=255), nullable=True),
        sa.Column("max_worker_drafts", sa.Integer(), nullable=True),
        sa.Column("max_published_workers", sa.Integer(), nullable=True),
        sa.Column("max_worker_installs_per_workspace", sa.Integer(), nullable=True),
        sa.Column("max_worker_runs_per_month", sa.Integer(), nullable=True),
        sa.Column("allow_worker_builder", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_marketplace_publishing", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_private_workers", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_public_workers", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_marketplace_install", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_team_features", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
    )
    op.create_index("ix_subscription_plans_code_active", "subscription_plans", ["code", "is_active"], unique=False)

    op.create_table(
        "workspace_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("billing_interval", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_workspace_subscriptions_workspace_status",
        "workspace_subscriptions",
        ["workspace_id", "status"],
        unique=False,
    )
    op.create_index("ix_workspace_subscriptions_customer_id", "workspace_subscriptions", ["stripe_customer_id"], unique=False)
    op.create_index(
        "ix_workspace_subscriptions_subscription_id",
        "workspace_subscriptions",
        ["stripe_subscription_id"],
        unique=False,
    )

    op.create_table(
        "billing_event_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("stripe_event_id", name="uq_billing_event_logs_stripe_event_id"),
    )
    op.create_index("ix_billing_event_logs_event_type", "billing_event_logs", ["event_type"], unique=False)

    op.add_column(
        "worker_subscriptions",
        sa.Column("access_type", sa.String(length=30), nullable=False, server_default="free"),
    )
    op.add_column(
        "worker_subscriptions",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
    )
    op.add_column("worker_subscriptions", sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True))
    op.add_column("worker_subscriptions", sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True))
    op.add_column("worker_subscriptions", sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True))
    op.add_column(
        "worker_subscriptions",
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column("worker_subscriptions", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_worker_subscriptions_status", "worker_subscriptions", ["status"], unique=False)
    op.create_index(
        "ix_worker_subscriptions_checkout_session",
        "worker_subscriptions",
        ["stripe_checkout_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_worker_subscriptions_stripe_subscription",
        "worker_subscriptions",
        ["stripe_subscription_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_worker_subscriptions_stripe_subscription", table_name="worker_subscriptions")
    op.drop_index("ix_worker_subscriptions_checkout_session", table_name="worker_subscriptions")
    op.drop_index("ix_worker_subscriptions_status", table_name="worker_subscriptions")
    op.drop_column("worker_subscriptions", "expires_at")
    op.drop_column("worker_subscriptions", "granted_at")
    op.drop_column("worker_subscriptions", "stripe_subscription_id")
    op.drop_column("worker_subscriptions", "stripe_payment_intent_id")
    op.drop_column("worker_subscriptions", "stripe_checkout_session_id")
    op.drop_column("worker_subscriptions", "status")
    op.drop_column("worker_subscriptions", "access_type")

    op.drop_index("ix_billing_event_logs_event_type", table_name="billing_event_logs")
    op.drop_table("billing_event_logs")

    op.drop_index("ix_workspace_subscriptions_subscription_id", table_name="workspace_subscriptions")
    op.drop_index("ix_workspace_subscriptions_customer_id", table_name="workspace_subscriptions")
    op.drop_index("ix_workspace_subscriptions_workspace_status", table_name="workspace_subscriptions")
    op.drop_table("workspace_subscriptions")

    op.drop_index("ix_subscription_plans_code_active", table_name="subscription_plans")
    op.drop_table("subscription_plans")

    op.drop_index("ix_creator_monetization_profiles_payouts_enabled", table_name="creator_monetization_profiles")
    op.drop_table("creator_monetization_profiles")
