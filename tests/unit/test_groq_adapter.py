import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test analysis result"}}]
        }
        mock_response.raise_for_status = MagicMock()

        adapter._client.post = AsyncMock(return_value=mock_response)

        result = await adapter.analyze_signal(sample_signal)

        assert result == "Test analysis result"

    @pytest.mark.asyncio
    async def test_analyze_signal_returns_empty_on_failure(self, adapter, sample_signal):
        adapter._client.post = AsyncMock(side_effect=Exception("API Error"))

        result = await adapter.analyze_signal(sample_signal)

        assert result == ""

    @pytest.mark.asyncio
    async def test_analyze_scenario_success(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Bullish: test\nNeutral: test\nBearish: test"}}]
        }
        mock_response.raise_for_status = MagicMock()

        adapter._client.post = AsyncMock(return_value=mock_response)

        result = await adapter.analyze_scenario()

        assert "Bullish:" in result
        assert "Neutral:" in result
        assert "Bearish:" in result

    @pytest.mark.asyncio
    async def test_analyze_scenario_returns_empty_on_failure(self, adapter):
        adapter._client.post = AsyncMock(side_effect=Exception("API Error"))

        result = await adapter.analyze_scenario()

        assert result == ""
