"""Add role change tracking columns to users table.

Revision ID: d1234567890f
Revises: d031d7ddb44d
Create Date: 2026-03-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1234567890f"
down_revision: str | Sequence[str] | None = "d031d7ddb44d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add requested_role column for tracking role change requests
    op.add_column(
        "users",
        sa.Column("requested_role", sa.String(20), nullable=True),
    )

    # Add previous_role column for restoring on denial
    op.add_column(
        "users",
        sa.Column("previous_role", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop previous_role column
    op.drop_column("users", "previous_role")

    # Drop requested_role column
    op.drop_column("users", "requested_role")
