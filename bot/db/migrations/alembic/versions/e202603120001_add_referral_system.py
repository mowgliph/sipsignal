"""add referral system

Revision ID: e202603120001
Revises: d1234567890f
Create Date: 2026-03-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e202603120001"
down_revision: str | None = "d1234567890f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add columns to users table
    op.add_column("users", sa.Column("referrer_code", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("referred_by", sa.Integer(), nullable=True))

    # 2. Create unique constraint for referrer_code
    op.create_unique_constraint("uq_users_referrer_code", "users", ["referrer_code"])

    # 3. Create foreign key for referred_by
    op.create_foreign_key(
        "fk_users_referred_by", "users", "users", ["referred_by"], ["user_id"], ondelete="SET NULL"
    )

    # 4. Create indexes for performance
    op.create_index("idx_users_referrer_code", "users", ["referrer_code"], unique=False)
    op.create_index("idx_users_referred_by", "users", ["referred_by"], unique=False)

    # 5. Create referrals tracking table
    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("referrer_id", sa.Integer(), nullable=False),
        sa.Column("referred_id", sa.Integer(), nullable=False),
        sa.Column(
            "referred_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["referred_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("referrer_id", "referred_id"),
    )

    # 6. Create indexes for referrals table
    op.create_index("idx_referrals_referrer_id", "referrals", ["referrer_id"], unique=False)
    op.create_index("idx_referrals_referred_id", "referrals", ["referred_id"], unique=False)


def downgrade() -> None:
    # Drop indexes for referrals table
    op.drop_index("idx_referrals_referred_id", table_name="referrals")
    op.drop_index("idx_referrals_referrer_id", table_name="referrals")

    # Drop referrals table
    op.drop_table("referrals")

    # Drop indexes for users table
    op.drop_index("idx_users_referred_by", table_name="users")
    op.drop_index("idx_users_referrer_code", table_name="users")

    # Drop foreign key and constraint
    op.drop_constraint("fk_users_referred_by", "users", type_="foreignkey")
    op.drop_constraint("uq_users_referrer_code", "users", type_="unique")

    # Drop columns
    op.drop_column("users", "referred_by")
    op.drop_column("users", "referrer_code")
