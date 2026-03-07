from abc import ABC, abstractmethod


class ChartPort(ABC):
    @abstractmethod
    async def capture(self, symbol: str, timeframe: str) -> bytes | None: ...

    @abstractmethod
    async def close(self) -> None: ...
