"""Drop foreign key constraints on project_id columns referencing ai_projects.

Rationale:
- tgo-ai is now internal-only and receives project_id from tgo-api
- Allow referencing projects that may not be present locally
- Keep project_id columns but remove DB-level FK constraints
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ai_0007_drop_project_fks"
down_revision = "ai_0006_proj_ai_cfg_sync"
branch_labels = None
depends_on = None


TARGET_TABLES = [
    "ai_teams",
    "ai_agents",
    "ai_collections",
    "ai_tool_usage_records",
    "ai_collection_usage_records",
    "ai_agent_usage_records",
]


def _drop_fk_to_projects(table_name: str) -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    # Only run on Postgres; for other dialects, skip
    if dialect != "postgresql":
        return

    insp = sa.inspect(bind)

    # If table doesn't exist, skip safely
    try:
        if not insp.has_table(table_name):
            return
    except Exception:
        # If inspector cannot check, continue and rely on IF EXISTS below
        pass

    # Drop any FK that targets ai_projects or involves project_id using IF EXISTS to avoid aborting txn
    fkeys = insp.get_foreign_keys(table_name) or []
    for fk in fkeys:
        referred = fk.get("referred_table")
        constrained_cols = fk.get("constrained_columns") or []
        if referred == "ai_projects" or "project_id" in constrained_cols:
            name = fk.get("name")
            if name:
                op.execute(sa.text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{name}"'))

    # Fallback: conventional Postgres-generated name
    default_name = f"{table_name}_project_id_fkey"
    op.execute(sa.text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{default_name}"'))


def upgrade() -> None:
    for table in TARGET_TABLES:
        _drop_fk_to_projects(table)


def _create_fk_to_projects(table_name: str) -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    fk_name = f"{table_name}_project_id_fkey"

    if dialect == "postgresql":
        try:
            op.create_foreign_key(
                fk_name,
                source_table=table_name,
                referent_table="ai_projects",
                local_cols=["project_id"],
                remote_cols=["id"],
                ondelete="CASCADE",
            )
            return
        except Exception:
            pass

    # Fallback / other dialects
    try:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.create_foreign_key(
                fk_name,
                referent_table="ai_projects",
                local_cols=["project_id"],
                remote_cols=["id"],
                ondelete="CASCADE",
            )
    except Exception:
        # If the backend cannot recreate the FK, ignore in downgrade
        pass


def downgrade() -> None:
    for table in TARGET_TABLES:
        _create_fk_to_projects(table)

