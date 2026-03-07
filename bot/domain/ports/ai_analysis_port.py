from abc import ABC, abstractmethod

from bot.domain.signal import Signal


class AIAnalysisPort(ABC):
    @abstractmethod
    async def analyze_signal(self, signal: Signal) -> str: ...

    @abstractmethod
    async def analyze_scenario(self, context: str) -> str: ...
