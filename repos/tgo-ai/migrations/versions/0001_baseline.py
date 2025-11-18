"""Baseline (compressed) migration for tgo-ai.

This represents the starting point of the schema after resetting migrations.
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "ai_0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline marker: tables are created out-of-band (SQLAlchemy create_all)
    pass


def downgrade() -> None:
    # No-op for baseline
    pass

