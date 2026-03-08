# ScreenshotAdapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar ScreenshotAdapter que hereda de ChartPort en bot/infrastructure/telegram/

**Architecture:** Crear nueva clase ScreenshotAdapter que reimplementa la lógica de ChartCapture como adapter de ChartPort

**Tech Stack:** Python 3.13+, aiohttp, matplotlib, pytest

---

### Task 1: Crear ScreenshotAdapter

**Files:**
- Create: `bot/infrastructure/telegram/screenshot_adapter.py`
- Reference: `bot/domain/ports/chart_port.py`
- Reference: `bot/trading/chart_capture.py`

**Step 1: Escribir el test**

```python
# tests/unit/test_screenshot_adapter.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestScreenshotAdapter:
    def test_hereda_de_chart_port(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        from bot.domain.ports.chart_port import ChartPort
        assert issubclass(ScreenshotAdapter, ChartPort)

    def test_constructor_con_api_key(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        adapter = ScreenshotAdapter(api_key="test_key_123")
        assert adapter.api_key == "test_key_123"

    def test_constructor_fallback_a_config(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        with patch('bot.infrastructure.telegram.screenshot_adapter.SCREENSHOT_API_KEY', 'config_key'):
            adapter = ScreenshotAdapter()
            assert adapter.api_key == "config_key"

    def test_constructor_api_key_sobreescribe_config(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        with patch('bot.infrastructure.telegram.screenshot_adapter.SCREENSHOT_API_KEY', 'config_key'):
            adapter = ScreenshotAdapter(api_key="override_key")
            assert adapter.api_key == "override_key"

    @pytest.mark.asyncio
    async def test_capture_retorna_none_en_error(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        adapter = ScreenshotAdapter(api_key="test")
        with patch.object(adapter, '_capture_with_matplotlib', new_callable=AsyncMock) as mock_mpl:
            mock_mpl.return_value = None
            with patch.object(adapter, '_capture_with_api', new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = Exception("API Error")
                result = await adapter.capture("BTCUSDT", "4h")
                assert result is None

    @pytest.mark.asyncio
    async def test_close_cierra_recursos(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
        adapter = ScreenshotAdapter(api_key="test")
        mock_session = AsyncMock()
        mock_session.closed = False
        adapter.session = mock_session
        adapter.data_fetcher = AsyncMock()
        
        await adapter.close()
        
        mock_session.close.assert_called_once()
        adapter.data_fetcher.close.assert_called_once()
```

**Step 2: Ejecutar test para verificar que falla**

Run: `pytest tests/unit/test_screenshot_adapter.py -v`
Expected: FAIL (archivo no existe)

**Step 3: Implementar ScreenshotAdapter**

```python
"""
ScreenshotAdapter - Implementación de ChartPort para captura de gráficos.
"""

import io
import time
from dataclasses import dataclass

import aiohttp
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from loguru import logger

from bot.core.config import SCREENSHOT_API_KEY
from bot.domain.ports.chart_port import ChartPort
from bot.trading.data_fetcher import BinanceDataFetcher

matplotlib.use("Agg")

TF_MAP = {
    "1d": "D",
    "4h": "240",
    "1h": "60",
    "15m": "15",
}

CACHE_TTL = 300

_cache: dict[str, dict] = {}

COLOR_UP = "#26a69a"
COLOR_DOWN = "#ef5350"
COLOR_BG = "#000000"
COLOR_GRID = "#333333"
COLOR_TEXT = "#d1d4dc"


class ScreenshotAdapter(ChartPort):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key else SCREENSHOT_API_KEY
        self.data_fetcher = BinanceDataFetcher()
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self) -> None:
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception:
            pass
        try:
            await self.data_fetcher.close()
        except Exception:
            pass

    def _get_cache_key(self, symbol: str, timeframe: str) -> str:
        return f"{symbol}_{timeframe}"

    def _get_from_cache(self, symbol: str, timeframe: str) -> bytes | None:
        key = self._get_cache_key(symbol, timeframe)
        entry = _cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < CACHE_TTL:
            return entry["data"]
        return None

    def _set_cache(self, symbol: str, timeframe: str, data: bytes):
        key = self._get_cache_key(symbol, timeframe)
        _cache[key] = {"data": data, "timestamp": time.time()}

    def _generate_candlestick_chart(self, df) -> bytes:
        fig, (ax_price, ax_volume) = plt.subplots(
            2, 1, figsize=(12, 8), height_ratios=[3, 1], facecolor=COLOR_BG, edgecolor=COLOR_BG
        )
        fig.subplots_adjust(hspace=0.1)

        for ax in [ax_price, ax_volume]:
            ax.set_facecolor(COLOR_BG)
            ax.tick_params(colors=COLOR_TEXT)
            ax.spines["bottom"].set_color(COLOR_GRID)
            ax.spines["top"].set_color(COLOR_BG)
            ax.spines["left"].set_color(COLOR_GRID)
            ax.spines["right"].set_color(COLOR_BG)
            ax.xaxis.label.set_color(COLOR_TEXT)
            ax.yaxis.label.set_color(COLOR_TEXT)
            ax.grid(True, color=COLOR_GRID, alpha=0.3)

        dates = mdates.date2num(df.index.to_pydatetime())
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        volumes = df["volume"].values

        for _i, (date, o, h, low_price, c, v) in enumerate(
            zip(dates, opens, highs, lows, closes, volumes, strict=False)
        ):
            color = COLOR_UP if c >= o else COLOR_DOWN

            ax_price.plot([date, date], [low_price, h], color=color, linewidth=0.8)
            ax_price.plot([date - 0.3, date + 0.3], [o, o], color=color, linewidth=0.8)
            ax_price.plot([date - 0.3, date + 0.3], [c, c], color=color, linewidth=0.8)

            ax_volume.bar(date, v, width=0.6, color=color, alpha=0.7)

        ax_price.set_ylabel("Price", color=COLOR_TEXT)
        ax_price.set_xlabel("")
        ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax_price.tick_params(axis="x", rotation=45)

        ax_volume.set_ylabel("Volume", color=COLOR_TEXT)
        ax_volume.set_xlabel("Date", color=COLOR_TEXT)
        ax_volume.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax_volume.tick_params(axis="x", rotation=45)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor=COLOR_BG, dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    async def _capture_with_matplotlib(self, symbol: str, timeframe: str) -> bytes | None:
        try:
            df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
            if df is None or df.empty:
                logger.warning(f"No se pudieron obtener datos OHLCV para {symbol}")
                return None

            return self._generate_candlestick_chart(df)

        except Exception as e:
            logger.warning(f"Error generando gráfico con matplotlib: {e}")
            return None

    async def _capture_with_api(self, symbol: str, timeframe: str) -> bytes | None:
        if not self.api_key:
            logger.warning("SCREENSHOT_API_KEY no configurada")
            return None

        try:
            tv_interval = TF_MAP.get(timeframe, timeframe)

            cache_buster = str(int(time.time() * 1000))
            chart_url = f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}&interval={tv_interval}&__cb={cache_buster}"

            session = await self._get_session()
            async with session.post(
                "https://api.screenshot-api.org/api/v1/screenshot",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": chart_url,
                    "viewport": {"width": 1200, "height": 800},
                    "format": "png",
                    "fullPage": False,
                    "blockAds": True,
                    "darkMode": True,
                    "cache": False,
                    "staleTTL": 0,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", {})
                    screenshot_url = data.get("screenshotUrl")
                    if result.get("success") and screenshot_url:
                        async with session.get(screenshot_url) as img_response:
                            img_bytes = await img_response.read()
                            if len(img_bytes) > 100:
                                return img_bytes
                            else:
                                logger.warning(
                                    f"API screenshot returned empty image: {len(img_bytes)} bytes"
                                )
                                return None
                    else:
                        logger.warning(f"API screenshot returned error: {result}")
                        return None
                else:
                    logger.warning(f"HTTP error en screenshot API: {response.status}")
                    return None

        except TimeoutError:
            logger.warning("Timeout en screenshot API")
            return None
        except Exception as e:
            logger.warning(f"Error en screenshot API: {e}")
            return None

    async def capture(self, symbol: str, timeframe: str) -> bytes | None:
        try:
            cached = self._get_from_cache(symbol, timeframe)
            if cached:
                return cached

            data = await self._capture_with_matplotlib(symbol, timeframe)
            if not data:
                data = await self._capture_with_api(symbol, timeframe)

            if data:
                self._set_cache(symbol, timeframe, data)

            return data
        except Exception as e:
            logger.warning(f"Error en capture: {e}")
            return None
```

**Step 4: Ejecutar test para verificar que pasa**

Run: `pytest tests/unit/test_screenshot_adapter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/infrastructure/telegram/screenshot_adapter.py tests/unit/test_screenshot_adapter.py
git commit -m "feat: add ScreenshotAdapter implementing ChartPort"
```

---

### Task 2: Verificar que tests existentes pasan

**Step 1: Ejecutar todos los tests**

Run: `pytest --tb=short`
Expected: Todos los tests pasan

**Step 2: Si hay errores, resolverlos**

Fix any failing tests related to this change

---

**Plan complete and saved to `docs/plans/2026-03-07-screenshot-adapter-plan.md`. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
