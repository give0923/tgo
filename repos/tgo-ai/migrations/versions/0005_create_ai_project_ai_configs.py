"""Create ai_project_ai_configs table.

- Primary key: project_id (UUID)
- No foreign key constraints
- Stores default chat and embedding model selections per project
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "ai_0005_project_ai_configs"
down_revision = "ai_0004_drop_fk_llm_providers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_project_ai_configs",
        sa.Column("project_id", UUID(as_uuid=True), primary_key=True, nullable=False, comment="Project UUID (primary key)"),
        sa.Column("default_chat_provider_id", UUID(as_uuid=True), nullable=True, comment="LLM provider id for default chat model"),
        sa.Column("default_chat_model", sa.String(length=150), nullable=True, comment="Default chat model name"),
        sa.Column("default_embedding_provider_id", UUID(as_uuid=True), nullable=True, comment="LLM provider id for default embedding model"),
        sa.Column("default_embedding_model", sa.String(length=150), nullable=True, comment="Default embedding model name"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        comment="Per-project default AI model configuration (synced from tgo-api)",
    )

    # Primary key already provides an index on project_id


def downgrade() -> None:
    op.drop_table("ai_project_ai_configs")

