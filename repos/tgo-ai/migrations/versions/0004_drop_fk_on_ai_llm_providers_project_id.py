"""Drop FK on ai_llm_providers.project_id to decouple from ai_projects.

Rationale:
- tgo-api may send LLM providers for projects that are not yet present in tgo-ai
- Removing the foreign key allows ai_llm_providers.project_id to reference such projects

This migration drops the FK constraint only; the column remains, as do existing
unique/index constraints.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ai_0004_drop_fk_llm_providers"
down_revision = "ai_0003_llm_providers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    # On PostgreSQL, the implicit constraint name is typically <table>_<column>_fkey
    fk_name = "ai_llm_providers_project_id_fkey"

    if dialect == "postgresql":
        op.drop_constraint(fk_name, "ai_llm_providers", type_="foreignkey")
    else:
        # Best-effort for SQLite/others: attempt to drop within batch context.
        # SQLite will recreate the table without the FK if supported by alembic batch.
        try:
            with op.batch_alter_table("ai_llm_providers", schema=None) as batch_op:
                batch_op.drop_constraint(fk_name, type_="foreignkey")
        except Exception:
            # If the backend does not support dropping FKs or the name is not present,
            # proceed without failing (FKs may not be enforced or named on SQLite).
            pass


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    fk_name = "ai_llm_providers_project_id_fkey"

    if dialect == "postgresql":
        op.create_foreign_key(
            fk_name,
            source_table="ai_llm_providers",
            referent_table="ai_projects",
            local_cols=["project_id"],
            remote_cols=["id"],
            ondelete="CASCADE",
        )
    else:
        try:
            with op.batch_alter_table("ai_llm_providers", schema=None) as batch_op:
                batch_op.create_foreign_key(
                    fk_name,
                    referent_table="ai_projects",
                    local_cols=["project_id"],
                    remote_cols=["id"],
                    ondelete="CASCADE",
                )
        except Exception:
            # If the backend cannot recreate the FK in batch mode, ignore.
            pass

