import os
import sys
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.application.get_scenario_analysis import DEFAULT_ANALYSIS_CONFIG, GetScenarioAnalysis
from bot.domain.signal import Signal


class MockMarketDataPort:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        return self._df


class MockAIAnalysisPort:
    def __init__(self, analysis: str = "Scenario analysis result"):
        self._analysis = analysis

    async def analyze_signal(self, signal: Signal) -> str:
        return "signal analysis"

    async def analyze_scenario(self, context: str) -> str:
        return self._analysis


def create_df() -> pd.DataFrame:
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1d")
    close_prices = [50000 + i * 100 for i in range(100)]

    df = pd.DataFrame(
        {
            "open": close_prices,
            "high": [c + 500 for c in close_prices],
            "low": [c - 500 for c in close_prices],
            "close": close_prices,
            "volume": [1000 for _ in range(100)],
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
async def test_execute_returns_ai_analysis():
    df = create_df()
    market_data = MockMarketDataPort(df)
    ai = MockAIAnalysisPort("Escenario bullish confirmado")

    use_case = GetScenarioAnalysis(market_data, ai)

    with patch("bot.application.get_scenario_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute()

    assert result == "Escenario bullish confirmado"


@pytest.mark.asyncio
async def test_execute_builds_summary_with_bullish_trend():
    df = create_df()
    df["sup_is_bullish"] = True

    market_data = MockMarketDataPort(df)
    ai = MockAIAnalysisPort()

    use_case = GetScenarioAnalysis(market_data, ai)

    captured_context = None

    async def capture_analyze(context: str) -> str:
        nonlocal captured_context
        captured_context = context
        return "analysis"

    ai.analyze_scenario = capture_analyze

    with patch("bot.application.get_scenario_analysis.calculate_all", mock_calculate_all):
        await use_case.execute()

    assert captured_context is not None
    assert "ALCISTA" in captured_context
    assert "$59,900.00" in captured_context


@pytest.mark.asyncio
async def test_execute_builds_summary_with_bearish_trend():
    df = create_df()
    df["sup_is_bullish"] = False

    market_data = MockMarketDataPort(df)
    ai = MockAIAnalysisPort()

    use_case = GetScenarioAnalysis(market_data, ai)

    captured_context = None

    async def capture_analyze(context: str) -> str:
        nonlocal captured_context
        captured_context = context
        return "analysis"

    ai.analyze_scenario = capture_analyze

    with patch("bot.application.get_scenario_analysis.calculate_all", mock_calculate_all):
        await use_case.execute()

    assert captured_context is not None
    assert "BAJISTA" in captured_context


@pytest.mark.asyncio
async def test_execute_includes_rsi_when_available():
    df = create_df()
    df["rsi"] = 65.5

    market_data = MockMarketDataPort(df)
    ai = MockAIAnalysisPort()

    use_case = GetScenarioAnalysis(market_data, ai)

    captured_context = None

    async def capture_analyze(context: str) -> str:
        nonlocal captured_context
        captured_context = context
        return "analysis"

    ai.analyze_scenario = capture_analyze

    with patch("bot.application.get_scenario_analysis.calculate_all", mock_calculate_all):
        await use_case.execute()

    assert captured_context is not None
    assert "65.50" in captured_context or "65.5" in captured_context


@pytest.mark.asyncio
async def test_execute_includes_ema_position_when_available():
    df = create_df()
    df["ema_20"] = 50000.0

    market_data = MockMarketDataPort(df)
    ai = MockAIAnalysisPort()

    use_case = GetScenarioAnalysis(market_data, ai)

    captured_context = None

    async def capture_analyze(context: str) -> str:
        nonlocal captured_context
        captured_context = context
        return "analysis"

    ai.analyze_scenario = capture_analyze

    with patch("bot.application.get_scenario_analysis.calculate_all", mock_calculate_all):
        await use_case.execute()

    assert captured_context is not None
    assert "EMA" in captured_context
