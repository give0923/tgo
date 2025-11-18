"""Add collection_metadata (JSONB) and tags (text[]) to rag_collections.

Fixes runtime error:
  asyncpg.exceptions.UndefinedColumnError: column rag_collections.collection_metadata does not exist

Also creates a GIN index on tags for fast filtering.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "rag_0003_add_metadata_and_tags"
down_revision = "rag_0002_add_display_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add JSONB column for metadata (nullable)
    op.add_column(
        "rag_collections",
        sa.Column("collection_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Add tags as array of varchar (nullable)
    op.add_column(
        "rag_collections",
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=True),
    )

    # Create GIN index on tags for efficient array membership queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rag_collections_tags ON rag_collections USING gin (tags)"
    )


def downgrade() -> None:
    # Drop index then columns
    op.execute("DROP INDEX IF EXISTS idx_rag_collections_tags")
    op.drop_column("rag_collections", "tags")
    op.drop_column("rag_collections", "collection_metadata")

