"""
Captura de gráficos TradingView.
"""

import asyncio
import time
from typing import Dict, Optional

import aiohttp
from loguru import logger

from core.config import SCREENSHOT_API_KEY
from trading.data_fetcher import BinanceDataFetcher

TF_MAP = {
    "1d": "D",
    "4h": "240",
    "1h": "60",
    "15m": "15",
}

CACHE_TTL = 300

_cache: Dict[str, Dict] = {}


class ChartCapture:
    def __init__(self):
        self.data_fetcher = BinanceDataFetcher()
        self.session: Optional[aiohttp.ClientSession] = None

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

    def _get_from_cache(self, symbol: str, timeframe: str) -> Optional[bytes]:
        key = self._get_cache_key(symbol, timeframe)
        entry = _cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < CACHE_TTL:
            return entry["data"]
        return None

    def _set_cache(self, symbol: str, timeframe: str, data: bytes):
        key = self._get_cache_key(symbol, timeframe)
        _cache[key] = {"data": data, "timestamp": time.time()}

    async def _capture_with_lightweight(self, symbol: str, timeframe: str) -> Optional[bytes]:
        logger.warning("lightweight-charts deshabilitado temporalmente - usar fallback externo")
        return None

    async def _capture_with_api(self, symbol: str, timeframe: str) -> Optional[bytes]:
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
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get("data", {})
                    screenshot_url = data.get("screenshotUrl")
                    status = data.get("status")
                    logger.info(f"Screenshot API response: status={status}, url={screenshot_url}")
                    if result.get("success") and screenshot_url:
                        async with session.get(screenshot_url) as img_response:
                            img_bytes = await img_response.read()
                            logger.info(f"Downloaded image: {len(img_bytes)} bytes, content-type: {img_response.headers.get('content-type')}")
                            if len(img_bytes) > 100:
                                return img_bytes
                            else:
                                logger.warning(f"API screenshot returned empty image: {len(img_bytes)} bytes")
                                return None
                    else:
                        logger.warning(f"API screenshot returned error: {result}")
                        return None
                else:
                    logger.warning(f"HTTP error en screenshot API: {response.status}")
                    return None

        except asyncio.TimeoutError:
            logger.warning("Timeout en screenshot API")
            return None
        except Exception as e:
            logger.warning(f"Error en screenshot API: {e}")
            return None

    async def capture(self, symbol: str, timeframe: str) -> Optional[bytes]:
        cached = self._get_from_cache(symbol, timeframe)
        if cached:
            return cached

        data = await self._capture_with_lightweight(symbol, timeframe)
        if not data:
            data = await self._capture_with_api(symbol, timeframe)

        if data:
            self._set_cache(symbol, timeframe, data)

        return data
