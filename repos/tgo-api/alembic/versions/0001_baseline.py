"""Baseline migration for tgo-api.

This migration represents the starting point of the schema after
resetting migrations. It creates all api_* tables defined in the
SQLAlchemy models so that a fresh database is fully ready for use.
"""

from alembic import op

from app.core.database import Base

# revision identifiers, used by Alembic.
revision = "api_0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all api_* tables defined on Base.metadata.

    We delegate to SQLAlchemy's metadata to ensure the schema matches
    the current models. "checkfirst=True" makes this safe to run on an
    empty database and idempotent if tables already exist.
    """

    bind = op.get_bind()

    # Only create api_* tables (this matches Alembic's include_* filters)
    tables = [t for t in Base.metadata.sorted_tables if t.name.startswith("api_")]
    for table in tables:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    """Drop all api_* tables.

    This is primarily for local development/testing. In production you
    typically wouldn't downgrade a baseline in this way.
    """

    bind = op.get_bind()

    # Drop in reverse dependency order
    tables = [t for t in reversed(Base.metadata.sorted_tables) if t.name.startswith("api_")]
    for table in tables:
        table.drop(bind=bind, checkfirst=True)

