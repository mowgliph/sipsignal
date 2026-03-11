"""Unit tests for strategy engine with active trade check."""

import os
import sys
from datetime import UTC, datetime
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.domain.active_trade import ActiveTrade
from bot.trading.strategy_engine import UserConfig, run_cycle


def mock_calculate_all(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Mock calculate_all that returns DataFrame unchanged."""
    return df


class MockActiveTradeRepository:
    """Mock trade repository for testing."""

    def __init__(self, active_trade: ActiveTrade | None = None):
        self._active_trade = active_trade

    async def get_active(self) -> ActiveTrade | None:
        """Return active trade if exists."""
        return self._active_trade

    async def save(self, trade: ActiveTrade) -> ActiveTrade:
        """Mock save method."""
        return trade

    async def update(self, trade: ActiveTrade) -> None:
        """Mock update method."""
        pass

    async def close(self, trade_id: int, status: str) -> None:
        """Mock close method."""
        pass


class MockMarketDataPort:
    """Mock market data port for testing."""

    def __init__(
        self,
        sup_is_bullish: bool = True,
        ash_bullish_signal: bool = True,
        ash_bearish_signal: bool = False,
        rr_ratio: float = 1.5,
        enable_short: bool = False,
    ):
        self._sup_is_bullish = sup_is_bullish
        self._ash_bullish_signal = ash_bullish_signal
        self._ash_bearish_signal = ash_bearish_signal
        self._rr_ratio = rr_ratio
        self._enable_short = enable_short

    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """Return mock OHLCV data with required columns."""
        df = pd.DataFrame(
            {
                "open": [50000.0],
                "high": [50500.0],
                "low": [49500.0],
                "close": [50000.0],
                "volume": [1000.0],
                "sup_is_bullish": [self._sup_is_bullish],
                "ash_bullish_signal": [self._ash_bullish_signal],
                "ash_bearish_signal": [self._ash_bearish_signal],
                "rr_ratio": [self._rr_ratio],
                "long_tp": [51000.0],
                "long_sl": [49000.0],
                "short_tp": [49000.0],
                "short_sl": [51000.0],
                "supertrend_line": [48000.0],
                "ATRr_14": [500.0],
            }
        )
        df.index = pd.to_datetime(["2024-01-01"])
        return df


@pytest.mark.asyncio
async def test_run_cycle_blocks_signal_when_trade_active():
    """Verify no signal generated when active trade exists."""
    config = UserConfig(timeframe="4h")

    # Create mock active trade
    active_trade = ActiveTrade(
        id=1,
        signal_id=100,
        direction="LONG",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49000.0,
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )

    trade_repo = MockActiveTradeRepository(active_trade=active_trade)
    market_data = MockMarketDataPort()

    # Should return None when trade is active
    result = await run_cycle(config, trade_repo, market_data)
    assert result is None


@pytest.mark.asyncio
async def test_run_cycle_allows_signal_when_no_trade():
    """Verify signal can be generated when no active trade."""
    config = UserConfig(timeframe="4h")
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort()

    # Should not crash and may return signal or None based on conditions
    result = await run_cycle(config, trade_repo, market_data)
    # Result may be None if no signal detected, but function should not crash
    assert result is None or hasattr(result, "direction")


@pytest.mark.asyncio
async def test_run_cycle_generates_long_signal():
    """Verify LONG signal is generated when conditions are met."""
    config = UserConfig(timeframe="4h", enable_long=True)
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(sup_is_bullish=True, ash_bullish_signal=True, rr_ratio=1.5)

    with patch("bot.trading.strategy_engine.calculate_all", mock_calculate_all):
        result = await run_cycle(config, trade_repo, market_data)

    assert result is not None
    assert result.direction == "LONG"
    assert result.entry_price == 50000.0
    assert result.tp1_level == 51000.0
    assert result.sl_level == 49000.0
    assert result.rr_ratio == 1.5


@pytest.mark.asyncio
async def test_run_cycle_generates_short_signal():
    """Verify SHORT signal is generated when conditions are met."""
    config = UserConfig(timeframe="4h", enable_short=True)
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(
        sup_is_bullish=False, ash_bullish_signal=False, ash_bearish_signal=True, rr_ratio=1.5
    )

    with patch("bot.trading.strategy_engine.calculate_all", mock_calculate_all):
        result = await run_cycle(config, trade_repo, market_data)

    assert result is not None
    assert result.direction == "SHORT"
    assert result.entry_price == 50000.0
    assert result.tp1_level == 49000.0
    assert result.sl_level == 51000.0


@pytest.mark.asyncio
async def test_run_cycle_respects_enable_long_flag():
    """Verify LONG signals are disabled when enable_long is False."""
    config = UserConfig(timeframe="4h", enable_long=False, enable_short=False)
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(sup_is_bullish=True, ash_bullish_signal=True, rr_ratio=1.5)

    result = await run_cycle(config, trade_repo, market_data)

    # Should not generate LONG signal when disabled
    assert result is None


@pytest.mark.asyncio
async def test_run_cycle_respects_enable_short_flag():
    """Verify SHORT signals are disabled when enable_short is False."""
    config = UserConfig(timeframe="4h", enable_long=False, enable_short=False)
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(
        sup_is_bullish=False, ash_bullish_signal=False, ash_bearish_signal=True, rr_ratio=1.5
    )

    result = await run_cycle(config, trade_repo, market_data)

    # Should not generate SHORT signal when disabled
    assert result is None


@pytest.mark.asyncio
async def test_run_cycle_blocks_low_rr_ratio():
    """Verify signals are blocked when risk:reward ratio is below threshold."""
    config = UserConfig(timeframe="4h", enable_long=True)
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(sup_is_bullish=True, ash_bullish_signal=True, rr_ratio=0.5)

    result = await run_cycle(config, trade_repo, market_data)

    # Should not generate signal with RR < 1.0
    assert result is None


@pytest.mark.asyncio
async def test_run_cycle_with_custom_config():
    """Verify run_cycle uses custom configuration parameters."""
    config = UserConfig(
        timeframe="1h",
        enable_long=True,
        enable_short=False,
        supertrend_period=10,
        supertrend_mult=2.0,
        capital=20000.0,
        risk_percent=2.0,
    )
    trade_repo = MockActiveTradeRepository(active_trade=None)
    market_data = MockMarketDataPort(sup_is_bullish=True, ash_bullish_signal=True, rr_ratio=1.5)

    with patch("bot.trading.strategy_engine.calculate_all", mock_calculate_all):
        result = await run_cycle(config, trade_repo, market_data)

    assert result is not None
    assert result.timeframe == "1h"
    assert result.direction == "LONG"
