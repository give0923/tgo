"""Relax legacy columns in rag_collections (make name/external_id nullable).

This fixes IntegrityError on inserts caused by the legacy NOT NULL constraint:
  asyncpg.exceptions.NotNullViolationError: null value in column "name" of relation "rag_collections" violates not-null constraint

The current ORM model uses display_name instead of name and does not use external_id.
We keep these legacy columns for backward compatibility but make them nullable to avoid
breaking inserts.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rag_0004_relax_legacy_columns"
down_revision = "rag_0003_add_metadata_and_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # If legacy column "name" exists, relax NOT NULL and backfill from display_name where needed
    name_col_exists = conn.exec_driver_sql(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'rag_collections' AND column_name = 'name' LIMIT 1
        """
    ).first() is not None

    if name_col_exists:
        # Backfill any NULL names with display_name to preserve readability (best-effort)
        op.execute(
            "UPDATE rag_collections SET name = display_name WHERE name IS NULL AND display_name IS NOT NULL"
        )
        op.alter_column(
            "rag_collections",
            "name",
            existing_type=sa.String(length=255),
            nullable=True,
        )

    # If legacy column "external_id" exists, relax NOT NULL
    external_id_exists = conn.exec_driver_sql(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'rag_collections' AND column_name = 'external_id' LIMIT 1
        """
    ).first() is not None

    if external_id_exists:
        op.alter_column(
            "rag_collections",
            "external_id",
            existing_type=sa.String(length=64),
            nullable=True,
        )


def downgrade() -> None:
    # Downgrade is a no-op because restoring NOT NULL could break data created after upgrade
    pass

