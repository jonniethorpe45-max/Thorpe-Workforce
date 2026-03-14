"""worker platform generalization

Revision ID: 0003_worker_platform_generalization
Revises: 0002_worker_lifecycle_and_runs
Create Date: 2026-03-14 15:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_worker_platform_generalization"
down_revision = "0002_worker_lifecycle_and_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_key", sa.String(length=80), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("worker_type", sa.String(length=50), nullable=False),
        sa.Column("worker_category", sa.String(length=80), nullable=False),
        sa.Column("plan_version", sa.String(length=40), nullable=False, server_default="v1"),
        sa.Column("default_config_json", sa.JSON(), nullable=True),
        sa.Column("allowed_actions", sa.JSON(), nullable=True),
        sa.Column("prompt_profile", sa.String(length=80), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.add_column("workers", sa.Column("worker_category", sa.String(length=80), nullable=False, server_default="go_to_market"))
    op.add_column("workers", sa.Column("mission", sa.Text(), nullable=False, server_default=""))
    op.add_column("workers", sa.Column("plan_version", sa.String(length=40), nullable=False, server_default="v1"))
    op.add_column("workers", sa.Column("allowed_actions", sa.JSON(), nullable=True))
    op.add_column("workers", sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_workers_template_id_worker_templates", "workers", "worker_templates", ["template_id"], ["id"])
    op.add_column("workers", sa.Column("origin_type", sa.String(length=40), nullable=False, server_default="built_in"))
    op.add_column("workers", sa.Column("is_custom_worker", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("workers", sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute("UPDATE workers SET mission = goal WHERE mission = ''")

    op.alter_column("workers", "worker_category", server_default=None)
    op.alter_column("workers", "mission", server_default=None)
    op.alter_column("workers", "plan_version", server_default=None)
    op.alter_column("workers", "origin_type", server_default=None)
    op.alter_column("workers", "is_custom_worker", server_default=None)
    op.alter_column("workers", "is_internal", server_default=None)


def downgrade() -> None:
    op.drop_column("workers", "is_internal")
    op.drop_column("workers", "is_custom_worker")
    op.drop_column("workers", "origin_type")
    op.drop_constraint("fk_workers_template_id_worker_templates", "workers", type_="foreignkey")
    op.drop_column("workers", "template_id")
    op.drop_column("workers", "allowed_actions")
    op.drop_column("workers", "plan_version")
    op.drop_column("workers", "mission")
    op.drop_column("workers", "worker_category")
    op.drop_table("worker_templates")
