import os
import sys
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.application.get_signal_analysis import DEFAULT_ANALYSIS_CONFIG, GetSignalAnalysis
from bot.domain.signal import Signal


class MockMarketDataPort:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        return self._df


class MockChartPort:
    def __init__(self, chart_bytes: bytes | None = None):
        self._chart_bytes = chart_bytes

    async def capture(self, symbol: str, timeframe: str) -> bytes | None:
        return self._chart_bytes

    async def close(self) -> None:
        pass


class MockAIAnalysisPort:
    def __init__(self, context: str = "AI analysis"):
        self._context = context

    async def analyze_signal(self, signal: Signal) -> str:
        return self._context

    async def analyze_scenario(self) -> str:
        return self._context


def create_df() -> pd.DataFrame:
    dates = pd.date_range(start="2024-01-01", periods=50, freq="1h")
    close_prices = [50000 + i * 10 for i in range(50)]

    df = pd.DataFrame(
        {
            "open": close_prices,
            "high": [c + 100 for c in close_prices],
            "low": [c - 100 for c in close_prices],
            "close": close_prices,
            "volume": [1000 for _ in range(50)],
        },
        index=dates,
    )

    atr_col = f"ATRr_{DEFAULT_ANALYSIS_CONFIG['tp_period']}"
    df[atr_col] = 500.0

    df["SUPERT_14_1.8"] = [c * 0.999 for c in close_prices]
    df["SUPERTd_14_1.8"] = -1
    df["sup_is_bullish"] = True
    df["sup_cross_bullish"] = False
    df["sup_cross_bearish"] = False
    df["supertrend_line"] = [c * 0.999 for c in close_prices]

    df["ash_smth_bulls"] = 100.0
    df["ash_smth_bears"] = 50.0
    df["ash_difference"] = 100.0
    df["ash_bullish"] = True
    df["ash_bearish"] = False
    df["ash_neutral"] = False
    df["ash_bullish_signal"] = True
    df["ash_bearish_signal"] = False

    df["long_tp"] = [c + 750 for c in close_prices]
    df["long_sl"] = [c - 750 for c in close_prices]
    df["short_tp"] = [c - 750 for c in close_prices]
    df["short_sl"] = [c + 750 for c in close_prices]
    df["rr_ratio"] = 1.5

    return df


def mock_calculate_all(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    return df


@pytest.mark.asyncio
async def test_execute_returns_signal_ai_context_and_chart():
    df = create_df()
    market_data = MockMarketDataPort(df)
    chart = MockChartPort(b"fake_chart")
    ai = MockAIAnalysisPort("AI context")

    use_case = GetSignalAnalysis(market_data, chart, ai)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute("1h")

    assert "signal" in result
    assert "ai_context" in result
    assert "chart_bytes" in result

    assert result["ai_context"] == "AI context"
    assert result["chart_bytes"] == b"fake_chart"

    signal = result["signal"]
    assert isinstance(signal, Signal)
    assert signal.status == "ANALISIS"
    assert signal.timeframe == "1h"


@pytest.mark.asyncio
async def test_execute_uses_custom_timeframe():
    df = create_df()
    market_data = MockMarketDataPort(df)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()

    use_case = GetSignalAnalysis(market_data, chart, ai)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute("4h")

    assert result["signal"].timeframe == "4h"


@pytest.mark.asyncio
async def test_execute_ai_failure_continues():
    df = create_df()
    market_data = MockMarketDataPort(df)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()
    ai.analyze_signal = AsyncMock(side_effect=Exception("AI failed"))

    use_case = GetSignalAnalysis(market_data, chart, ai)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute()

    assert result["ai_context"] == ""


@pytest.mark.asyncio
async def test_execute_chart_failure_continues():
    df = create_df()
    market_data = MockMarketDataPort(df)
    chart = MockChartPort()
    chart.capture = AsyncMock(side_effect=Exception("Chart failed"))
    ai = MockAIAnalysisPort()

    use_case = GetSignalAnalysis(market_data, chart, ai)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute()

    assert result["chart_bytes"] is None
