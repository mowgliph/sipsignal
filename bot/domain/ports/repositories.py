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
