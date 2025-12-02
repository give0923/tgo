"""Add parent-child hierarchy to website pages.

This migration adds:
1. parent_page_id - self-referential FK for page hierarchy
2. crawl_source - tracks how the page was added
3. discovered_links - stores links found on the page
4. Makes crawl_job_id nullable (pages can exist without a job)
5. Changes unique constraint from (crawl_job_id, url_hash) to (collection_id, url_hash)

Revision ID: 0008
Revises: 0007_add_qa_pairs_table
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "rag_0008_page_hierarchy"
down_revision = "rag_0007_add_qa_pairs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add hierarchy support to website pages."""
    
    # 1. Add parent_page_id column (self-referential FK)
    op.add_column(
        "rag_website_pages",
        sa.Column(
            "parent_page_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rag_website_pages.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    
    # 2. Add crawl_source column
    op.add_column(
        "rag_website_pages",
        sa.Column(
            "crawl_source",
            sa.String(64),
            nullable=False,
            server_default="discovered",
        ),
    )
    
    # 3. Add discovered_links column (JSONB)
    op.add_column(
        "rag_website_pages",
        sa.Column(
            "discovered_links",
            postgresql.JSONB,
            nullable=True,
        ),
    )
    
    # 4. Make crawl_job_id nullable
    op.alter_column(
        "rag_website_pages",
        "crawl_job_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    
    # 5. Update the foreign key constraint for crawl_job_id to SET NULL
    op.drop_constraint(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        "rag_website_crawl_jobs",
        ["crawl_job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    # 6. Drop old unique constraint on (crawl_job_id, url_hash)
    op.drop_index("ix_rag_website_pages_job_url_unique", table_name="rag_website_pages")

    # 7. Remove duplicate (collection_id, url_hash) entries before creating unique constraint
    # Keep only the oldest record (by created_at) for each duplicate group
    op.execute("""
        DELETE FROM rag_website_pages
        WHERE id NOT IN (
            SELECT DISTINCT ON (collection_id, url_hash) id
            FROM rag_website_pages
            ORDER BY collection_id, url_hash, created_at ASC
        )
    """)

    # 8. Create new unique constraint on (collection_id, url_hash)
    op.create_index(
        "idx_website_pages_collection_url",
        "rag_website_pages",
        ["collection_id", "url_hash"],
        unique=True,
    )
    
    # 8. Add index for parent_page_id
    op.create_index(
        "idx_website_pages_parent_page_id",
        "rag_website_pages",
        ["parent_page_id"],
    )
    
    # 9. Add index for crawl_source
    op.create_index(
        "idx_website_pages_crawl_source",
        "rag_website_pages",
        ["crawl_source"],
    )


def downgrade() -> None:
    """Revert hierarchy changes."""
    
    # Drop new indexes
    op.drop_index("idx_website_pages_crawl_source", table_name="rag_website_pages")
    op.drop_index("idx_website_pages_parent_page_id", table_name="rag_website_pages")
    op.drop_index("idx_website_pages_collection_url", table_name="rag_website_pages")
    
    # Recreate old unique constraint
    op.create_index(
        "ix_rag_website_pages_job_url_unique",
        "rag_website_pages",
        ["crawl_job_id", "url_hash"],
        unique=True,
    )
    
    # Revert crawl_job_id FK to CASCADE
    op.drop_constraint(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "rag_website_pages_crawl_job_id_fkey",
        "rag_website_pages",
        "rag_website_crawl_jobs",
        ["crawl_job_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Make crawl_job_id NOT NULL again (may fail if NULL values exist)
    op.alter_column(
        "rag_website_pages",
        "crawl_job_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    
    # Drop new columns
    op.drop_column("rag_website_pages", "discovered_links")
    op.drop_column("rag_website_pages", "crawl_source")
    op.drop_column("rag_website_pages", "parent_page_id")

