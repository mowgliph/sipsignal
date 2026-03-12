"""PostgreSQL implementation of ReferralRepository."""

from bot.core import database
from bot.domain.ports.repositories import ReferralRepository
from bot.utils.referral_code import generate_referral_code


class PostgreSQLReferralRepository(ReferralRepository):
    async def get_referrer_code(self, user_id: int) -> str | None:
        """Get user's referral code."""
        record = await database.fetchrow(
            "SELECT referrer_code FROM users WHERE user_id = $1",
            user_id,
        )
        return record["referrer_code"] if record else None

    async def generate_referrer_code(self, user_id: int) -> str:
        """Generate and save unique referral code for user."""
        # Check if already exists
        existing = await self.get_referrer_code(user_id)
        if existing:
            return existing

        # Generate unique code with retry
        max_retries = 10
        for _ in range(max_retries):
            code = generate_referral_code()
            # Check uniqueness
            existing_user = await self.get_by_code(code)
            if existing_user is None:
                # Save code
                await database.execute(
                    "UPDATE users SET referrer_code = $1 WHERE user_id = $2",
                    code,
                    user_id,
                )
                return code

        raise RuntimeError("Failed to generate unique referral code")

    async def get_by_code(self, code: str) -> int | None:
        """Get user_id from referral code."""
        record = await database.fetchrow(
            "SELECT user_id FROM users WHERE referrer_code = $1",
            code,
        )
        return record["user_id"] if record else None

    async def record_referral(self, referrer_id: int, referred_id: int) -> None:
        """Record new referral relationship."""
        # Prevent self-referral
        if referrer_id == referred_id:
            raise ValueError("Cannot refer oneself")

        # Check if already recorded
        existing = await database.fetchrow(
            "SELECT 1 FROM referrals WHERE referrer_id = $1 AND referred_id = $2",
            referrer_id,
            referred_id,
        )
        if existing:
            return  # Already recorded

        await database.execute(
            """
            INSERT INTO referrals (referrer_id, referred_id)
            VALUES ($1, $2)
            """,
            referrer_id,
            referred_id,
        )

    async def get_referrals(self, referrer_id: int) -> list[dict]:
        """Get list of users referred by this user."""
        records = await database.fetch(
            """
            SELECT u.*, r.referred_at
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = $1
            ORDER BY r.referred_at DESC
            """,
            referrer_id,
        )
        return [dict(r) for r in records]

    async def get_referral_count(self, referrer_id: int) -> int:
        """Get total number of referrals for a user."""
        record = await database.fetchval(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1",
            referrer_id,
        )
        return int(record) if record else 0

    async def get_referrer(self, referred_id: int) -> int | None:
        """Get the ID of who referred this user."""
        record = await database.fetchrow(
            "SELECT referrer_id FROM referrals WHERE referred_id = $1",
            referred_id,
        )
        return record["referrer_id"] if record else None
