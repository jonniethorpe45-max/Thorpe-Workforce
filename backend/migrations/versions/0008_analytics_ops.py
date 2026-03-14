"""analytics and platform operations foundation

Revision ID: 0008_analytics_ops
Revises: 0007_billing_core
Create Date: 2026-03-15 02:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0008_analytics_ops"
down_revision = "0007_billing_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "worker_templates",
        sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="approved"),
    )
    op.add_column("worker_templates", sa.Column("moderation_notes", sa.Text(), nullable=True))
    op.add_column("worker_templates", sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("worker_templates", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "worker_templates",
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_worker_templates_reviewed_by_user_id_users",
        "worker_templates",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_worker_templates_moderation_status",
        "worker_templates",
        ["moderation_status"],
        unique=False,
    )

    op.create_table(
        "worker_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("reporter_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index(
        "ix_worker_reports_template_status",
        "worker_reports",
        ["worker_template_id", "status"],
        unique=False,
    )
    op.create_index("ix_worker_reports_created_at", "worker_reports", ["created_at"], unique=False)

    op.create_table(
        "worker_analytics_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uninstall_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_running_workspaces", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_running_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("test_run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("publish_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("installs_from_marketplace", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("installs_from_public_page", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paid_purchase_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_gross_revenue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_platform_revenue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_creator_revenue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("worker_template_id", "workspace_id", "date", name="uq_worker_analytics_daily_scope_date"),
    )
    op.create_index("ix_worker_analytics_daily_date", "worker_analytics_daily", ["date"], unique=False)
    op.create_index(
        "ix_worker_analytics_daily_worker_date",
        "worker_analytics_daily",
        ["worker_template_id", "date"],
        unique=False,
    )

    op.create_table(
        "workspace_usage_daily",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("worker_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chain_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("installed_workers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_workers_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("workspace_id", "date", name="uq_workspace_usage_daily_workspace_date"),
    )
    op.create_index(
        "ix_workspace_usage_daily_workspace_date",
        "workspace_usage_daily",
        ["workspace_id", "date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_usage_daily_workspace_date", table_name="workspace_usage_daily")
    op.drop_table("workspace_usage_daily")

    op.drop_index("ix_worker_analytics_daily_worker_date", table_name="worker_analytics_daily")
    op.drop_index("ix_worker_analytics_daily_date", table_name="worker_analytics_daily")
    op.drop_table("worker_analytics_daily")

    op.drop_index("ix_worker_reports_created_at", table_name="worker_reports")
    op.drop_index("ix_worker_reports_template_status", table_name="worker_reports")
    op.drop_table("worker_reports")

    op.drop_index("ix_worker_templates_moderation_status", table_name="worker_templates")
    op.drop_constraint("fk_worker_templates_reviewed_by_user_id_users", "worker_templates", type_="foreignkey")
    op.drop_column("worker_templates", "report_count")
    op.drop_column("worker_templates", "reviewed_at")
    op.drop_column("worker_templates", "reviewed_by_user_id")
    op.drop_column("worker_templates", "moderation_notes")
    op.drop_column("worker_templates", "moderation_status")
