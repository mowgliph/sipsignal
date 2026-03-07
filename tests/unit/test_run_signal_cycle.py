import os
import sys
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.application.run_signal_cycle import DEFAULT_ANALYSIS_CONFIG, RunSignalCycle
from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig


class MockMarketDataPort:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        return self._df


class MockSignalRepository:
    def __init__(self):
        self.saved_signal: Signal | None = None

    async def save(self, signal: Signal) -> Signal:
        signal.id = 1
        self.saved_signal = signal
        return signal

    async def get_by_id(self, signal_id: int) -> Signal | None:
        return self.saved_signal

    async def get_recent(self, limit: int) -> list[Signal]:
        return [self.saved_signal] if self.saved_signal else []

    async def update_status(self, signal_id: int, status: str) -> None:
        if self.saved_signal:
            self.saved_signal.status = status


class MockActiveTradeRepository:
    def __init__(self, has_active: bool = False):
        self._has_active = has_active

    async def save(self, trade) -> None:
        pass

    async def get_active(self):
        return {"id": 1} if self._has_active else None

    async def update(self, trade) -> None:
        pass

    async def close(self, trade_id: int, status: str) -> None:
        pass


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


class MockNotifierPort:
    def __init__(self):
        self.sent_signals: list[dict] = []

    async def send_signal(
        self, chat_id: int, signal: Signal, chart: bytes | None, ai_context: str
    ) -> None:
        self.sent_signals.append(
            {
                "chat_id": chat_id,
                "signal": signal,
                "chart": chart,
                "ai_context": ai_context,
            }
        )


def create_df_with_conditions(signal_type: str = "LONG") -> pd.DataFrame:
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
    df["SUPERTd_14_1.8"] = -1 if signal_type == "LONG" else 1
    df["sup_is_bullish"] = signal_type == "LONG"
    df["sup_cross_bullish"] = False
    df["sup_cross_bearish"] = False
    df["supertrend_line"] = [c * 0.999 for c in close_prices]

    df["ash_smth_bulls"] = 100.0
    df["ash_smth_bears"] = 50.0
    df["ash_difference"] = 100.0
    df["ash_bullish"] = signal_type == "LONG"
    df["ash_bearish"] = signal_type == "SHORT"
    df["ash_neutral"] = False
    df["ash_bullish_signal"] = signal_type == "LONG"
    df["ash_bearish_signal"] = signal_type == "SHORT"

    df["long_tp"] = [c + 750 for c in close_prices]
    df["long_sl"] = [c - 750 for c in close_prices]
    df["short_tp"] = [c - 750 for c in close_prices]
    df["short_sl"] = [c + 750 for c in close_prices]
    df["rr_ratio"] = 1.5

    return df


def mock_calculate_all(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    return df


@pytest.mark.asyncio
async def test_execute_returns_none_when_active_trade_exists():
    df = create_df_with_conditions()
    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=True)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()
    notifier = MockNotifierPort()
    admin_ids = [123, 456]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is None


@pytest.mark.asyncio
async def test_execute_detects_long_signal():
    df = create_df_with_conditions(signal_type="LONG")
    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort(b"fake_chart")
    ai = MockAIAnalysisPort("AI context")
    notifier = MockNotifierPort()
    admin_ids = [123]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is not None
    assert result.direction == "LONG"
    assert result.id == 1


@pytest.mark.asyncio
async def test_execute_detects_short_signal():
    df = create_df_with_conditions(signal_type="SHORT")
    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort(b"fake_chart")
    ai = MockAIAnalysisPort("AI context")
    notifier = MockNotifierPort()
    admin_ids = [123]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is not None
    assert result.direction == "SHORT"


@pytest.mark.asyncio
async def test_execute_returns_none_without_signal():
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

    df["ash_smth_bulls"] = 10.0
    df["ash_smth_bears"] = 50.0
    df["ash_difference"] = 10.0
    df["ash_bullish"] = False
    df["ash_bearish"] = False
    df["ash_neutral"] = True
    df["ash_bullish_signal"] = False
    df["ash_bearish_signal"] = False

    df["long_tp"] = [c + 750 for c in close_prices]
    df["long_sl"] = [c - 750 for c in close_prices]
    df["short_tp"] = [c - 750 for c in close_prices]
    df["short_sl"] = [c + 750 for c in close_prices]
    df["rr_ratio"] = 0.5

    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()
    notifier = MockNotifierPort()
    admin_ids = [123]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is None


@pytest.mark.asyncio
async def test_execute_sends_to_all_admins():
    df = create_df_with_conditions()
    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort(b"chart")
    ai = MockAIAnalysisPort("context")
    notifier = MockNotifierPort()
    admin_ids = [111, 222, 333]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert len(notifier.sent_signals) == 3
    assert notifier.sent_signals[0]["chat_id"] == 111
    assert notifier.sent_signals[1]["chat_id"] == 222
    assert notifier.sent_signals[2]["chat_id"] == 333


@pytest.mark.asyncio
async def test_execute_ai_failure_uses_empty_string():
    df = create_df_with_conditions()
    market_data = MockMarketDataPort(df)
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()
    ai.analyze_signal = AsyncMock(side_effect=Exception("AI failed"))
    notifier = MockNotifierPort()
    admin_ids = [123]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    with patch("bot.trading.technical_analysis.calculate_all", mock_calculate_all):
        result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is not None
    assert notifier.sent_signals[0]["ai_context"] == ""


@pytest.mark.asyncio
async def test_execute_returns_none_on_exception():
    market_data = MockMarketDataPort(pd.DataFrame())
    signal_repo = MockSignalRepository()
    trade_repo = MockActiveTradeRepository(has_active=False)
    chart = MockChartPort()
    ai = MockAIAnalysisPort()
    notifier = MockNotifierPort()
    admin_ids = [123]

    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, admin_ids)

    result = await use_case.execute(UserConfig(user_id=1, timeframe="1h"))

    assert result is None
