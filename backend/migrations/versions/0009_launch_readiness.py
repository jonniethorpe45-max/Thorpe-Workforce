"""launch readiness models and featured workers

Revision ID: 0009_launch_readiness
Revises: 0008_analytics_ops
Create Date: 2026-03-15 06:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0009_launch_readiness"
down_revision = "0008_analytics_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "worker_templates",
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "worker_templates",
        sa.Column("featured_rank", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_worker_templates_featured_rank",
        "worker_templates",
        ["is_featured", "featured_rank"],
        unique=False,
    )

    op.create_table(
        "user_onboarding_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("current_step", sa.String(length=80), nullable=False, server_default="welcome"),
        sa.Column("goal_category", sa.String(length=40), nullable=True),
        sa.Column("selected_paths_json", sa.JSON(), nullable=True),
        sa.Column("recommended_template_slugs", sa.JSON(), nullable=True),
        sa.Column("completed_steps_json", sa.JSON(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_skipped", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", name="uq_user_onboarding_states_user_id"),
    )
    op.create_index(
        "ix_user_onboarding_states_workspace",
        "user_onboarding_states",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_onboarding_states_status",
        "user_onboarding_states",
        ["is_completed", "is_skipped"],
        unique=False,
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_tokens_expires_at",
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "support_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("handled_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="contact_form"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_support_requests_status_created",
        "support_requests",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_support_requests_email",
        "support_requests",
        ["email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_requests_email", table_name="support_requests")
    op.drop_index("ix_support_requests_status_created", table_name="support_requests")
    op.drop_table("support_requests")

    op.drop_index("ix_password_reset_tokens_expires_at", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_user_onboarding_states_status", table_name="user_onboarding_states")
    op.drop_index("ix_user_onboarding_states_workspace", table_name="user_onboarding_states")
    op.drop_table("user_onboarding_states")

    op.drop_index("ix_worker_templates_featured_rank", table_name="worker_templates")
    op.drop_column("worker_templates", "featured_rank")
    op.drop_column("worker_templates", "is_featured")
