from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bot.domain.signal import Signal

if TYPE_CHECKING:
    from bot.trading.strategy_engine import UserConfig


class NotifierPort(ABC):
    @abstractmethod
    async def send_signal(
        self,
        bot,
        chat_id: int,
        signal: Signal,
        chart: bytes | None,
        ai_context: str,
        user_config: "UserConfig",
    ) -> None: ...

    @abstractmethod
    async def send_message(self, bot, chat_id: int, text: str) -> None: ...

    @abstractmethod
    async def send_warning(self, bot, chat_id: int, text: str) -> None: ...
