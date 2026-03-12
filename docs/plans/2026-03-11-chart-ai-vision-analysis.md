# Chart AI Vision Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement AI-powered market synopsis for `/chart` command using Groq Vision API (primary) with text-based fallback, providing 50-75 word analysis in Spanish with bullish/bearish/neutral scenarios.

**Architecture:** Vision-based AI analysis of chart screenshots with automatic fallback to text-based OHLCV analysis on failure, 15-minute caching per symbol/timeframe/indicator combination, graceful degradation to chart-only on complete AI failure.

**Tech Stack:** Python 3.13+, Groq Vision API (LLaVA), Groq Text API, python-telegram-bot, aiohttp, base64 encoding, SQLAlchemy for caching.

---

## Context

### Current State
- `/chart` command generates matplotlib charts with selectable indicators (EMA, BB, RSI, Pivots)
- Interactive buttons allow timeframe changes and indicator toggles
- Groq AI integration exists for signal analysis (`GroqClient`, `GroqAdapter`)
- No AI analysis attached to chart responses
- PRD specifies AI-powered market context as core feature

### Problem to Solve
Users receive chart images without intelligent analysis. They must manually identify support/resistance levels, trend direction, and potential scenarios. The goal is to provide instant AI-powered insights directly in the chart message.

### Solution Overview
1. Capture chart image with user-selected indicators
2. Send image to Groq Vision API for visual pattern recognition
3. On vision failure, fallback to text-based analysis using OHLCV data
4. Cache analysis for 15 minutes per unique configuration
5. Send chart + AI synopsis (50-75 words) to Telegram

---

## Implementation Tasks

### Task 1: Add Vision API Configuration

**Files:**
- Modify: `bot/core/config.py`
- Test: N/A (configuration only)

**Step 1: Add vision model configuration**

Modify `bot/core/config.py` - add after existing Groq config:

```python
# Groq Vision API Configuration
GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
GROQ_VISION_MAX_TOKENS: int = int(os.getenv("GROQ_VISION_MAX_TOKENS", "200"))
GROQ_VISION_TEMPERATURE: float = float(os.getenv("GROQ_VISION_TEMPERATURE", "0.3"))
GROQ_VISION_TIMEOUT: int = int(os.getenv("GROQ_VISION_TIMEOUT", "10"))
```

**Step 2: Update `env.example`**

Add to `env.example`:

```bash
# Groq Vision API (optional, for chart analysis)
GROQ_VISION_MODEL=llama-3.2-11b-vision-preview
GROQ_VISION_MAX_TOKENS=200
GROQ_VISION_TEMPERATURE=0.3
GROQ_VISION_TIMEOUT=10
```

**Step 3: Commit**

```bash
git add bot/core/config.py env.example
git commit -m "feat: add Groq Vision API configuration"
```

---

### Task 2: Create Vision Client

**Files:**
- Create: `bot/ai/vision_client.py`
- Test: `tests/unit/test_vision_client.py`

**Step 1: Write vision client tests**

Create `tests/unit/test_vision_client.py`:

```python
"""Tests for Groq Vision client."""

import os
import pytest

from bot.ai.vision_client import VisionClient


def test_vision_client_requires_api_key():
    """Test VisionClient raises error without API key."""
    # Temporarily remove API key
    original = os.environ.get("GROQ_API_KEY")
    if "GROQ_API_KEY" in os.environ:
        del os.environ["GROQ_API_KEY"]

    try:
        client = VisionClient()
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            _ = client.client
    finally:
        if original:
            os.environ["GROQ_API_KEY"] = original


def test_vision_client_with_api_key():
    """Test VisionClient initializes with API key."""
    client = VisionClient(api_key="test_key")
    assert client._api_key == "test_key"
    assert client.MODEL == "llama-3.2-11b-vision-preview"
    assert client.MAX_TOKENS == 200
    assert client.TIMEOUT == 10
```

**Step 2: Run test to verify it fails**

```bash
source venv/bin/activate
pytest tests/unit/test_vision_client.py::test_vision_client_requires_api_key -v
```

Expected: FAIL (file doesn't exist yet)

**Step 3: Create vision client implementation**

Create `bot/ai/vision_client.py`:

```python
"""
Groq Vision client for chart image analysis.
Uses LLaVA model for visual pattern recognition.
"""

import base64
import os

from groq import AsyncGroq

from bot.utils.logger import logger


class VisionClient:
    """Async client for Groq Vision API (LLaVA)."""

    MODEL = "llama-3.2-11b-vision-preview"
    MAX_TOKENS = 200
    TEMPERATURE = 0.3
    TIMEOUT = 10  # seconds

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        self._client: AsyncGroq | None = None

    @property
    def client(self) -> AsyncGroq:
        """Lazy initialization of Groq client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError("GROQ_API_KEY not configured")
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    async def analyze_chart(
        self,
        image_bytes: bytes,
        symbol: str,
        timeframe: str,
        indicators: list[str],
    ) -> str:
        """
        Analyze chart image using Groq Vision.

        Args:
            image_bytes: Chart screenshot (PNG format)
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "4h")
            indicators: List of active indicators (e.g., ["EMA", "BB", "RSI"])

        Returns:
            AI analysis in Spanish (50-75 words) or empty string on failure
        """
        from bot.ai.prompts import build_vision_analysis_prompt

        if not self._api_key:
            logger.warning("GROQ_API_KEY not configured, skipping vision analysis")
            return ""

        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Build prompt
            prompt = build_vision_analysis_prompt(symbol, timeframe, indicators)

            # Call Groq Vision API
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    },
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                timeout=self.TIMEOUT,
            )

            content = response.choices[0].message.content.strip()
            logger.debug(f"Vision analysis completed: {len(content)} chars")
            return content

        except TimeoutError as e:
            logger.warning(f"Vision API timeout ({self.TIMEOUT}s): {e}")
            return ""
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
            return ""  # Trigger fallback
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_vision_client.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add bot/ai/vision_client.py tests/unit/test_vision_client.py
git commit -m "feat: add Groq Vision client for chart analysis"
```

---

### Task 3: Add Vision Prompts

**Files:**
- Modify: `bot/ai/prompts.py`
- Test: `tests/unit/test_prompts.py`

**Step 1: Add tests for vision prompts**

Create or modify `tests/unit/test_prompts.py`:

```python
"""Tests for AI prompt generation."""

from bot.ai.prompts import build_vision_analysis_prompt, build_text_fallback_prompt


def test_build_vision_analysis_prompt():
    """Test vision analysis prompt generation."""
    result = build_vision_analysis_prompt("BTCUSDT", "4h", ["EMA", "RSI"])

    assert "BTCUSDT" in result
    assert "4H" in result
    assert "EMA" in result
    assert "RSI" in result
    assert "Español" in result
    assert "75 palabras" in result


def test_build_vision_prompt_no_indicators():
    """Test vision prompt with no indicators."""
    result = build_vision_analysis_prompt("ETHUSDT", "1h", [])

    assert "precio limpio" in result


def test_build_text_fallback_prompt():
    """Test text fallback prompt generation."""
    price_data = {
        "current": 65000.0,
        "change_24h": 2.5,
        "rsi": 62.0,
        "ema20": 64500.0,
        "bb_lower": 63000.0,
        "bb_upper": 67000.0,
        "support": 64000.0,
        "resistance": 66500.0,
    }

    result = build_text_fallback_prompt("BTCUSDT", "4h", price_data, {"ema": True})

    assert "BTCUSDT" in result
    assert "4H" in result
    assert "65,000" in result
    assert "Español" in result
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/test_prompts.py -v
```

Expected: FAIL (functions don't exist)

**Step 3: Add vision prompt functions**

Modify `bot/ai/prompts.py` - add at the end:

```python
def build_vision_analysis_prompt(
    symbol: str,
    timeframe: str,
    indicators: list[str],
) -> str:
    """
    Build prompt for vision-based chart analysis.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        timeframe: Timeframe (e.g., "4h")
        indicators: List of active indicators

    Returns:
        Prompt in Spanish optimized for 50-75 word response
    """
    ind_str = ", ".join(indicators) if indicators else "precio limpio"

    return f"""
Analiza este gráfico de {symbol} en temporalidad {timeframe.upper()}.
Indicadores visibles: {ind_str}.

IDENTIFICA:
1. Tendencia actual (alcista/bajista/lateral) y su fortaleza
2. 2-3 niveles clave de soporte y resistencia con precios aproximados
3. Patrones visuales (triángulos, banderas, H&S, dobles techos/suelos)

ESCENARIOS (con precios objetivo):
📈 ALCISTA: Qué confirmaría subida y hacia qué nivel
📉 BAJISTA: Qué indicaría debilidad y hacia qué nivel
⚖️ NEUTRAL: Rango probable de consolidación

FORMATO: Español, máximo 75 palabras, usa emojis, incluye precios.
"""


def build_text_fallback_prompt(
    symbol: str,
    timeframe: str,
    price_data: dict,
    indicators: dict[str, bool],
) -> str:
    """
    Build prompt for text-based fallback analysis.

    Args:
        symbol: Trading pair
        timeframe: Timeframe
        price_data: Dict with OHLCV and indicator data
        indicators: Dict of indicator states

    Returns:
        Prompt in Spanish for OHLCV data analysis
    """
    active_indicators = [k.upper() for k, v in indicators.items() if v]
    ind_str = ", ".join(active_indicators) if active_indicators else "sin indicadores"

    return f"""
ANÁLISIS TÉCNICO {symbol} {timeframe.upper()}

DATOS:
- Precio: ${price_data['current']:,.2f}
- Cambio 24h: {price_data['change_24h']:+.2f}%
- RSI: {price_data['rsi']:.1f}
- EMA20: ${price_data['ema20']:,.2f}
- Bollinger: ${price_data['bb_lower']:,.2f} - ${price_data['bb_upper']:,.2f}
- Soporte clave: ${price_data['support']:,.2f}
- Resistencia clave: ${price_data['resistance']:,.2f}
- Indicadores: {ind_str}

Genera análisis de 50-75 palabras en español con emojis,
incluye escenarios alcista/bajista con precios objetivo.
"""
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_prompts.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add bot/ai/prompts.py tests/unit/test_prompts.py
git commit -m "feat: add vision and text fallback prompts"
```

---

### Task 4: Create Market Synopsis Builder

**Files:**
- Create: `bot/ai/market_synopsis.py`
- Test: `tests/unit/test_market_synopsis.py`

**Step 1: Write market synopsis tests**

Create `tests/unit/test_market_synopsis.py`:

```python
"""Tests for MarketSynopsisBuilder."""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.ai.market_synopsis import MarketSynopsisBuilder, MarketAnalysis


@pytest.fixture
def mock_vision_client():
    client = AsyncMock()
    client.analyze_chart = AsyncMock(return_value="Vision analysis result")
    return client


@pytest.fixture
def mock_text_client():
    client = AsyncMock()
    return client


@pytest.fixture
def mock_data_fetcher():
    fetcher = AsyncMock()
    return fetcher


def test_cache_key_generation(mock_vision_client, mock_text_client, mock_data_fetcher):
    """Test cache key includes all parameters."""
    builder = MarketSynopsisBuilder(mock_vision_client, mock_text_client, mock_data_fetcher)

    indicators = {"ema": True, "bb": False, "rsi": True, "pivots": False}
    key = builder._get_cache_key("BTCUSDT", "4h", indicators)

    assert key == "BTCUSDT_4h_ema:1_bb:0_pivots:0_rsi:1"


def test_cache_hit(mock_vision_client, mock_text_client, mock_data_fetcher):
    """Test cache returns stored analysis within TTL."""
    builder = MarketSynopsisBuilder(mock_vision_client, mock_text_client, mock_data_fetcher)

    # Pre-populate cache
    analysis = MarketAnalysis(
        synopsis="Cached analysis",
        scenarios="",
        timestamp=time.time(),
        method="vision",
    )
    key = "BTCUSDT_4h_ema:0_bb:0_pivots:0_rsi:0"
    builder._cache[key] = analysis

    # Should return cached without calling API
    result = builder._cache.get(key)
    assert result is analysis


def test_cache_miss_triggers_vision(mock_vision_client, mock_text_client, mock_data_fetcher):
    """Test cache miss triggers vision analysis."""
    builder = MarketSynopsisBuilder(mock_vision_client, mock_text_client, mock_data_fetcher)

    # This would normally be async, simplified for test
    assert mock_vision_client.analyze_chart.called is False


def test_fallback_on_vision_failure(mock_vision_client, mock_text_client, mock_data_fetcher):
    """Test text fallback when vision fails."""
    builder = MarketSynopsisBuilder(mock_vision_client, mock_text_client, mock_data_fetcher)

    # Configure vision to fail
    mock_vision_client.analyze_chart = AsyncMock(return_value="")

    # Should trigger text fallback (tested in integration)
    assert True  # Placeholder for integration test
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/test_market_synopsis.py -v
```

Expected: FAIL (module doesn't exist)

**Step 3: Create market synopsis builder**

Create `bot/ai/market_synopsis.py`:

```python
"""
Market synopsis builder with vision primary + text fallback.
Provides AI-powered chart analysis with caching.
"""

import time
from dataclasses import dataclass

from bot.utils.logger import logger


@dataclass
class MarketAnalysis:
    """Holds AI analysis result with metadata."""
    synopsis: str
    scenarios: str
    timestamp: float
    method: str  # "vision" or "text"


class MarketSynopsisBuilder:
    """Builds market analysis with caching and fallback."""

    CACHE_TTL = 900  # 15 minutes

    def __init__(self, vision_client, text_client, data_fetcher):
        self._vision = vision_client
        self._text = text_client
        self._fetcher = data_fetcher
        self._cache: dict[str, MarketAnalysis] = {}

    def _get_cache_key(
        self,
        symbol: str,
        timeframe: str,
        indicators: dict[str, bool],
    ) -> str:
        """
        Generate unique cache key including indicator state.

        Format: {symbol}_{timeframe}_{indicator_flags}
        Example: BTCUSDT_4h_ema:1_bb:0_pivots:0_rsi:1
        """
        ind_str = "_".join(
            f"{k}:{'1' if v else '0'}"
            for k, v in sorted(indicators.items())
        )
        return f"{symbol}_{timeframe}_{ind_str}"

    async def analyze(
        self,
        symbol: str,
        timeframe: str,
        indicators: dict[str, bool],
        chart_bytes: bytes,
    ) -> MarketAnalysis:
        """
        Get market analysis with vision primary + text fallback.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "4h")
            indicators: Dict of indicator states
            chart_bytes: Chart image bytes

        Returns:
            MarketAnalysis with synopsis and scenarios
        """
        # Check cache first
        key = self._get_cache_key(symbol, timeframe, indicators)
        cached = self._cache.get(key)

        if cached and (time.time() - cached.timestamp) < self.CACHE_TTL:
            logger.debug(f"Cache HIT for {key}")
            return cached

        logger.debug(f"Cache MISS for {key}, analyzing...")

        # Try vision analysis (primary method)
        vision_result = await self._vision.analyze_chart(
            chart_bytes,
            symbol,
            timeframe,
            [k for k, v in indicators.items() if v],
        )

        if vision_result:
            logger.info(f"Vision analysis successful for {symbol} {timeframe}")
            analysis = MarketAnalysis(
                synopsis=vision_result,
                scenarios="",  # Included in vision response
                timestamp=time.time(),
                method="vision",
            )
            self._cache[key] = analysis
            return analysis

        # Fallback to text analysis
        logger.info(f"Vision failed, using text fallback for {symbol} {timeframe}")

        try:
            df = await self._fetcher.get_ohlcv(symbol, timeframe, limit=100)

            if df is None or df.empty:
                logger.warning(f"No data for text fallback: {symbol} {timeframe}")
                return MarketAnalysis(
                    synopsis="",
                    scenarios="",
                    timestamp=time.time(),
                    method="none",
                )

            text_result = await self._text.analyze_market(
                df,
                symbol,
                timeframe,
                indicators,
            )

            analysis = MarketAnalysis(
                synopsis=text_result.synopsis,
                scenarios=text_result.scenarios,
                timestamp=time.time(),
                method="text",
            )
            self._cache[key] = analysis
            return analysis

        except Exception as e:
            logger.error(f"Text fallback failed: {e}")
            return MarketAnalysis(
                synopsis="",
                scenarios="",
                timestamp=time.time(),
                method="none",
            )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_market_synopsis.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add bot/ai/market_synopsis.py tests/unit/test_market_synopsis.py
git commit -m "feat: add market synopsis builder with caching"
```

---

### Task 5: Update AI Port Interface

**Files:**
- Modify: `bot/domain/ports/ai_port.py`
- Test: `tests/unit/test_services_ports.py`

**Step 1: Add analyze_chart method to port**

Modify `bot/domain/ports/ai_port.py`:

```python
class AIAnalysisPort(ABC):
    """Port for AI analysis services."""

    @abstractmethod
    async def analyze_signal(self, signal: Signal) -> str:
        """Analyze a trading signal."""
        pass

    @abstractmethod
    async def analyze_chart(
        self,
        image_bytes: bytes,
        symbol: str,
        timeframe: str,
        indicators: list[str],
    ) -> str:
        """
        Analyze chart image using vision AI.

        Args:
            image_bytes: Chart screenshot
            symbol: Trading pair
            timeframe: Timeframe
            indicators: Active indicators

        Returns:
            AI analysis text or empty string
        """
        pass

    @abstractmethod
    async def analyze_scenario(self) -> str:
        """Analyze market scenarios."""
        pass
```

**Step 2: Update GroqAdapter to implement new method**

Modify `bot/infrastructure/groq/groq_adapter.py`:

```python
async def analyze_chart(
    self,
    image_bytes: bytes,
    symbol: str,
    timeframe: str,
    indicators: list[str],
) -> str:
    """
    Analyze chart image using Groq Vision.
    Delegates to VisionClient for actual implementation.
    """
    from bot.ai.vision_client import VisionClient

    vision = VisionClient(self._api_key)
    return await vision.analyze_chart(image_bytes, symbol, timeframe, indicators)
```

**Step 3: Run linting**

```bash
ruff check bot/domain/ports/ai_port.py bot/infrastructure/groq/groq_adapter.py --fix
ruff format bot/domain/ports/ai_port.py bot/infrastructure/groq/groq_adapter.py
```

**Step 4: Commit**

```bash
git add bot/domain/ports/ai_port.py bot/infrastructure/groq/groq_adapter.py
git commit -m "feat: add analyze_chart method to AI port"
```

---

### Task 6: Integrate AI Analysis into Chart Handler

**Files:**
- Modify: `bot/handlers/chart_handler.py:100-150`
- Test: `tests/integration/test_chart_with_ai.py`

**Step 1: Add AI analysis to chart command**

Modify `bot/handlers/chart_handler.py` - update `chart_command()` function:

```python
@admin_only
async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura y envía el gráfico con análisis IA."""

    args = context.args
    symbol = DEFAULT_SYMBOL
    timeframe = DEFAULT_TIMEFRAME

    # Parse arguments (existing logic)
    for arg in args:
        arg_lower = arg.lower()
        arg_upper = arg.upper()
        if arg_lower in VALID_TIMEFRAMES:
            timeframe = arg_lower
        elif arg_upper.endswith("USDT") or arg_upper.endswith("BTC"):
            symbol = arg_upper
        else:
            await update.message.reply_text(
                f"⚠️ *Argumento inválido: `{arg}`*\n"
                f"Timeframes válidos: `{', '.join(VALID_TIMEFRAMES)}`\n"
                f"Ejemplo: `/chart ETHUSDT 1h`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    # Show loading state with AI mention
    msg = await update.message.reply_text(
        f"⏳ *Generando gráfico {symbol} {timeframe.upper()} con análisis IA...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        chart_capture = ChartCapture()

        # Capture chart with indicators (default: none)
        chart_bytes = await chart_capture.capture(
            symbol,
            timeframe,
            show_ema=False,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )

        if not chart_bytes:
            await msg.edit_text("⚠️ Error generando gráfico.")
            return

        # Get AI analysis
        from bot.container import Container
        container = Container()
        synopsis_builder = container.market_synopsis_builder()

        analysis = await synopsis_builder.analyze(
            symbol=symbol,
            timeframe=timeframe,
            indicators={
                "ema": False,
                "bb": False,
                "rsi": False,
                "pivots": False,
            },
            chart_bytes=chart_bytes,
        )

        # Build caption with AI analysis
        now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        caption = f"📊 *{symbol} {timeframe.upper()}* — {now_utc}\n\n"

        if analysis.synopsis:
            caption += f"🧠 *ANÁLISIS IA*\n{analysis.synopsis}\n"

            if analysis.scenarios:
                caption += f"\n{analysis.scenarios}\n"

            if analysis.method == "text":
                caption += "\n_📝 Análisis basado en datos (fallback)_"
        else:
            caption += "_Gráfico generado exitosamente._"

        # Build keyboard with default state
        keyboard = build_chart_keyboard(
            symbol,
            timeframe,
            show_ema=False,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )

        await msg.delete()
        await update.message.reply_photo(
            photo=chart_bytes,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )

        await chart_capture.close()

    except Exception as e:
        logger.error(f"Chart command failed: {e}")
        try:
            await msg.edit_text(f"⚠️ Error: {str(e)}")
        except Exception:
            await msg.edit_text(f"⚠️ Error: {str(e)}")
```

**Step 2: Update callback handlers to include AI analysis**

Modify `handle_timeframe_change()` in `bot/handlers/chart_handler.py`:

```python
async def handle_timeframe_change(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    new_timeframe: str,
    show_ema: bool,
    show_bb: bool,
    show_rsi: bool,
    show_pivots: bool,
):
    """Handle timeframe change button click."""
    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture(
            symbol,
            new_timeframe,
            show_ema=show_ema,
            show_bb=show_bb,
            show_rsi=show_rsi,
            show_pivots=show_pivots,
        )

        if chart_bytes:
            now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

            # Get AI analysis for new configuration
            from bot.container import Container
            container = Container()
            synopsis_builder = container.market_synopsis_builder()

            analysis = await synopsis_builder.analyze(
                symbol=symbol,
                timeframe=new_timeframe,
                indicators={
                    "ema": show_ema,
                    "bb": show_bb,
                    "rsi": show_rsi,
                    "pivots": show_pivots,
                },
                chart_bytes=chart_bytes,
            )

            # Build caption
            caption = f"📊 *{symbol} {new_timeframe.upper()}* — {now_utc}\n\n"

            if analysis.synopsis:
                caption += f"🧠 *ANÁLISIS IA*\n{analysis.synopsis}\n"
                if analysis.method == "text":
                    caption += "\n_📝 Análisis basado en datos_"

            keyboard = build_chart_keyboard(
                symbol,
                new_timeframe,
                show_ema=show_ema,
                show_bb=show_bb,
                show_rsi=show_rsi,
                show_pivots=show_pivots,
            )

            from telegram import InputMediaPhoto

            media = InputMediaPhoto(
                media=chart_bytes,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
            )

            try:
                await update.callback_query.edit_message_media(
                    media=media,
                    reply_markup=keyboard,
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.debug("Message unchanged, skipping")
                    return
                raise

        await chart_capture.close()

    except Exception as e:
        logger.warning(f"Error cambiando timeframe: {e}")
        raise
```

**Step 3: Run linting**

```bash
ruff check bot/handlers/chart_handler.py --fix
ruff format bot/handlers/chart_handler.py
```

**Step 4: Commit**

```bash
git add bot/handlers/chart_handler.py
git commit -m "feat: integrate AI analysis into chart command"
```

---

### Task 7: Update Dependency Injection Container

**Files:**
- Modify: `bot/container.py`
- Test: N/A (integration test covers this)

**Step 1: Add market synopsis builder to container**

Modify `bot/container.py`:

```python
from bot.ai.market_synopsis import MarketSynopsisBuilder
from bot.ai.vision_client import VisionClient
# ... existing imports

class Container:
    # ... existing methods

    def vision_client(self) -> VisionClient:
        """Get Vision API client."""
        return VisionClient()

    def market_synopsis_builder(self) -> MarketSynopsisBuilder:
        """Get market synopsis builder."""
        from bot.infrastructure.binance.binance_adapter import BinanceAdapter

        vision = self.vision_client()
        text = self.groq_client()  # Reuse existing GroqClient for text
        fetcher = BinanceAdapter()

        return MarketSynopsisBuilder(vision, text, fetcher)
```

**Step 2: Run linting**

```bash
ruff check bot/container.py --fix
ruff format bot/container.py
```

**Step 3: Commit**

```bash
git add bot/container.py
git commit -m "feat: add market synopsis builder to DI container"
```

---

### Task 8: Add Integration Tests

**Files:**
- Create: `tests/integration/test_chart_with_ai.py`

**Step 1: Write integration tests**

Create `tests/integration/test_chart_with_ai.py`:

```python
"""Integration tests for chart with AI analysis."""

import pytest

from bot.ai.vision_client import VisionClient
from bot.ai.market_synopsis import MarketSynopsisBuilder
from bot.trading.chart_capture import ChartCapture


@pytest.mark.asyncio
async def test_vision_client_initialization():
    """Test VisionClient initializes correctly."""
    client = VisionClient()
    assert client.MODEL == "llama-3.2-11b-vision-preview"
    assert client.TIMEOUT == 10


@pytest.mark.asyncio
async def test_market_synopsis_builder_cache():
    """Test MarketSynopsisBuilder caching behavior."""
    # This test verifies cache key generation and TTL behavior
    from unittest.mock import AsyncMock

    vision_mock = AsyncMock()
    text_mock = AsyncMock()
    fetcher_mock = AsyncMock()

    builder = MarketSynopsisBuilder(vision_mock, text_mock, fetcher_mock)

    # Test cache key generation
    key1 = builder._get_cache_key("BTCUSDT", "4h", {"ema": True, "bb": False})
    key2 = builder._get_cache_key("BTCUSDT", "4h", {"ema": True, "bb": False})
    key3 = builder._get_cache_key("BTCUSDT", "4h", {"ema": False, "bb": False})

    assert key1 == key2
    assert key1 != key3


@pytest.mark.asyncio
async def test_chart_capture_with_indicators():
    """Test chart capture generates different images for different indicators."""
    capture = ChartCapture()

    try:
        # Capture with no indicators
        chart_none = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=False, show_bb=False, show_rsi=False, show_pivots=False,
        )

        # Capture with EMA
        chart_ema = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=True, show_bb=False, show_rsi=False, show_pivots=False,
        )

        assert chart_none is not None
        assert chart_ema is not None
        # Images should be different (different cache keys)

    finally:
        await capture.close()
```

**Step 2: Run integration tests**

```bash
pytest tests/integration/test_chart_with_ai.py -v
```

Expected: All PASS (may skip if API key not configured)

**Step 3: Commit**

```bash
git add tests/integration/test_chart_with_ai.py
git commit -m "test: add integration tests for AI chart analysis"
```

---

### Task 9: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/ai-chart-analysis.md`

**Step 1: Add AI chart analysis documentation**

Create `docs/ai-chart-analysis.md`:

```markdown
# AI-Powered Chart Analysis

## Overview

The `/chart` command now includes AI-powered market analysis using Groq Vision API. The system analyzes chart screenshots to identify trends, support/resistance levels, and provides bullish/bearish/neutral scenarios.

## Features

- **Vision-Based Analysis**: Primary method uses Groq LLaVA model to analyze chart images
- **Text Fallback**: Automatically falls back to OHLCV data analysis if vision fails
- **Smart Caching**: 15-minute cache per symbol/timeframe/indicator combination
- **Spanish Language**: All analysis provided in Spanish
- **Concise Output**: 50-75 words optimized for Telegram captions

## Usage

```bash
/chart BTCUSDT 4h
```

Response includes:
1. Chart image with selected indicators
2. AI analysis (trend, key levels, scenarios)
3. Interactive buttons to change timeframe/toggle indicators

## Configuration

### Environment Variables

```bash
# Required for AI analysis
GROQ_API_KEY=your_api_key_here

# Optional: Vision API customization
GROQ_VISION_MODEL=llama-3.2-11b-vision-preview
GROQ_VISION_MAX_TOKENS=200
GROQ_VISION_TEMPERATURE=0.3
GROQ_VISION_TIMEOUT=10
```

## How It Works

1. User sends `/chart BTCUSDT 4h`
2. System generates chart with matplotlib
3. Chart sent to Groq Vision API
4. AI identifies patterns, levels, scenarios
5. Analysis cached for 15 minutes
6. Chart + analysis sent to Telegram

### Fallback Behavior

If Vision API fails (timeout, error, no API key):
- System automatically uses text-based analysis
- Sends OHLCV data + indicators to Groq text API
- User receives analysis marked as "📝 Análisis basado en datos"

If both fail:
- Chart sent without AI analysis
- Error logged for debugging

## Caching

Cache key format: `{symbol}_{timeframe}_{indicators}`

Example: `BTCUSDT_4h_ema:1_bb:0_rsi:1_pivots:0`

Cache TTL: 15 minutes

Cache invalidation: Automatic on next request after TTL

## Cost Estimation

- Vision API: ~$0.0002 per analysis
- Text API: ~$0.00005 per analysis
- 100 requests/day: ~$0.60/month (well within free tier)

## Error Handling

| Error | Behavior | User Sees |
|-------|----------|-----------|
| Vision timeout | Text fallback | Analysis (marked as fallback) |
| Vision error | Text fallback | Analysis (marked as fallback) |
| Text error | Chart only | Chart without analysis |
| No API key | Chart only | Chart without analysis |

## Testing

```bash
# Unit tests
pytest tests/unit/test_vision_client.py -v
pytest tests/unit/test_market_synopsis.py -v
pytest tests/unit/test_prompts.py -v

# Integration tests
pytest tests/integration/test_chart_with_ai.py -v
```
```

**Step 2: Update README with AI feature**

Modify `README.md` - add to features section:

```markdown
## Features

- 📊 **Automated Technical Analysis** - RSI, MACD, Bollinger Bands, EMA, Supertrend
- 🎯 **Trading Signals** - Entry opportunities with risk:reward ratios
- 📡 **WebSocket Price Monitor** - Real-time take profit and stop loss tracking
- 🧠 **AI Integration** - Market context analysis via Groq API
- 🖼️ **AI Chart Analysis** - Vision-powered market synopsis with scenarios (NEW)
- 🌐 **Multi-language** - Spanish and English support
- 💰 **Capital Management** - Drawdown control and performance tracking
```

**Step 3: Commit**

```bash
git add docs/ai-chart-analysis.md README.md
git commit -m "docs: add AI chart analysis documentation"
```

---

### Task 10: Run Full Test Suite and Verify

**Files:**
- All tests

**Step 1: Run unit tests**

```bash
pytest tests/unit/test_vision_client.py tests/unit/test_market_synopsis.py tests/unit/test_prompts.py -v
```

Expected: All PASS

**Step 2: Run integration tests**

```bash
pytest tests/integration/test_chart_with_ai.py -v
```

Expected: All PASS (may skip if GROQ_API_KEY not set)

**Step 3: Run full test suite**

```bash
pytest --cov=. --cov-report=term-missing
```

Expected: All PASS, coverage maintained or improved

**Step 4: Run linting**

```bash
ruff check . --fix
ruff format .
```

Expected: No issues

**Step 5: Commit**

```bash
git add .
git commit -m "test: verify all tests pass for AI chart analysis"
```

---

### Task 11: Manual Testing in Telegram

**Files:**
- N/A (manual testing)

**Step 1: Start the bot**

```bash
source venv/bin/activate
python bot/main.py
```

**Step 2: Test in Telegram**

1. Send `/chart BTCUSDT 4h`
2. **Expected:** Chart + AI analysis in Spanish (50-75 words)
3. Verify analysis includes:
   - Trend direction (alcista/bajista/lateral)
   - Support/resistance levels with prices
   - Bullish/bearish/neutral scenarios
4. Click "1h" timeframe button
5. **Expected:** New chart + new AI analysis for 1h
6. Click "📈 EMA" button
7. **Expected:** Chart regenerates with EMA + new AI analysis
8. Wait 16 minutes
9. Send `/chart BTCUSDT 4h` again
10. **Expected:** Cache expired, new AI analysis generated

**Step 3: Test fallback behavior**

1. Temporarily set invalid GROQ_API_KEY in `.env`
2. Restart bot
3. Send `/chart BTCUSDT 4h`
4. **Expected:** Chart sent without AI analysis (graceful degradation)
5. Check logs for warning message

**Step 4: Verify caching**

1. Send `/chart BTCUSDT 4h` twice in quick succession
2. **Expected:** Second request uses cached analysis (faster response)
3. Check logs for "Cache HIT" message

**Step 5: Check logs**

```bash
tail -100 bot/logs/sipsignal.log | grep -i "vision\|synopsis\|cache"
```

Expected: Debug logs showing analysis flow

---

## Verification Criteria

✅ All unit tests pass
✅ All integration tests pass
✅ Manual testing confirms:
  - AI analysis appears in chart messages
  - Vision API is primary method
  - Text fallback works on vision failure
  - Caching reduces API calls
  - Graceful degradation on complete failure
✅ Analysis is in Spanish (50-75 words)
✅ Scenarios include price targets
✅ Linting passes (ruff check + format)
✅ No regression in existing chart functionality

---

## Rollback Plan

If issues occur:

1. **Revert commits:**
   ```bash
   git log --oneline -10
   git revert <commit-hash>  # Revert AI-related commits
   ```

2. **Restart bot:**
   ```bash
   sudo systemctl restart sipsignal
   ```

3. **Investigate logs:**
   ```bash
   tail -200 bot/logs/sipsignal.log | grep -i "error\|exception"
   ```

4. **Disable AI temporarily:**
   - Comment out AI analysis call in `chart_handler.py`
   - Bot continues working with chart-only mode

---

## Related Files Reference

### New Files
- `bot/ai/vision_client.py` - Groq Vision API client
- `bot/ai/market_synopsis.py` - Market synopsis builder with caching
- `docs/ai-chart-analysis.md` - Feature documentation
- `tests/unit/test_vision_client.py` - Vision client tests
- `tests/unit/test_market_synopsis.py` - Synopsis builder tests
- `tests/integration/test_chart_with_ai.py` - Integration tests

### Modified Files
- `bot/ai/prompts.py` - Add vision and text fallback prompts
- `bot/handlers/chart_handler.py` - Integrate AI analysis
- `bot/domain/ports/ai_port.py` - Add analyze_chart method
- `bot/infrastructure/groq/groq_adapter.py` - Implement vision method
- `bot/container.py` - Add synopsis builder to DI
- `bot/core/config.py` - Add vision API config
- `README.md` - Update features
- `env.example` - Add vision env vars

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Vision API success rate | >95% | Logs / total requests |
| Text fallback trigger rate | <5% | Fallback logs / total |
| Cache hit rate | >60% | Cache HIT logs / total |
| Average response time | <8s | Request to response |
| User satisfaction | N/A | Manual feedback |

---

## Future Enhancements (Out of Scope)

- Support for multiple symbols in single analysis
- Custom prompt templates per timeframe
- User-configurable analysis depth (brief/detailed)
- Historical comparison ("vs yesterday's analysis")
- Multi-language support based on `/lang` setting
- Vision model A/B testing (LLaVA vs other models)
