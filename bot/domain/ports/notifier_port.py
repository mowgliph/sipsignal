from abc import ABC, abstractmethod

from bot.domain.signal import Signal


class NotifierPort(ABC):
    @abstractmethod
    async def send_signal(
        self, chat_id: int, signal: Signal, chart: bytes | None, ai_context: str
    ) -> None: ...
