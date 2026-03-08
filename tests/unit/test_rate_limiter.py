"""Tests for rate_limiter module."""

import asyncio

import pytest

from bot.utils.rate_limiter import (
    AdminNotificationRateLimiter,
    AdminRateLimiter,
    RateLimiter,
)


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_rate_limiter_creation():
    """Test rate limiter can be created."""
    limiter = RateLimiter(max_requests=5, time_window=60)
    assert limiter.max_requests == 5
    assert limiter.time_window == 60


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests():
    """Test rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=3, time_window=1)

    # Should allow 3 requests
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess():
    """Test rate limiter blocks excess requests."""
    limiter = RateLimiter(max_requests=2, time_window=1)

    await limiter.acquire()
    await limiter.acquire()

    # Third request should return False
    result = await limiter.try_acquire()
    assert result is False


def test_admin_rate_limiter_singleton():
    """Test admin rate limiter is singleton."""
    # Reset singleton for test
    AdminRateLimiter._instance = None

    r1 = AdminRateLimiter.get_instance()
    r2 = AdminRateLimiter.get_instance()
    assert r1 is r2


def test_admin_notification_rate_limiter_singleton():
    """Test admin notification rate limiter is singleton."""
    # Reset singleton for test
    AdminNotificationRateLimiter._instance = None

    r1 = AdminNotificationRateLimiter.get_instance()
    r2 = AdminNotificationRateLimiter.get_instance()
    assert r1 is r2
