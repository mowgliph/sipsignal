"""add user price snapshots table

Revision ID: d4567890123e
Revises: a1234567890b
Create Date: 2026-03-08 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4567890123e"
down_revision: str | Sequence[str] | None = "b500dbed383f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_price_snapshots table
    op.create_table(
        "user_price_snapshots",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.PrimaryKeyConstraint("user_id", "symbol"),
    )

    # Create indexes
    op.create_index("idx_user_price_snapshots_user_id", "user_price_snapshots", ["user_id"])
    op.create_index("idx_user_price_snapshots_symbol", "user_price_snapshots", ["symbol"])

    # Create trigger for updated_at (PostgreSQL-specific)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER update_user_price_snapshots_updated_at
            BEFORE UPDATE ON user_price_snapshots
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute(
        "DROP TRIGGER IF EXISTS update_user_price_snapshots_updated_at ON user_price_snapshots"
    )

    # Drop indexes
    op.drop_index("idx_user_price_snapshots_symbol", table_name="user_price_snapshots")
    op.drop_index("idx_user_price_snapshots_user_id", table_name="user_price_snapshots")

    # Drop table
    op.drop_table("user_price_snapshots")
