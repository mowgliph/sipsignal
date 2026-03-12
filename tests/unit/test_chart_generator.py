"""Tests for chart_generator with optional indicators."""

import io
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from bot.utils.chart_generator import (
    COLOR_BG,
    COLOR_BRAND,
    COLOR_DOWN,
    COLOR_EMA20,
    COLOR_RSI,
    COLOR_UP,
    COLOR_WATERMARK,
    generate_ohlcv_chart,
)


def test_new_color_palette():
    """Test new TradingView-style colors are defined correctly."""
    # Background color (dark blue TradingView style)
    assert COLOR_BG == "#131722"

    # Candlestick colors
    assert COLOR_UP == "#089981"  # TradingView green
    assert COLOR_DOWN == "#F23645"  # Vibrant red

    # Indicator colors
    assert COLOR_EMA20 == "#2962FF"  # Bright blue
    assert COLOR_RSI == "#FF9800"  # Golden orange

    # Branding colors
    assert COLOR_BRAND == "#2962FF"  # Professional blue
    assert COLOR_WATERMARK == "#787B86"  # Medium gray


def test_generate_chart_no_indicators():
    """Test chart generation with all indicators disabled (default)."""
    df = _create_sample_ohlcv()

    buf = generate_ohlcv_chart(
        df,
        "BTCUSDT",
        "4h",
        show_ema=False,
        show_bb=False,
        show_rsi=False,
        show_pivots=False,
    )

    assert buf is not None
    assert isinstance(buf, io.BytesIO)
    buf.seek(0)
    assert buf.read()[:4] == b"\x89PNG"


def test_generate_chart_with_ema_only():
    """Test chart generation with only EMA enabled."""
    df = _create_sample_ohlcv()

    buf = generate_ohlcv_chart(
        df,
        "BTCUSDT",
        "4h",
        show_ema=True,
        show_bb=False,
        show_rsi=False,
        show_pivots=False,
    )

    assert buf is not None
    buf.seek(0)
    assert buf.read()[:4] == b"\x89PNG"


def test_generate_chart_with_all_indicators():
    """Test chart generation with all indicators enabled."""
    df = _create_sample_ohlcv()

    buf = generate_ohlcv_chart(
        df,
        "BTCUSDT",
        "4h",
        show_ema=True,
        show_bb=True,
        show_rsi=True,
        show_pivots=True,
        pivot=50000,
        r1=51000,
        s1=49000,
    )

    assert buf is not None


def test_generate_chart_default_params():
    """Test that default parameters disable all indicators."""
    df = _create_sample_ohlcv()

    # Call with minimal parameters
    buf = generate_ohlcv_chart(df, "BTCUSDT", "4h")

    # Should work and produce valid PNG
    assert buf is not None
    buf.seek(0)
    png_data = buf.read()
    assert png_data[:4] == b"\x89PNG"
    # Should be relatively small (no indicators = simpler chart)
    assert len(png_data) > 10000  # At least 10KB


def _create_sample_ohlcv() -> pd.DataFrame:
    """Create sample OHLCV DataFrame for testing."""

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
