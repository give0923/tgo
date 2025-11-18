"""Add display_name column to rag_collections and related indexes.

This migration fixes runtime error:
  asyncpg.exceptions.UndefinedColumnError: column rag_collections.display_name does not exist

It adds the missing column and creates indexes used by queries.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rag_0002_add_display_name"
down_revision = "rag_0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Add column as nullable first to allow backfill
    op.add_column(
        "rag_collections",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )

    # 2) Backfill values
    # If legacy column "name" exists, copy from it; otherwise set to ''
    name_col_exists = conn.exec_driver_sql(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'rag_collections'
          AND column_name = 'name'
        LIMIT 1
        """
    ).first() is not None

    if name_col_exists:
        op.execute(
            "UPDATE rag_collections SET display_name = name WHERE display_name IS NULL"
        )
    else:
        op.execute(
            "UPDATE rag_collections SET display_name = '' WHERE display_name IS NULL"
        )

    # 3) Make column NOT NULL
    op.alter_column(
        "rag_collections",
        "display_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # 4) Create indexes (idempotent via IF NOT EXISTS)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rag_collections_display_name ON rag_collections(display_name)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rag_collections_project_display_name ON rag_collections(project_id, display_name)"
    )


def downgrade() -> None:
    # Drop indexes if they exist, then drop the column
    op.execute(
        "DROP INDEX IF EXISTS idx_rag_collections_project_display_name"
    )
    op.execute(
        "DROP INDEX IF EXISTS idx_rag_collections_display_name"
    )
    op.drop_column("rag_collections", "display_name")

