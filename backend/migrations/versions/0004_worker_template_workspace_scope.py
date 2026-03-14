"""worker template workspace scope

Revision ID: 0004_worker_template_workspace_scope
Revises: 0003_worker_platform_generalization
Create Date: 2026-03-14 16:10:00.000000
"""

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_worker_template_workspace_scope"
down_revision = "0003_worker_platform_generalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("worker_templates", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_worker_templates_workspace_id_workspaces",
        "worker_templates",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_worker_templates_workspace_id_workspaces", "worker_templates", type_="foreignkey")
    op.drop_column("worker_templates", "workspace_id")
