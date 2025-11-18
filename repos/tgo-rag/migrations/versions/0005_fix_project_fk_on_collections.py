"""Fix rag_collections.project_id foreign key to reference rag_projects.

Legacy schema pointed to ai_projects; update to rag_projects to match ORM.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rag_0005_fix_proj_fk"
down_revision = "rag_0004_relax_legacy_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop legacy foreign key if present and recreate pointing to rag_projects
    try:
        op.drop_constraint(
            "rag_collections_project_id_fkey",
            "rag_collections",
            type_="foreignkey",
        )
    except Exception:
        # Constraint might have a different name in some environments; attempt to find and drop via raw SQL
        op.execute(
            """
            DO $$
            DECLARE
                fk_name text;
            BEGIN
                SELECT tc.constraint_name INTO fk_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'rag_collections'
                  AND tc.constraint_type = 'FOREIGN KEY'
                  AND kcu.column_name = 'project_id'
                LIMIT 1;
                IF fk_name IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE rag_collections DROP CONSTRAINT %I', fk_name);
                END IF;
            END$$;
            """
        )

    op.create_foreign_key(
        "rag_collections_project_id_fkey",
        source_table="rag_collections",
        referent_table="rag_projects",
        local_cols=["project_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Best effort: switch back to ai_projects
    op.drop_constraint(
        "rag_collections_project_id_fkey",
        "rag_collections",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "rag_collections_project_id_fkey",
        source_table="rag_collections",
        referent_table="ai_projects",
        local_cols=["project_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

