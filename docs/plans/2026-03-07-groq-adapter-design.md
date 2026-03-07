# GroqAdapter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement `GroqAdapter` class in `bot/infrastructure/groq/groq_adapter.py` that inherits from `AIAnalysisPort` and uses httpx.AsyncClient for async API calls to Groq.

**Architecture:** Create a new adapter following the port interface pattern. Uses httpx.AsyncClient directly instead of the groq SDK for async HTTP calls.

**Tech Stack:** Python 3.13+, httpx, asyncio

---

## Tasks

### Task 1: Create GroqAdapter class

**Files:**
- Create: `bot/infrastructure/groq/groq_adapter.py`
- Reference: `bot/domain/ports/ai_analysis_port.py:6-11`
- Reference: `bot/domain/signal.py:5-17`

**Step 1: Write the failing test**

Create test file `tests/unit/test_groq_adapter.py`:

```python
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import UTC, datetime

from bot.domain.signal import Signal
from bot.infrastructure.groq.groq_adapter import GroqAdapter


class TestGroqAdapter:

    @pytest.fixture
    def adapter(self):
        return GroqAdapter(api_key="test_api_key")

    @pytest.fixture
    def sample_signal(self):
        return Signal(
            id=1,
            direction="LONG",
            entry_price=45000.0,
            tp1_level=47000.0,
            sl_level=44000.0,
            rr_ratio=2.5,
            atr_value=1200.0,
            supertrend_line=44500.0,
            timeframe="1h",
            detected_at=datetime.now(UTC),
            status="EMITIDA",
        )

    @pytest.mark.asyncio
    async def test_analyze_signal_success(self, adapter, sample_signal):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Test analysis result"}}
            ]
        }

        with patch.object(adapter._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await adapter.analyze_signal(sample_signal)

        assert result == "Test analysis result"

    @pytest.mark.asyncio
    async def test_analyze_signal_returns_empty_on_failure(self, adapter, sample_signal):
        with patch.object(adapter._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API Error")
            result = await adapter.analyze_signal(sample_signal)

        assert result == ""

    @pytest.mark.asyncio
    async def test_analyze_scenario_success(self, adapter):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Bullish: ...\nNeutral: ...\nBearish: ..."}}
            ]
        }

        with patch.object(adapter._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await adapter.analyze_scenario()

        assert "Bullish:" in result
        assert "Neutral:" in result
        assert "Bearish:" in result

    @pytest.mark.asyncio
    async def test_analyze_scenario_returns_empty_on_failure(self, adapter):
        with patch.object(adapter._client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("API Error")
            result = await adapter.analyze_scenario()

        assert result == ""
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/unit/test_groq_adapter.py -v`
Expected: FAIL with "GroqAdapter not found"

**Step 3: Write minimal implementation**

Create `bot/infrastructure/groq/groq_adapter.py`:

```python
import httpx

from bot.domain.ports import AIAnalysisPort
from bot.domain.signal import Signal


class GroqAdapter(AIAnalysisPort):
    """Async adapter for Groq API using httpx."""

    MODEL = "llama3-70b-8192"
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    MAX_TOKENS = 150
    TEMPERATURE = 0.3

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    async def analyze_signal(self, signal: Signal) -> str:
        """
        Analyze a trading signal using Groq.

        Args:
            signal: Signal with trading data

        Returns:
            Analysis text or empty string on failure
        """
        direction_text = "alcista" if signal.direction == "LONG" else "bajista"
        supertrend_status = "alcista" if signal.entry_price > signal.supertrend_line else "bajista"

        prompt = (
            f"Analiza el contexto de mercado para esta señal {direction_text} en BTC/USDT "
            f"timeframe {signal.timeframe}. "
            f"Dirección: {signal.direction}. "
            f"Precio entrada: ${signal.entry_price:,.2f}. "
            f"SL: ${signal.sl_level:,.2f}. "
            f"TP1: ${signal.tp1_level:,.2f}. "
            f"Estado Supertrend: {supertrend_status} "
            f"(línea en ${signal.supertrend_line:,.2f}). "
            f"Ratio R:R: {signal.rr_ratio:.2f}. "
            f"Proporciona un análisis de contexto de mercado en 2-3 oraciones en español."
        )

        return await self._call_groq(prompt)

    async def analyze_scenario(self) -> str:
        """
        Analyze BTC scenario with bullish, neutral, and bearish perspectives.

        Returns:
            Scenario analysis or empty string on failure
        """
        prompt = (
            "Proporciona un análisis de escenario para BTC/USDT en tres perspectivas:\n"
            "1. ESCENARIO ALCISTA: ¿Qué necesitaría pasar para confirmar tendencia alcista?\n"
            "2. ESCENARIO NEUTRAL: Condiciones actuales y rangos probables\n"
            "3. ESCENARIO BAJISTA: ¿Qué señales indicarían debilidad?\n"
            "Sé conciso y práctico."
        )

        return await self._call_groq(prompt)

    async def _call_groq(self, prompt: str) -> str:
        """Make API call to Groq and return response text."""
        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente de análisis de trading. Responde de forma concisa.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
        }

        try:
            response = await self._client.post(self.ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/unit/test_groq_adapter.py -v`
Expected: PASS

**Step 5: Run linting**

Run: `source venv/bin/activate && ruff check bot/infrastructure/groq/groq_adapter.py`
Expected: No errors

---

### Task 2: Update __init__.py exports

**Files:**
- Modify: `bot/infrastructure/groq/__init__.py`

**Step 1: Add exports**

```python
from bot.infrastructure.groq.groq_adapter import GroqAdapter

__all__ = ["GroqAdapter"]
```

**Step 2: Run lint**

Run: `source venv/bin/activate && ruff check bot/infrastructure/groq/`
Expected: No errors

---

### Task 3: Run full test suite

**Step 1: Run all tests**

Run: `source venv/bin/activate && pytest --cov=bot/infrastructure/groq --cov-report=term-missing`
Expected: All tests pass

---

## Notes

- The adapter uses httpx.AsyncClient directly as specified in the prompt
- Error handling returns empty string without propagating exceptions
- API endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Model: `llama3-70b-8192`
