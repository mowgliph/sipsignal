from abc import ABC, abstractmethod

import pandas as pd


class MarketDataPort(ABC):
    @abstractmethod
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame: ...
