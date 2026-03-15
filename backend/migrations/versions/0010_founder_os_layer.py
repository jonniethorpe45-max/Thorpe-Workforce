"""founder os automation and reports

Revision ID: 0010_founder_os_layer
Revises: 0009_launch_readiness
Create Date: 2026-03-16 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0010_founder_os_layer"
down_revision = "0009_launch_readiness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "founder_os_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_chains.id"), nullable=True),
        sa.Column("report_type", sa.String(length=50), nullable=False, server_default="daily_briefing"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("chain_run_id", sa.String(length=120), nullable=True),
        sa.Column("source_run_ids_json", sa.JSON(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_founder_os_reports_workspace_type_created",
        "founder_os_reports",
        ["workspace_id", "report_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_founder_os_reports_workspace_chain_created",
        "founder_os_reports",
        ["workspace_id", "chain_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "founder_os_automations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_chains.id"), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="weekly"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runtime_input_json", sa.JSON(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_founder_os_automations_workspace_enabled_next_run",
        "founder_os_automations",
        ["workspace_id", "is_enabled", "next_run_at"],
        unique=False,
    )
    op.create_index(
        "ix_founder_os_automations_workspace_chain",
        "founder_os_automations",
        ["workspace_id", "chain_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_founder_os_automations_workspace_chain", table_name="founder_os_automations")
    op.drop_index("ix_founder_os_automations_workspace_enabled_next_run", table_name="founder_os_automations")
    op.drop_table("founder_os_automations")

    op.drop_index("ix_founder_os_reports_workspace_chain_created", table_name="founder_os_reports")
    op.drop_index("ix_founder_os_reports_workspace_type_created", table_name="founder_os_reports")
    op.drop_table("founder_os_reports")
