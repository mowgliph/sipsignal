"""
Captura de gráficos TradingView.
"""

import io
import time

import aiohttp
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from loguru import logger

from core.config import SCREENSHOT_API_KEY
from trading.data_fetcher import BinanceDataFetcher

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
        self.data_fetcher = BinanceDataFetcher()
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        await self.data_fetcher.close()

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
        if not SCREENSHOT_API_KEY:
            logger.warning("SCREENSHOT_API_KEY no configurada")
            return None

        try:
            tv_interval = TF_MAP.get(timeframe, timeframe)
            import time

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

    async def capture(self, symbol: str, timeframe: str) -> bytes | None:
        cached = self._get_from_cache(symbol, timeframe)
        if cached:
            return cached

        data = await self._capture_with_matplotlib(symbol, timeframe)
        if not data:
            data = await self._capture_with_api(symbol, timeframe)

        if data:
            self._set_cache(symbol, timeframe, data)

        return data
