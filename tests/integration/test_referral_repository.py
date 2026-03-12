"""Integration tests for PostgreSQLReferralRepository."""

import pytest

from bot.core import database
from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository


@pytest.mark.asyncio
async def test_generate_referrer_code():
    """Test code generation for user."""
    repo = PostgreSQLReferralRepository()

    # Create test user
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )

    try:
        code = await repo.generate_referrer_code(999001)
        assert len(code) == 8
        assert code.isalnum()

        # Should return same code on second call
        code2 = await repo.generate_referrer_code(999001)
        assert code == code2
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id = 999001")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


@pytest.mark.asyncio
async def test_get_by_code():
    """Test getting user by referral code."""
    repo = PostgreSQLReferralRepository()

    # Create test user
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )

    try:
        code = await repo.generate_referrer_code(999001)
        user_id = await repo.get_by_code(code)
        assert user_id == 999001
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id = 999001")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


@pytest.mark.asyncio
async def test_get_by_invalid_code():
    """Test getting user by invalid code returns None."""
    repo = PostgreSQLReferralRepository()

    user_id = await repo.get_by_code("INVALID123")
    assert user_id is None


@pytest.mark.asyncio
async def test_record_referral():
    """Test recording referral relationship."""
    repo = PostgreSQLReferralRepository()

    # Create test users
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999002,
    )

    try:
        await repo.generate_referrer_code(999001)
        await repo.record_referral(999001, 999002)

        count = await repo.get_referral_count(999001)
        assert count == 1
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id IN (999001, 999002)")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


@pytest.mark.asyncio
async def test_self_referral_blocked():
    """Test that self-referral is blocked."""
    repo = PostgreSQLReferralRepository()

    # Create test user
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )

    try:
        with pytest.raises(ValueError, match="Cannot refer oneself"):
            await repo.record_referral(999001, 999001)
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id = 999001")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


@pytest.mark.asyncio
async def test_get_referrals():
    """Test getting list of referrals."""
    repo = PostgreSQLReferralRepository()

    # Create test users
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999002,
    )

    try:
        await repo.generate_referrer_code(999001)
        await repo.record_referral(999001, 999002)

        referrals = await repo.get_referrals(999001)
        assert len(referrals) == 1
        assert referrals[0]["user_id"] == 999002
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id IN (999001, 999002)")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


@pytest.mark.asyncio
async def test_get_referrer():
    """Test getting referrer of a user."""
    repo = PostgreSQLReferralRepository()

    # Create test users
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999002,
    )

    try:
        await repo.generate_referrer_code(999001)
        await repo.record_referral(999001, 999002)

        referrer = await repo.get_referrer(999002)
        assert referrer == 999001
    finally:
        # Cleanup
        await database.execute("DELETE FROM users WHERE user_id IN (999001, 999002)")
        await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")
