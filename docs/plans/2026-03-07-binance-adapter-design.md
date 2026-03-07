# BinanceAdapter (MarketDataPort) - Design

**Date**: 2026-03-07
**Status**: Approved
**Task**: Implementar `BinanceAdapter` que implemente `MarketDataPort`

---

## Objective

Crear `bot/infrastructure/binance/binance_adapter.py` que implemente el puerto `MarketDataPort` definido en el dominio.

---

## Architecture

| Element | Details |
|---------|---------|
| File | `bot/infrastructure/binance/binance_adapter.py` |
| Class | `BinanceAdapter` |
| Base Class | `MarketDataPort` |
| Port Location | `bot.domain.ports.market_data_port.MarketDataPort` |

---

## Interface

```python
class BinanceAdapter(MarketDataPort):
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame: ...
```

---

## Implementation Details

### Method: `get_ohlcv(symbol, timeframe, limit)`

**Parameters:**
- `symbol`: Trading pair (e.g., "BTCUSDT")
- `timeframe`: Interval (e.g., "1h", "4h", "15m")
- `limit`: Number of candles (default: 200)

**Returns:**
- `pd.DataFrame` with columns: `open`, `high`, `low`, `close`, `volume`, `timestamp`

**Logic (identical to BinanceDataFetcher):**
1. Validate timeframe against `INTERVAL_DURATIONS`
2. Build URL: `https://data-api.binance.vision/api/v3/klines`
3. Execute request with retry logic
4. Parse response into DataFrame
5. Exclude open candle if applicable
6. Return formatted DataFrame

### Retry Logic
- Delays: `[2, 4, 8]` seconds (exponential backoff)
- Max retries: 3
- Handle HTTP 429 (rate-limit) specifically
- Timeout per request: 10 seconds

### Imports
```python
import asyncio
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from loguru import logger
from bot.domain.ports.market_data_port import MarketDataPort
```

---

## Constraints

- **DO NOT** modify `bot/trading/data_fetcher.py` (keep intact for now)
- Use `timeframe` parameter name for port consistency
- Maintain identical behavior to `BinanceDataFetcher.get_ohlcv()`

---

## Success Criteria

1. `BinanceAdapter` implements `MarketDataPort` interface
2. `get_ohlcv()` returns DataFrame with correct columns
3. Retry logic handles rate-limits (429) with exponential backoff
4. Open candle is excluded from results
5. All existing tests pass
