"""Create ai_collections table for tgo-ai service.

This decouples AI service collections from RAG service tables by introducing
an ai_* namespaced table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "ai_0002_ai_collections"
down_revision = "ai_0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_collections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False, comment="Primary key UUID"),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("ai_projects.id", ondelete="CASCADE"), nullable=False, comment="Associated project ID"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Collection display name"),
        sa.Column("description", sa.Text(), nullable=True, comment="Optional collection description"),
        sa.Column("external_id", sa.String(length=64), nullable=False, unique=True, comment="External RAG service collection identifier"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record creation timestamp"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="Record last update timestamp"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="Soft delete timestamp"),
        comment="Project-level knowledge collection metadata",
    )

    # Helpful indexes
    op.create_index("idx_ai_collections_project_id", "ai_collections", ["project_id"], unique=False)
    op.create_index("idx_ai_collections_deleted_at", "ai_collections", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_ai_collections_deleted_at", table_name="ai_collections")
    op.drop_index("idx_ai_collections_project_id", table_name="ai_collections")
    op.drop_table("ai_collections")

