"""Remove WebsiteCrawlJob table and crawl_job_id column.

Revision ID: 0009
Revises: 0008
Create Date: 2024-01-15

This migration removes the WebsiteCrawlJob table and the crawl_job_id column
from rag_website_pages. Crawl configuration is now stored in Collection.crawl_config.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "rag_0009_remove_crawl_jobs"
down_revision = "rag_0008_page_hierarchy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove crawl_job_id column and drop rag_website_crawl_jobs table."""
    # Drop the foreign key constraint first (name from 0008 migration)
    op.drop_constraint(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        type_="foreignkey"
    )

    # Drop the crawl_job_id index (name from 0002 migration)
    op.drop_index(
        "ix_rag_website_pages_crawl_job_id",
        table_name="rag_website_pages"
    )

    # Drop the crawl_job_id column
    op.drop_column("rag_website_pages", "crawl_job_id")

    # Drop the rag_website_crawl_jobs table
    op.drop_table("rag_website_crawl_jobs")


def downgrade() -> None:
    """Recreate rag_website_crawl_jobs table and crawl_job_id column."""
    # Recreate the rag_website_crawl_jobs table
    op.create_table(
        "rag_website_crawl_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_url", sa.String(2048), nullable=False),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("include_patterns", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("exclude_patterns", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("crawl_options", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("pages_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_crawled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["collection_id"], ["rag_collections.id"], ondelete="CASCADE"),
    )

    # Create indexes for the crawl jobs table (matching 0002 migration naming)
    op.create_index("ix_rag_website_crawl_jobs_collection_id", "rag_website_crawl_jobs", ["collection_id"])
    op.create_index("ix_rag_website_crawl_jobs_status", "rag_website_crawl_jobs", ["status"])

    # Add crawl_job_id column back to rag_website_pages
    op.add_column(
        "rag_website_pages",
        sa.Column("crawl_job_id", postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Create index for crawl_job_id (matching 0002 migration naming)
    op.create_index(
        "ix_rag_website_pages_crawl_job_id",
        "rag_website_pages",
        ["crawl_job_id"]
    )

    # Add foreign key constraint (matching 0008 migration naming)
    op.create_foreign_key(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        "rag_website_crawl_jobs",
        ["crawl_job_id"],
        ["id"],
        ondelete="SET NULL"
    )

