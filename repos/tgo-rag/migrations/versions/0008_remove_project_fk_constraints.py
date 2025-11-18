"""
Remove foreign key constraints on project_id columns to decouple from rag_projects.

Revision ID: rag_0008_drop_proj_fk
Revises: rag_0007_status_len_64
Create Date: 2025-11-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rag_0008_drop_proj_fk"
down_revision = "rag_0007_status_len_64"
branch_labels = None
depends_on = None


def _drop_project_fk(table: str, column: str = "project_id") -> None:
    op.execute(
        f"""
        DO $$
        DECLARE
            fk_name text;
        BEGIN
            SELECT tc.constraint_name INTO fk_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = '{table}'
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = '{column}'
            LIMIT 1;
            IF fk_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %I', fk_name);
            END IF;
        END$$;
        """
    )


def upgrade() -> None:
    # Drop FK constraints on project_id for target tables
    _drop_project_fk("rag_files")
    _drop_project_fk("rag_collections")
    _drop_project_fk("rag_file_documents")


def downgrade() -> None:
    # Recreate FK constraints to rag_projects (best-effort)
    op.create_foreign_key(
        "rag_files_project_id_fkey",
        source_table="rag_files",
        referent_table="rag_projects",
        local_cols=["project_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "rag_collections_project_id_fkey",
        source_table="rag_collections",
        referent_table="rag_projects",
        local_cols=["project_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "rag_file_documents_project_id_fkey",
        source_table="rag_file_documents",
        referent_table="rag_projects",
        local_cols=["project_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

