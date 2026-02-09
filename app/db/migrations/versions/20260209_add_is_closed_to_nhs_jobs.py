"""Add is_closed to nhs_jobs

Revision ID: 20260209a1b2
Revises:
Create Date: 2026-02-09 13:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260209a1b2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nhs_jobs",
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("nhs_jobs", "is_closed")
