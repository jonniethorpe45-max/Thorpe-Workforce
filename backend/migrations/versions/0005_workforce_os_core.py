"""workforce os core models

Revision ID: 0005_workforce_os_core
Revises: 0004_worker_template_workspace_scope
Create Date: 2026-03-14 17:15:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0005_workforce_os_core"
down_revision = "0004_worker_template_workspace_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend worker_templates for marketplace/public metadata.
    op.add_column("worker_templates", sa.Column("creator_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("worker_templates", sa.Column("name", sa.String(length=120), nullable=False, server_default=""))
    op.add_column("worker_templates", sa.Column("slug", sa.String(length=160), nullable=True))
    op.add_column("worker_templates", sa.Column("short_description", sa.String(length=255), nullable=True))
    op.add_column("worker_templates", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("worker_templates", sa.Column("category", sa.String(length=80), nullable=False, server_default="general"))
    op.add_column("worker_templates", sa.Column("visibility", sa.String(length=30), nullable=False, server_default="workspace"))
    op.add_column("worker_templates", sa.Column("status", sa.String(length=30), nullable=False, server_default="active"))
    op.add_column("worker_templates", sa.Column("instructions", sa.Text(), nullable=True))
    op.add_column("worker_templates", sa.Column("model_name", sa.String(length=120), nullable=True))
    op.add_column("worker_templates", sa.Column("config_json", sa.JSON(), nullable=True))
    op.add_column("worker_templates", sa.Column("capabilities_json", sa.JSON(), nullable=True))
    op.add_column("worker_templates", sa.Column("actions_json", sa.JSON(), nullable=True))
    op.add_column("worker_templates", sa.Column("tools_json", sa.JSON(), nullable=True))
    op.add_column("worker_templates", sa.Column("memory_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("worker_templates", sa.Column("chain_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("worker_templates", sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("worker_templates", sa.Column("is_marketplace_listed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("worker_templates", sa.Column("pricing_type", sa.String(length=30), nullable=False, server_default="internal"))
    op.add_column("worker_templates", sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_templates", sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"))
    op.add_column("worker_templates", sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_templates", sa.Column("rating_avg", sa.Float(), nullable=False, server_default="0"))
    op.add_column("worker_templates", sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_templates", sa.Column("tags_json", sa.JSON(), nullable=True))

    op.create_foreign_key(
        "fk_worker_templates_creator_user_id_users",
        "worker_templates",
        "users",
        ["creator_user_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_worker_templates_workspace_slug",
        "worker_templates",
        ["workspace_id", "slug"],
    )
    op.create_index("ix_worker_templates_slug", "worker_templates", ["slug"], unique=False)
    op.create_index(
        "ix_worker_templates_visibility_status",
        "worker_templates",
        ["visibility", "status"],
        unique=False,
    )
    op.create_index(
        "ix_worker_templates_marketplace_listed",
        "worker_templates",
        ["is_marketplace_listed"],
        unique=False,
    )

    op.execute("UPDATE worker_templates SET name = display_name WHERE name = ''")
    op.execute("UPDATE worker_templates SET slug = template_key WHERE slug IS NULL OR slug = ''")
    op.execute("UPDATE worker_templates SET category = worker_category WHERE worker_category IS NOT NULL")
    op.execute(
        "UPDATE worker_templates SET visibility = CASE WHEN is_public THEN 'public' ELSE 'workspace' END "
        "WHERE visibility = 'workspace'"
    )
    op.execute(
        "UPDATE worker_templates SET status = CASE WHEN is_active THEN 'active' ELSE 'archived' END "
        "WHERE status = 'active'"
    )
    op.execute(
        "UPDATE worker_templates SET is_system_template = CASE WHEN workspace_id IS NULL THEN true ELSE false END"
    )
    op.execute("UPDATE worker_templates SET is_marketplace_listed = is_public")
    op.execute(
        "UPDATE worker_templates SET pricing_type = 'free', price_cents = 0 "
        "WHERE is_public = true AND pricing_type = 'internal'"
    )

    # Worker instances for explicit runtime worker objects.
    op.create_table(
        "worker_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("legacy_worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workers.id"), nullable=True, unique=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("runtime_config_json", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schedule_expression", sa.String(length=120), nullable=True),
        sa.Column("memory_scope", sa.String(length=20), nullable=False, server_default="instance"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_worker_instances_workspace_status",
        "worker_instances",
        ["workspace_id", "status"],
        unique=False,
    )
    op.create_index("ix_worker_instances_template_id", "worker_instances", ["template_id"], unique=False)
    op.create_index("ix_worker_instances_next_run_at", "worker_instances", ["next_run_at"], unique=False)

    # Extend worker_runs for richer run telemetry.
    op.add_column("worker_runs", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("worker_runs", sa.Column("instance_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("worker_runs", sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("worker_runs", sa.Column("triggered_by", sa.String(length=40), nullable=False, server_default="manual"))
    op.add_column("worker_runs", sa.Column("trigger_source", sa.String(length=255), nullable=True))
    op.add_column("worker_runs", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("worker_runs", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.add_column("worker_runs", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("worker_runs", sa.Column("token_usage_input", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_runs", sa.Column("token_usage_output", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_runs", sa.Column("cost_cents", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("worker_runs", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    op.create_foreign_key(
        "fk_worker_runs_workspace_id_workspaces",
        "worker_runs",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_worker_runs_instance_id_worker_instances",
        "worker_runs",
        "worker_instances",
        ["instance_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_worker_runs_template_id_worker_templates",
        "worker_runs",
        "worker_templates",
        ["template_id"],
        ["id"],
    )
    op.create_index("ix_worker_runs_workspace_id", "worker_runs", ["workspace_id"], unique=False)
    op.create_index("ix_worker_runs_instance_id", "worker_runs", ["instance_id"], unique=False)
    op.create_index("ix_worker_runs_template_id", "worker_runs", ["template_id"], unique=False)

    op.execute(
        "UPDATE worker_runs wr "
        "SET workspace_id = w.workspace_id, template_id = w.template_id "
        "FROM workers w "
        "WHERE wr.worker_id = w.id"
    )
    op.execute("UPDATE worker_runs SET created_at = started_at WHERE created_at IS NULL")
    op.execute("UPDATE worker_runs SET error_message = error_text WHERE error_message IS NULL AND error_text IS NOT NULL")

    # Worker memory store.
    op.create_table(
        "worker_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_instances.id"), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=True),
        sa.Column("memory_key", sa.String(length=255), nullable=False),
        sa.Column("memory_value_json", sa.JSON(), nullable=False),
        sa.Column("memory_type", sa.String(length=50), nullable=False, server_default="episodic"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_worker_memory_workspace_key", "worker_memory", ["workspace_id", "memory_key"], unique=False)
    op.create_index("ix_worker_memory_instance_id", "worker_memory", ["instance_id"], unique=False)
    op.create_index("ix_worker_memory_template_id", "worker_memory", ["template_id"], unique=False)

    # Worker chains.
    op.create_table(
        "worker_chains",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("trigger_type", sa.String(length=40), nullable=False, server_default="manual"),
        sa.Column("trigger_config_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_worker_chains_workspace_status", "worker_chains", ["workspace_id", "status"], unique=False)

    op.create_table(
        "worker_chain_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_chains.id"), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("worker_instance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_instances.id"), nullable=True),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=True),
        sa.Column("step_name", sa.String(length=120), nullable=False),
        sa.Column("input_mapping_json", sa.JSON(), nullable=True),
        sa.Column("condition_json", sa.JSON(), nullable=True),
        sa.Column("on_success_next_step", sa.Integer(), nullable=True),
        sa.Column("on_failure_next_step", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("chain_id", "step_order", name="uq_worker_chain_steps_chain_order"),
        sa.CheckConstraint(
            "(worker_instance_id IS NOT NULL) OR (worker_template_id IS NOT NULL)",
            name="ck_worker_chain_steps_worker_ref",
        ),
    )
    op.create_index("ix_worker_chain_steps_chain_id", "worker_chain_steps", ["chain_id"], unique=False)

    # Worker tools and template bindings.
    op.create_table(
        "worker_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("config_schema_json", sa.JSON(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_worker_tools_category_active", "worker_tools", ["category", "is_active"], unique=False)

    op.create_table(
        "worker_template_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("worker_tool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_tools.id"), nullable=False),
        sa.UniqueConstraint("worker_template_id", "worker_tool_id", name="uq_worker_template_tool_pair"),
    )

    # Subscriptions/purchases and revenue events.
    op.create_table(
        "worker_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("purchaser_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("billing_status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_worker_subscriptions_workspace_active",
        "worker_subscriptions",
        ["workspace_id", "is_active"],
        unique=False,
    )
    op.create_index("ix_worker_subscriptions_template_id", "worker_subscriptions", ["worker_template_id"], unique=False)

    op.create_table(
        "worker_revenue_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("creator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("revenue_type", sa.String(length=40), nullable=False),
        sa.Column("gross_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_fee_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("creator_payout_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("reference_type", sa.String(length=60), nullable=True),
        sa.Column("reference_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_worker_revenue_events_template", "worker_revenue_events", ["worker_template_id"], unique=False)
    op.create_index("ix_worker_revenue_events_workspace", "worker_revenue_events", ["workspace_id"], unique=False)

    op.create_table(
        "worker_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("worker_template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("worker_templates.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("worker_template_id", "user_id", "workspace_id", name="uq_worker_reviews_template_user_workspace"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_worker_reviews_rating_range"),
    )
    op.create_index("ix_worker_reviews_template_id", "worker_reviews", ["worker_template_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_worker_reviews_template_id", table_name="worker_reviews")
    op.drop_table("worker_reviews")

    op.drop_index("ix_worker_revenue_events_workspace", table_name="worker_revenue_events")
    op.drop_index("ix_worker_revenue_events_template", table_name="worker_revenue_events")
    op.drop_table("worker_revenue_events")

    op.drop_index("ix_worker_subscriptions_template_id", table_name="worker_subscriptions")
    op.drop_index("ix_worker_subscriptions_workspace_active", table_name="worker_subscriptions")
    op.drop_table("worker_subscriptions")

    op.drop_table("worker_template_tools")

    op.drop_index("ix_worker_tools_category_active", table_name="worker_tools")
    op.drop_table("worker_tools")

    op.drop_index("ix_worker_chain_steps_chain_id", table_name="worker_chain_steps")
    op.drop_table("worker_chain_steps")

    op.drop_index("ix_worker_chains_workspace_status", table_name="worker_chains")
    op.drop_table("worker_chains")

    op.drop_index("ix_worker_memory_template_id", table_name="worker_memory")
    op.drop_index("ix_worker_memory_instance_id", table_name="worker_memory")
    op.drop_index("ix_worker_memory_workspace_key", table_name="worker_memory")
    op.drop_table("worker_memory")

    op.drop_index("ix_worker_runs_template_id", table_name="worker_runs")
    op.drop_index("ix_worker_runs_instance_id", table_name="worker_runs")
    op.drop_index("ix_worker_runs_workspace_id", table_name="worker_runs")
    op.drop_constraint("fk_worker_runs_template_id_worker_templates", "worker_runs", type_="foreignkey")
    op.drop_constraint("fk_worker_runs_instance_id_worker_instances", "worker_runs", type_="foreignkey")
    op.drop_constraint("fk_worker_runs_workspace_id_workspaces", "worker_runs", type_="foreignkey")
    op.drop_column("worker_runs", "created_at")
    op.drop_column("worker_runs", "cost_cents")
    op.drop_column("worker_runs", "token_usage_output")
    op.drop_column("worker_runs", "token_usage_input")
    op.drop_column("worker_runs", "error_message")
    op.drop_column("worker_runs", "duration_ms")
    op.drop_column("worker_runs", "summary")
    op.drop_column("worker_runs", "trigger_source")
    op.drop_column("worker_runs", "triggered_by")
    op.drop_column("worker_runs", "template_id")
    op.drop_column("worker_runs", "instance_id")
    op.drop_column("worker_runs", "workspace_id")

    op.drop_index("ix_worker_instances_next_run_at", table_name="worker_instances")
    op.drop_index("ix_worker_instances_template_id", table_name="worker_instances")
    op.drop_index("ix_worker_instances_workspace_status", table_name="worker_instances")
    op.drop_table("worker_instances")

    op.drop_index("ix_worker_templates_marketplace_listed", table_name="worker_templates")
    op.drop_index("ix_worker_templates_visibility_status", table_name="worker_templates")
    op.drop_index("ix_worker_templates_slug", table_name="worker_templates")
    op.drop_constraint("uq_worker_templates_workspace_slug", "worker_templates", type_="unique")
    op.drop_constraint("fk_worker_templates_creator_user_id_users", "worker_templates", type_="foreignkey")
    op.drop_column("worker_templates", "tags_json")
    op.drop_column("worker_templates", "rating_count")
    op.drop_column("worker_templates", "rating_avg")
    op.drop_column("worker_templates", "install_count")
    op.drop_column("worker_templates", "currency")
    op.drop_column("worker_templates", "price_cents")
    op.drop_column("worker_templates", "pricing_type")
    op.drop_column("worker_templates", "is_marketplace_listed")
    op.drop_column("worker_templates", "is_system_template")
    op.drop_column("worker_templates", "chain_enabled")
    op.drop_column("worker_templates", "memory_enabled")
    op.drop_column("worker_templates", "tools_json")
    op.drop_column("worker_templates", "actions_json")
    op.drop_column("worker_templates", "capabilities_json")
    op.drop_column("worker_templates", "config_json")
    op.drop_column("worker_templates", "model_name")
    op.drop_column("worker_templates", "instructions")
    op.drop_column("worker_templates", "status")
    op.drop_column("worker_templates", "visibility")
    op.drop_column("worker_templates", "category")
    op.drop_column("worker_templates", "description")
    op.drop_column("worker_templates", "short_description")
    op.drop_column("worker_templates", "slug")
    op.drop_column("worker_templates", "name")
    op.drop_column("worker_templates", "creator_user_id")
