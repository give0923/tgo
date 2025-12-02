"""Add crawl_config to website pages.

This migration adds a crawl_config JSONB column to the rag_website_pages table.
This allows per-page crawl configuration that can override the collection defaults.

Revision ID: rag_0010_page_crawl_config
Revises: rag_0009_remove_crawl_jobs
Create Date: 2025-01-15

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic
revision = "rag_0010_page_crawl_config"
down_revision = "rag_0009_remove_crawl_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add crawl_config column to rag_website_pages table."""
    op.add_column(
        "rag_website_pages",
        sa.Column(
            "crawl_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Page-specific crawl configuration that overrides collection defaults",
        ),
    )


def downgrade() -> None:
    """Remove crawl_config column from rag_website_pages table."""
    op.drop_column("rag_website_pages", "crawl_config")

