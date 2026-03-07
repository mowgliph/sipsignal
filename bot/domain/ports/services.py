from abc import ABC, abstractmethod
from typing import Any

from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig


class MarketDataPort(ABC):
    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Any: ...


class ChartPort(ABC):
    @abstractmethod
    async def capture(self, symbol: str, timeframe: str) -> bytes | None: ...


class AIAnalysisPort(ABC):
    @abstractmethod
    async def analyze_signal(self, signal: Signal) -> str: ...

    @abstractmethod
    async def analyze_scenario(self) -> str: ...


class NotifierPort(ABC):
    @abstractmethod
    async def send_signal(
        self,
        chat_id: int,
        signal: Signal,
        chart: bytes | None,
        ai_context: str,
        user_config: UserConfig,
    ) -> None: ...

    @abstractmethod
    async def send_message(self, chat_id: int, text: str) -> None: ...

    @abstractmethod
    async def send_warning(self, chat_id: int, text: str) -> None: ...
