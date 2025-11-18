"""
Alter rag_files.status column length to 64 to accommodate intermediate processing statuses.

Revision ID: rag_0007_status_len_64
Revises: rag_0006_add_embedding_configs
Create Date: 2025-11-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rag_0007_status_len_64"
down_revision = "rag_0006_add_embedding_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Acquire an exclusive lock to prevent concurrent writes during type change
    op.execute("LOCK TABLE rag_files IN ACCESS EXCLUSIVE MODE")

    # Increase status column size from 20 to 64
    op.alter_column(
        "rag_files",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert status column size back to 20
    op.alter_column(
        "rag_files",
        "status",
        existing_type=sa.String(length=64),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

