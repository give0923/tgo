"""Add project onboarding progress table.

Revision ID: api_0003_add_onboarding
Revises: api_0002_add_default_team_id
Create Date: 2025-12-02

This migration creates the api_project_onboarding_progress table
for tracking new user onboarding steps per project.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "api_0003_add_onboarding"
down_revision = "api_0002_add_default_team_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create api_project_onboarding_progress table."""
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if "api_project_onboarding_progress" not in tables:
        op.create_table(
            "api_project_onboarding_progress",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "project_id",
                UUID(as_uuid=True),
                sa.ForeignKey("api_projects.id", ondelete="CASCADE"),
                nullable=False,
                comment="Associated project ID (unique)",
            ),
            sa.Column(
                "step_1_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether AI provider setup is completed",
            ),
            sa.Column(
                "step_2_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether default models are configured",
            ),
            sa.Column(
                "step_3_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether RAG collection is created",
            ),
            sa.Column(
                "step_4_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether agent with knowledge base is created",
            ),
            sa.Column(
                "step_5_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether first chat is started",
            ),
            sa.Column(
                "is_completed",
                sa.Boolean(),
                nullable=False,
                default=False,
                comment="Whether all onboarding steps are completed or skipped",
            ),
            sa.Column(
                "completed_at",
                sa.DateTime(),
                nullable=True,
                comment="Timestamp when onboarding was completed or skipped",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("project_id", name="uq_project_onboarding_project_id"),
        )


def downgrade() -> None:
    """Drop api_project_onboarding_progress table."""
    op.drop_table("api_project_onboarding_progress")

