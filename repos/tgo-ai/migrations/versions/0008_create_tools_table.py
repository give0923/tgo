"""Create tools table for project-level tool configurations.

- No foreign key constraint on project_id (project data lives in tgo-api)
- Indexes on project_id and name for query performance
- JSONB for config payloads
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PG_ENUM

# revision identifiers, used by Alembic.
revision = "ai_0008_create_tools_table"
down_revision = "ai_0007_drop_project_fks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure Postgres ENUM type for tool_type exists without duplicating creation
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        exists = bind.exec_driver_sql("SELECT 1 FROM pg_type WHERE typname = 'tool_type_enum'").fetchone()
        if not exists:
            op.execute("CREATE TYPE tool_type_enum AS ENUM ('MCP', 'FUNCTION')")
    # Use a non-creating ENUM instance for the column to avoid Alembic emitting CREATE TYPE again
    tool_type_enum_for_column = PG_ENUM("MCP", "FUNCTION", name="tool_type_enum", create_type=False)

    # Create tools table
    op.create_table(
        "ai_tools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False, comment="Primary key UUID"),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False, comment="Associated project ID"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Tool name"),
        sa.Column("description", sa.Text(), nullable=True, comment="Optional tool description"),
        sa.Column("tool_type", tool_type_enum_for_column, nullable=False, comment="Tool type (MCP or FUNCTION)"),
        sa.Column("transport_type", sa.String(length=50), nullable=True, comment="Transport type (e.g., http, stdio, sse)"),
        sa.Column("endpoint", sa.String(length=1024), nullable=True, comment="Endpoint URL or path"),
        sa.Column("config", JSONB, nullable=True, comment="Tool configuration as JSON object"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record last update timestamp"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="Soft delete timestamp"),
        comment="Project-level tool configuration",
    )

    # Helpful indexes
    op.create_index("idx_tools_project_id", "ai_tools", ["project_id"], unique=False)
    op.create_index("idx_tools_name", "ai_tools", ["name"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_tools_name", table_name="ai_tools")
    op.drop_index("idx_tools_project_id", table_name="ai_tools")

    # Drop table
    op.drop_table("ai_tools")

    # Drop ENUM type
    tool_type_enum = PG_ENUM("MCP", "FUNCTION", name="tool_type_enum")
    bind = op.get_bind()
    tool_type_enum.drop(bind, checkfirst=True)

