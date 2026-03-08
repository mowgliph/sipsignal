"""Rate limiting utilities using aiolimiter."""

import asyncio

from aiolimiter import AsyncLimiter


class RateLimiter:
    """
    Async rate limiter wrapper using aiolimiter.

    Provides simple async rate limiting with configurable
    max requests and time window.
    """

    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._limiter = AsyncLimiter(max_requests, time_window)

    async def acquire(self) -> None:
        """Acquire rate limit slot, waiting if necessary."""
        await self._limiter.acquire()

    async def try_acquire(self) -> bool:
        """
        Try to acquire rate limit slot without waiting.

        Uses asyncio.wait_for with a minimal timeout to check if
        the slot is available immediately.

        Returns:
            True if acquired, False if rate limited
        """
        try:
            # Try to acquire with minimal wait (0.001 seconds)
            # This will fail quickly if rate limited
            await asyncio.wait_for(self._limiter.acquire(), timeout=0.001)
            return True
        except TimeoutError:
            return False
        except Exception:
            return False

    def reset(self) -> None:
        """Reset the rate limiter."""
        self._limiter = AsyncLimiter(self.max_requests, self.time_window)


class AdminRateLimiter:
    """
    Singleton rate limiter for admin commands.

    Limits admin commands to prevent abuse.
    """

    _instance: RateLimiter | None = None

    @classmethod
    def get_instance(cls) -> RateLimiter:
        """Get singleton instance of admin rate limiter."""
        if cls._instance is None:
            # 5 requests per minute for admin commands
            cls._instance = RateLimiter(max_requests=5, time_window=60)
        return cls._instance


class AdminNotificationRateLimiter:
    """
    Singleton rate limiter for admin notifications.

    Limits notifications to admins to prevent spam.
    """

    _instance: RateLimiter | None = None

    @classmethod
    def get_instance(cls) -> RateLimiter:
        """Get singleton instance of notification rate limiter."""
        if cls._instance is None:
            # 1 request per 10 seconds for admin notifications
            cls._instance = RateLimiter(max_requests=1, time_window=10)
        return cls._instance
