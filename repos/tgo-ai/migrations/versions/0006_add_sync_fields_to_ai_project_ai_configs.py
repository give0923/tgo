"""Add sync tracking fields to ai_project_ai_configs.

- Adds last_sync_at (tz-aware)
- Adds sync_status (with default 'not_synced')
- Adds sync_error (text)
- Adds sync_attempt_count (int)
- Adds index on sync_status
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ai_0006_proj_ai_cfg_sync"
down_revision = "ai_0005_project_ai_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_project_ai_configs",
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True, comment="Timestamp of last successful sync to RAG"),
    )
    op.add_column(
        "ai_project_ai_configs",
        sa.Column("sync_status", sa.String(length=32), nullable=True, server_default="not_synced", comment="Current sync status: pending|success|failed|not_synced"),
    )
    op.add_column(
        "ai_project_ai_configs",
        sa.Column("sync_error", sa.Text(), nullable=True, comment="Last sync error message, if any"),
    )
    op.add_column(
        "ai_project_ai_configs",
        sa.Column("sync_attempt_count", sa.Integer(), nullable=True, server_default="0", comment="Number of sync attempts for current config"),
    )

    op.create_index(
        "ix_ai_project_ai_configs_sync_status",
        "ai_project_ai_configs",
        ["sync_status"],
        unique=False,
    )



def downgrade() -> None:
    op.drop_index("ix_ai_project_ai_configs_sync_status", table_name="ai_project_ai_configs")
    op.drop_column("ai_project_ai_configs", "sync_attempt_count")
    op.drop_column("ai_project_ai_configs", "sync_error")
    op.drop_column("ai_project_ai_configs", "sync_status")
    op.drop_column("ai_project_ai_configs", "last_sync_at")

