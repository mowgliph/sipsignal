"""
Captura de gráficos con indicadores opcionales.
"""

import asyncio
import time
from functools import partial

import aiohttp
import matplotlib

from bot.core.config import SCREENSHOT_API_KEY
from bot.infrastructure.binance.binance_adapter import BinanceAdapter
from bot.utils.logger import logger

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


class ChartCapture:
    def __init__(self):
        self.data_fetcher = BinanceAdapter()
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        await self.data_fetcher.close()

    def _get_cache_key(
        self,
        symbol: str,
        timeframe: str,
        show_ema: bool,
        show_bb: bool,
        show_rsi: bool,
        show_pivots: bool,
    ) -> str:
        """Generate cache key including indicator state."""
        ema = "T" if show_ema else "F"
        bb = "T" if show_bb else "F"
        rsi = "T" if show_rsi else "F"
        piv = "T" if show_pivots else "F"
        return f"{symbol}_{timeframe}_ema:{ema}_bb:{bb}_rsi:{rsi}_piv:{piv}"

    def _get_from_cache(
        self,
        symbol: str,
        timeframe: str,
        show_ema: bool,
        show_bb: bool,
        show_rsi: bool,
        show_pivots: bool,
    ) -> bytes | None:
        key = self._get_cache_key(symbol, timeframe, show_ema, show_bb, show_rsi, show_pivots)
        entry = _cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < CACHE_TTL:
            return entry["data"]
        return None

    def _set_cache(
        self,
        symbol: str,
        timeframe: str,
        show_ema: bool,
        show_bb: bool,
        show_rsi: bool,
        show_pivots: bool,
        data: bytes,
    ):
        key = self._get_cache_key(symbol, timeframe, show_ema, show_bb, show_rsi, show_pivots)
        _cache[key] = {"data": data, "timestamp": time.time()}

    def _generate_candlestick_chart(
        self,
        df,
        symbol: str = "BTCUSDT",
        timeframe: str = "4h",
        show_ema: bool = False,
        show_bb: bool = False,
        show_rsi: bool = False,
        show_pivots: bool = False,
    ) -> bytes | None:
        """Generate chart using local chart generator."""
        from bot.utils.chart_generator import generate_ohlcv_chart

        buf = generate_ohlcv_chart(
            df=df,
            symbol=symbol,
            timeframe=timeframe,
            show_ema=show_ema,
            show_bb=show_bb,
            show_rsi=show_rsi,
            show_pivots=show_pivots,
            candles=80,
        )
        if buf is None:
            return None
        return buf.getvalue()

    async def _capture_with_matplotlib(
        self,
        symbol: str,
        timeframe: str,
        show_ema: bool,
        show_bb: bool,
        show_rsi: bool,
        show_pivots: bool,
    ) -> bytes | None:
        """Capture chart using matplotlib with async executor."""
        try:
            df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
            if df is None or df.empty:
                logger.warning(f"No se pudieron obtener datos OHLCV para {symbol}")
                return None

            # Execute chart generation in thread pool to avoid blocking asyncio
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                partial(
                    self._generate_candlestick_chart,
                    df,
                    symbol,
                    timeframe,
                    show_ema,
                    show_bb,
                    show_rsi,
                    show_pivots,
                ),
            )
            return data

        except Exception as e:
            logger.warning(f"Error generando gráfico con matplotlib: {e}")
            return None

    async def _capture_with_api(self, symbol: str, timeframe: str) -> bytes | None:
        """Fallback to screenshot API (deprecated)."""
        if not SCREENSHOT_API_KEY:
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
                    "Authorization": f"Bearer {SCREENSHOT_API_KEY}",
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

    async def capture(
        self,
        symbol: str,
        timeframe: str,
        show_ema: bool = False,
        show_bb: bool = False,
        show_rsi: bool = False,
        show_pivots: bool = False,
    ) -> bytes | None:
        """
        Capture chart with optional indicators.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "4h")
            show_ema: Show EMA 20/50/200
            show_bb: Show Bollinger Bands
            show_rsi: Show RSI panel
            show_pivots: Show pivot levels
        """
        cached = self._get_from_cache(symbol, timeframe, show_ema, show_bb, show_rsi, show_pivots)
        if cached:
            return cached

        data = await self._capture_with_matplotlib(
            symbol, timeframe, show_ema, show_bb, show_rsi, show_pivots
        )
        if not data:
            data = await self._capture_with_api(symbol, timeframe)

        if data:
            self._set_cache(symbol, timeframe, show_ema, show_bb, show_rsi, show_pivots, data)

        return data
