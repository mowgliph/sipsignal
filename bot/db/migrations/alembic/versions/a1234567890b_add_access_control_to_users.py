"""Add access control columns to users table.

Revision ID: a1234567890b
Revises: c1234567890a
Create Date: 2026-03-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1234567890b"
down_revision: str | Sequence[str] | None = "c1234567890a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add status column with default value
    op.add_column(
        "users",
        sa.Column("status", sa.String(20), nullable=False, server_default="non_permitted"),
    )

    # Add requested_at column for tracking access request timestamps
    op.add_column(
        "users",
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop requested_at column
    op.drop_column("users", "requested_at")

    # Drop status column
    op.drop_column("users", "status")
