"""worker lifecycle and run tracking

Revision ID: 0002_worker_lifecycle_and_runs
Revises: 0001_initial_schema
Create Date: 2026-03-14 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_worker_lifecycle_and_runs"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workers", sa.Column("run_interval_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("workers", sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workers", sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workers", sa.Column("last_error_text", sa.Text(), nullable=True))
    op.alter_column("workers", "run_interval_minutes", server_default=None)

    op.add_column("worker_runs", sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_worker_runs_campaign_id_campaigns", "worker_runs", "campaigns", ["campaign_id"], ["id"])
    op.add_column("worker_runs", sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"))
    op.alter_column("worker_runs", "attempts", server_default=None)


def downgrade() -> None:
    op.drop_column("worker_runs", "attempts")
    op.drop_constraint("fk_worker_runs_campaign_id_campaigns", "worker_runs", type_="foreignkey")
    op.drop_column("worker_runs", "campaign_id")

    op.drop_column("workers", "last_error_text")
    op.drop_column("workers", "next_run_at")
    op.drop_column("workers", "last_run_at")
    op.drop_column("workers", "run_interval_minutes")
