"""Refactor agent-tool relationship to many-to-many via association table.

- Create ai_agent_tool_associations table (no DB-level FKs)
- Drop legacy ai_agent_tools table if it exists
- Add indexes and optional uniqueness constraint
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "ai_0009_tools_m2m"
down_revision = "ai_0008_create_tools_table"
branch_labels = None
depends_on = None


def _json_type():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return JSONB
    # SQLite and others
    return sa.JSON


def upgrade() -> None:
    # 1) Create association table
    op.create_table(
        "ai_agent_tool_associations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False, comment="Primary key UUID"),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, comment="Associated agent ID"),
        sa.Column("tool_id", UUID(as_uuid=True), nullable=False, comment="Associated tool ID"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Whether tool is enabled for this agent"),
        sa.Column("permissions", _json_type(), nullable=True, comment="Tool permissions array"),
        sa.Column("config", _json_type(), nullable=True, comment="Agent-specific tool configuration overrides"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record last update timestamp"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="Soft delete timestamp"),
        comment="Agent-to-tool association with per-agent settings",
    )

    # Indexes for efficient lookups
    op.create_index("idx_agent_tool_assoc_agent_id", "ai_agent_tool_associations", ["agent_id"], unique=False)
    op.create_index("idx_agent_tool_assoc_tool_id", "ai_agent_tool_associations", ["tool_id"], unique=False)

    # Optional uniqueness to prevent duplicate associations
    try:
        op.create_unique_constraint(
            "uq_agent_tool_assoc_agent_id_tool_id",
            "ai_agent_tool_associations",
            ["agent_id", "tool_id"],
        )
    except Exception:
        # Some dialects may not support unique constraints in the same manner; ignore
        pass

    # 2) Drop legacy table if present
    try:
        op.execute("DROP TABLE IF EXISTS ai_agent_tools")
    except Exception:
        # Ignore if dialect doesn't support IF EXISTS
        pass


def downgrade() -> None:
    # Recreate legacy table minimally (without data) to allow downgrade
    try:
        op.create_table(
            "ai_agent_tools",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("agent_id", UUID(as_uuid=True), nullable=False),
            sa.Column("tool_name", sa.String(length=355), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("permissions", _json_type(), nullable=True),
            sa.Column("config", _json_type(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
    except Exception:
        pass

    # Drop new association table and indexes/constraints
    try:
        op.drop_constraint("uq_agent_tool_assoc_agent_id_tool_id", "ai_agent_tool_associations", type_="unique")
    except Exception:
        pass

    op.drop_index("idx_agent_tool_assoc_tool_id", table_name="ai_agent_tool_associations")
    op.drop_index("idx_agent_tool_assoc_agent_id", table_name="ai_agent_tool_associations")
    op.drop_table("ai_agent_tool_associations")

