"""worker creator drafts and template metadata

Revision ID: 0006_worker_creator_drafts
Revises: 0005_workforce_os_core
Create Date: 2026-03-14 23:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0006_worker_creator_drafts"
down_revision = "0005_workforce_os_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("worker_templates", sa.Column("icon", sa.String(length=255), nullable=True))
    op.add_column("worker_templates", sa.Column("screenshots_json", sa.JSON(), nullable=True))
    op.add_column("worker_templates", sa.Column("usage_examples_json", sa.JSON(), nullable=True))
    op.add_column(
        "worker_templates",
        sa.Column("creator_revenue_percent", sa.Numeric(5, 2), nullable=False, server_default="70.00"),
    )
    op.add_column(
        "worker_templates",
        sa.Column("platform_revenue_percent", sa.Numeric(5, 2), nullable=False, server_default="30.00"),
    )
    op.create_check_constraint(
        "ck_worker_templates_creator_revenue_percent",
        "worker_templates",
        "creator_revenue_percent >= 0 AND creator_revenue_percent <= 100",
    )
    op.create_check_constraint(
        "ck_worker_templates_platform_revenue_percent",
        "worker_templates",
        "platform_revenue_percent >= 0 AND platform_revenue_percent <= 100",
    )

    op.create_table(
        "worker_template_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("creator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="custom"),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column("input_schema_json", sa.JSON(), nullable=True),
        sa.Column("output_schema_json", sa.JSON(), nullable=True),
        sa.Column("tools_json", sa.JSON(), nullable=True),
        sa.Column("visibility", sa.String(length=30), nullable=False, server_default="private"),
        sa.Column("price_monthly", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_onetime", sa.Numeric(10, 2), nullable=True),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.Column("screenshots_json", sa.JSON(), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("usage_examples_json", sa.JSON(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creator_revenue_percent", sa.Numeric(5, 2), nullable=False, server_default="70.00"),
        sa.Column("platform_revenue_percent", sa.Numeric(5, 2), nullable=False, server_default="30.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_worker_template_drafts_workspace_slug"),
        sa.CheckConstraint(
            "creator_revenue_percent >= 0 AND creator_revenue_percent <= 100",
            name="ck_worker_template_drafts_creator_revenue_percent",
        ),
        sa.CheckConstraint(
            "platform_revenue_percent >= 0 AND platform_revenue_percent <= 100",
            name="ck_worker_template_drafts_platform_revenue_percent",
        ),
    )
    op.create_index(
        "ix_worker_template_drafts_workspace_creator",
        "worker_template_drafts",
        ["workspace_id", "creator_user_id"],
        unique=False,
    )
    op.create_index("ix_worker_template_drafts_category", "worker_template_drafts", ["category"], unique=False)
    op.create_index("ix_worker_template_drafts_published", "worker_template_drafts", ["is_published"], unique=False)
    op.create_index("ix_worker_template_drafts_slug", "worker_template_drafts", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_worker_template_drafts_slug", table_name="worker_template_drafts")
    op.drop_index("ix_worker_template_drafts_published", table_name="worker_template_drafts")
    op.drop_index("ix_worker_template_drafts_category", table_name="worker_template_drafts")
    op.drop_index("ix_worker_template_drafts_workspace_creator", table_name="worker_template_drafts")
    op.drop_table("worker_template_drafts")

    op.drop_constraint("ck_worker_templates_platform_revenue_percent", "worker_templates", type_="check")
    op.drop_constraint("ck_worker_templates_creator_revenue_percent", "worker_templates", type_="check")
    op.drop_column("worker_templates", "platform_revenue_percent")
    op.drop_column("worker_templates", "creator_revenue_percent")
    op.drop_column("worker_templates", "usage_examples_json")
    op.drop_column("worker_templates", "screenshots_json")
    op.drop_column("worker_templates", "icon")
