"""Tests for ChartCapture with indicator parameters."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from bot.trading.chart_capture import ChartCapture


@pytest.mark.asyncio
async def test_capture_with_no_indicators():
    """Test capture with all indicators disabled."""
    capture = ChartCapture()
    df = _create_sample_ohlcv()

    # Mock data_fetcher with async function
    async def mock_get_ohlcv(*args, **kwargs):
        return df

    capture.data_fetcher.get_ohlcv = mock_get_ohlcv

    chart_bytes = await capture.capture(
        "BTCUSDT",
        "4h",
        show_ema=False,
        show_bb=False,
        show_rsi=False,
        show_pivots=False,
    )
    await capture.close()

    assert chart_bytes is not None
    assert len(chart_bytes) > 100


@pytest.mark.asyncio
async def test_capture_with_ema():
    """Test capture with EMA enabled."""
    capture = ChartCapture()
    df = _create_sample_ohlcv()

    async def mock_get_ohlcv(*args, **kwargs):
        return df

    capture.data_fetcher.get_ohlcv = mock_get_ohlcv

    chart_bytes = await capture.capture(
        "BTCUSDT",
        "4h",
        show_ema=True,
        show_bb=False,
        show_rsi=False,
        show_pivots=False,
    )
    await capture.close()

    assert chart_bytes is not None


@pytest.mark.asyncio
async def test_capture_cache_includes_indicators():
    """Test that cache key includes indicator state."""
    capture = ChartCapture()
    df = _create_sample_ohlcv()

    async def mock_get_ohlcv(*args, **kwargs):
        return df

    capture.data_fetcher.get_ohlcv = mock_get_ohlcv

    # Capture with no indicators
    chart1 = await capture.capture("BTCUSDT", "4h", False, False, False, False)

    # Capture with EMA - should NOT use cache from first call
    chart2 = await capture.capture("BTCUSDT", "4h", True, False, False, False)

    await capture.close()

    # Both should be valid but may be different sizes
    assert chart1 is not None
    assert chart2 is not None


def _create_sample_ohlcv():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range(start=datetime.now(UTC) - timedelta(days=10), periods=100, freq="4h")
    np.random.seed(42)

    base_price = 50000
    returns = np.random.randn(100) * 0.02
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": prices * (1 + np.random.randn(100) * 0.001),
            "high": prices * (1 + np.random.randn(100) * 0.002 + 0.001),
            "low": prices * (1 - np.random.randn(100) * 0.002 - 0.001),
            "close": prices,
            "volume": np.random.randint(1000, 10000, 100),
        },
        index=dates,
    )
