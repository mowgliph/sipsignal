from abc import ABC, abstractmethod

from bot.domain.active_trade import ActiveTrade
from bot.domain.drawdown_state import DrawdownState
from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig


class SignalRepository(ABC):
    @abstractmethod
    async def save(self, signal: Signal) -> Signal: ...

    @abstractmethod
    async def get_by_id(self, signal_id: int) -> Signal | None: ...

    @abstractmethod
    async def get_recent(self, limit: int) -> list[Signal]: ...

    @abstractmethod
    async def update_status(self, signal_id: int, status: str) -> None: ...


class ActiveTradeRepository(ABC):
    @abstractmethod
    async def save(self, trade: ActiveTrade) -> ActiveTrade: ...

    @abstractmethod
    async def get_active(self) -> ActiveTrade | None: ...

    @abstractmethod
    async def update(self, trade: ActiveTrade) -> None: ...

    @abstractmethod
    async def close(self, trade_id: int, status: str) -> None: ...


class UserConfigRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> UserConfig | None: ...

    @abstractmethod
    async def save(self, config: UserConfig) -> UserConfig: ...


class DrawdownRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> DrawdownState | None: ...

    @abstractmethod
    async def save(self, state: DrawdownState) -> DrawdownState: ...

    @abstractmethod
    async def reset(self, user_id: int) -> DrawdownState: ...


class UserRepository(ABC):
    """Repository protocol for user data operations.

    Defines the interface for all user-related persistence operations,
    including access control and user management.
    """

    @abstractmethod
    async def get(self, user_id: int) -> dict | None:
        """Get a user by their ID.

        Args:
            user_id: The Telegram user ID.

        Returns:
            User dictionary if found, None otherwise.
        """
        ...

    @abstractmethod
    async def save(self, user: dict) -> None:
        """Save a user (create or update).

        Args:
            user: User dictionary with all fields.
        """
        ...

    @abstractmethod
    async def get_all(self) -> list[dict]:
        """Get all users.

        Returns:
            List of all user dictionaries.
        """
        ...

    @abstractmethod
    async def get_by_status(self, status: str) -> list[dict]:
        """Get users by status.

        Args:
            status: User status filter (e.g., 'pending', 'approved', 'admin', 'non_permitted').

        Returns:
            List of user dictionaries matching the status.
        """
        ...

    @abstractmethod
    async def update_last_seen(self, user_id: int) -> None:
        """Update the last_seen timestamp for a user.

        Args:
            user_id: The Telegram user ID.
        """
        ...

    @abstractmethod
    async def get_user_status(self, user_id: int) -> str | None:
        """Get user's access status.

        Args:
            user_id: The Telegram user ID.

        Returns:
            The user's status string or None if user not found.
        """
        ...

    @abstractmethod
    async def request_access(self, user_id: int) -> bool:
        """Mark user as pending and set requested_at timestamp.

        Args:
            user_id: The Telegram user ID.

        Returns:
            True if successful, False if user not found.
        """
        ...

    @abstractmethod
    async def approve_user(self, user_id: int) -> bool:
        """Change user status to 'approved'.

        Args:
            user_id: The Telegram user ID.

        Returns:
            True if successful, False if user not found.
        """
        ...

    @abstractmethod
    async def deny_user(self, user_id: int) -> bool:
        """Change user status back to 'non_permitted'.

        Args:
            user_id: The Telegram user ID.

        Returns:
            True if successful, False if user not found.
        """
        ...

    @abstractmethod
    async def make_admin(self, user_id: int) -> bool:
        """Change user status to 'admin'.

        Args:
            user_id: The Telegram user ID.

        Returns:
            True if successful, False if user not found.
        """
        ...
