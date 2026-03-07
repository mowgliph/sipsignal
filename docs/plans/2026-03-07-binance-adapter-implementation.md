# BinanceAdapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear `BinanceAdapter` que implemente `MarketDataPort` para obtener datos OHLCV de Binance.

**Architecture:** Adapter que hereda de `MarketDataPort` y reimplementa `get_ohlcv()` con la misma lógica de `BinanceDataFetcher`.

**Tech Stack:** Python, aiohttp, pandas, loguru

---

### Task 1: Create BinanceAdapter class

**Files:**
- Create: `bot/infrastructure/binance/binance_adapter.py`
- Reference: `bot/trading/data_fetcher.py`
- Reference: `bot/domain/ports/market_data_port.py`

**Step 1: Write the implementation**

Create `bot/infrastructure/binance/binance_adapter.py` with:

```python
import asyncio
from datetime import datetime, timedelta

import aiohttp
import pandas as pd
from loguru import logger

from bot.domain.ports.market_data_port import MarketDataPort

BINANCE_BASE_URL = "https://data-api.binance.vision/api/v3"

INTERVAL_DURATIONS = {
    "1d": timedelta(days=1),
    "4h": timedelta(hours=4),
    "1h": timedelta(hours=1),
    "15m": timedelta(minutes=15),
}


class BinanceAdapter(MarketDataPort):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request_with_retry(self, url: str, params: dict, max_retries: int = 3) -> list:
        delays = [2, 4, 8]
        session = await self._get_session()

        for attempt in range(max_retries):
            start_time = asyncio.get_event_loop().time()
            try:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                    logger.info(
                        f"GET {url} params={params} - {response.status} - {latency_ms:.2f}ms"
                    )

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        wait_time = delays[attempt] if attempt < len(delays) else 8
                        logger.warning(f"Rate limited, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info,
                            response.history,
                            status=response.status,
                        )
            except TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1}/{max_retries}: {e}")

            if attempt < max_retries - 1:
                wait_time = delays[attempt] if attempt < len(delays) else 8
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise Exception(f"Failed after {max_retries} attempts")

    def _exclude_open_candle(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        if df.empty:
            return df

        duration = INTERVAL_DURATIONS.get(timeframe)
        if not duration:
            return df

        last_timestamp = df.index[-1]
        if last_timestamp + duration > datetime.utcnow():
            logger.info(f"Excluding open candle at {last_timestamp}")
            return df.iloc[:-1]

        return df

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        if timeframe not in INTERVAL_DURATIONS:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. Use: {list(INTERVAL_DURATIONS.keys())}"
            )

        url = f"{BINANCE_BASE_URL}/klines"
        params = {"symbol": symbol.upper(), "interval": timeframe, "limit": limit}

        data = await self._request_with_retry(url, params)

        df = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "num_trades",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore",
            ],
        )

        df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df.astype(
            {
                "open": "float64",
                "high": "float64",
                "low": "float64",
                "close": "float64",
                "volume": "float64",
            }
        )

        df = self._exclude_open_candle(df, timeframe)

        return df
```

**Step 2: Run linter to verify code**

Run: `ruff check bot/infrastructure/binance/binance_adapter.py`
Expected: No errors

**Step 3: Run formatter**

Run: `ruff format bot/infrastructure/binance/binance_adapter.py`
Expected: Formatted file

**Step 4: Verify imports work**

Run: `python -c "from bot.infrastructure.binance.binance_adapter import BinanceAdapter; print('OK')"`
Expected: OK

---

### Task 2: Verify MarketDataPort implementation

**Files:**
- Test: `bot/infrastructure/binance/binance_adapter.py`

**Step 1: Verify inheritance**

Run: `python -c "from bot.infrastructure.binance.binance_adapter import BinanceAdapter; from bot.domain.ports.market_data_port import MarketDataPort; assert issubclass(BinanceAdapter, MarketDataPort); print('BinanceAdapter implements MarketDataPort')"`
Expected: BinanceAdapter implements MarketDataPort

---

## Plan Complete

Two execution options:

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
