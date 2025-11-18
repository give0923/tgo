"""Create ai_llm_providers table and add llm_provider_id to agents and teams.

This introduces DB-backed LLM provider credentials and wiring for Agent/Team.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "ai_0003_llm_providers"
down_revision = "ai_0002_ai_collections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Create ai_llm_providers table
    op.create_table(
        "ai_llm_providers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False, comment="Primary key UUID"),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("ai_projects.id", ondelete="CASCADE"), nullable=False, comment="Associated project ID"),
        sa.Column("alias", sa.String(length=80), nullable=False, comment="Unique alias within project"),
        sa.Column("provider_kind", sa.String(length=40), nullable=False, comment="openai/anthropic/google/openai_compatible"),
        sa.Column("vendor", sa.String(length=40), nullable=True, comment="Vendor label (e.g. deepseek)"),
        sa.Column("api_base_url", sa.String(length=255), nullable=True, comment="Custom API base URL"),
        sa.Column("api_key", sa.String(length=255), nullable=True, comment="API key (do NOT log)"),
        sa.Column("organization", sa.String(length=100), nullable=True, comment="Organization/tenant id"),
        sa.Column("timeout", sa.Float(), nullable=True, comment="Request timeout seconds"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="Whether this provider is active"),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Last sync timestamp"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        comment="Project-level LLM provider credentials",
    )

    # Unique and helpful indexes
    with op.batch_alter_table("ai_llm_providers", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_ai_llm_providers_project_alias",
            ["project_id", "alias"],
        )
        batch_op.create_index("idx_ai_llm_providers_project_kind_active", ["project_id", "provider_kind", "is_active"], unique=False)
        batch_op.create_index("idx_ai_llm_providers_project_vendor", ["project_id", "vendor"], unique=False)

    # 2) Add llm_provider_id foreign keys to agents and teams
    with op.batch_alter_table("ai_agents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("llm_provider_id", UUID(as_uuid=True), sa.ForeignKey("ai_llm_providers.id", ondelete="SET NULL"), nullable=True, comment="Associated LLM provider (credentials) ID"),
        )
        batch_op.create_index("idx_ai_agents_llm_provider_id", ["llm_provider_id"], unique=False)

    with op.batch_alter_table("ai_teams", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("llm_provider_id", UUID(as_uuid=True), sa.ForeignKey("ai_llm_providers.id", ondelete="SET NULL"), nullable=True, comment="Associated LLM provider (credentials) ID"),
        )
        batch_op.create_index("idx_ai_teams_llm_provider_id", ["llm_provider_id"], unique=False)


def downgrade() -> None:
    # Drop added columns and indexes
    with op.batch_alter_table("ai_teams", schema=None) as batch_op:
        batch_op.drop_index("idx_ai_teams_llm_provider_id")
        batch_op.drop_column("llm_provider_id")

    with op.batch_alter_table("ai_agents", schema=None) as batch_op:
        batch_op.drop_index("idx_ai_agents_llm_provider_id")
        batch_op.drop_column("llm_provider_id")

    # Drop provider table indexes and table
    with op.batch_alter_table("ai_llm_providers", schema=None) as batch_op:
        batch_op.drop_index("idx_ai_llm_providers_project_vendor")
        batch_op.drop_index("idx_ai_llm_providers_project_kind_active")
        batch_op.drop_constraint("uq_ai_llm_providers_project_alias", type_="unique")

    op.drop_table("ai_llm_providers")

