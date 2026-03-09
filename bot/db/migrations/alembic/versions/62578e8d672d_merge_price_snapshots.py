"""merge price snapshots

Revision ID: 62578e8d672d
Revises: a1234567890b, d4567890123e
Create Date: 2026-03-08 20:01:26.597531

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "62578e8d672d"
down_revision: str | Sequence[str] | None = ("a1234567890b", "d4567890123e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
