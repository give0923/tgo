"""Add rag_embedding_configs table for project-level embedding settings.

- Stores embedding provider/model and runtime params per project
- Enforces single active config per project via partial unique index
- No FK on project_id by design (project managed upstream)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "rag_0006_add_embedding_configs"
down_revision = "rag_0005_fix_proj_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rag_embedding_configs table and indexes if they do not already exist.

    This migration is written to be idempotent to handle environments where the
    table may have been created manually or by a prior run.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    table_name = "rag_embedding_configs"
    existing_tables = set(insp.get_table_names())

    if table_name not in existing_tables:
        op.create_table(
            table_name,
            sa.Column("id", psql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("project_id", psql.UUID(as_uuid=True), nullable=False),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("dimensions", sa.Integer(), nullable=False, server_default=sa.text("1536")),
            sa.Column("batch_size", sa.Integer(), nullable=False, server_default=sa.text("10")),
            sa.Column("api_key", sa.String(length=512), nullable=True),
            sa.Column("base_url", sa.String(length=512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Ensure required indexes exist by name
    existing_indexes = set(ix.get("name") for ix in insp.get_indexes(table_name)) if table_name in existing_tables else set()

    if "ix_rag_embedding_configs_project_id" not in existing_indexes:
        op.create_index(
            "ix_rag_embedding_configs_project_id",
            table_name,
            ["project_id"],
            unique=False,
        )

    if "ix_rag_embedding_configs_is_active" not in existing_indexes:
        op.create_index(
            "ix_rag_embedding_configs_is_active",
            table_name,
            ["is_active"],
            unique=False,
        )

    if "uq_rag_embedding_configs_project_active" not in existing_indexes:
        op.create_index(
            "uq_rag_embedding_configs_project_active",
            table_name,
            ["project_id"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
        )


def downgrade() -> None:
    # Drop indexes then table
    op.drop_index("uq_rag_embedding_configs_project_active", table_name="rag_embedding_configs")
    op.drop_index("ix_rag_embedding_configs_is_active", table_name="rag_embedding_configs")
    op.drop_index("ix_rag_embedding_configs_project_id", table_name="rag_embedding_configs")
    op.drop_table("rag_embedding_configs")

