"""Add pt_ prefix to inbox tables and add platform_open_id to wukongim_inbox

Revision ID: pt_0002_prefix_open_id
Revises: pt_0001_baseline
Create Date: 2025-11-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "pt_0002_prefix_open_id"
down_revision = "pt_0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tables to add pt_ prefix
    op.rename_table("email_inbox", "pt_email_inbox")
    op.rename_table("wecom_inbox", "pt_wecom_inbox")
    op.rename_table("wukongim_inbox", "pt_wukongim_inbox")
    
    # Add platform_open_id column to pt_wukongim_inbox
    op.add_column(
        "pt_wukongim_inbox",
        sa.Column("platform_open_id", sa.String(length=255), nullable=True)
    )
    
    # Create index on platform_open_id
    op.create_index(
        "ix_wukongim_inbox_platform_open_id",
        "pt_wukongim_inbox",
        ["platform_open_id"],
        unique=False
    )


def downgrade() -> None:
    # Drop index on platform_open_id
    op.drop_index("ix_wukongim_inbox_platform_open_id", table_name="pt_wukongim_inbox")
    
    # Drop platform_open_id column
    op.drop_column("pt_wukongim_inbox", "platform_open_id")
    
    # Rename tables back to original names
    op.rename_table("pt_wukongim_inbox", "wukongim_inbox")
    op.rename_table("pt_wecom_inbox", "wecom_inbox")
    op.rename_table("pt_email_inbox", "email_inbox")

