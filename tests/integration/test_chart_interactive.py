"""Integration tests for interactive chart feature."""

import pytest

from bot.handlers.chart_handler import build_chart_keyboard
from bot.trading.chart_capture import ChartCapture


@pytest.mark.asyncio
async def test_full_chart_interaction_flow():
    """Test complete chart interaction flow with real data."""
    capture = ChartCapture()

    try:
        # Capture with no indicators
        chart_bytes = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=False,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_bytes is not None
        assert len(chart_bytes) > 10000

        # Capture with EMA
        chart_ema = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=True,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_ema is not None

    finally:
        await capture.close()


def test_keyboard_callback_data_length():
    """Test all callback data fits within Telegram limits."""
    # Test with all indicators active (longest callback data)
    keyboard = build_chart_keyboard(
        "BTCUSDT",
        "4h",
        show_ema=True,
        show_bb=True,
        show_rsi=True,
        show_pivots=True,
    )

    for row in keyboard.inline_keyboard:
        for button in row:
            callback_length = len(button.callback_data.encode("utf-8"))
            assert callback_length <= 64, (
                f"Callback too long: {button.callback_data} ({callback_length} bytes)"
            )


@pytest.mark.asyncio
async def test_chart_multiple_symbols():
    """Test chart generation for multiple symbols."""
    capture = ChartCapture()

    try:
        for symbol in ["BTCUSDT", "ETHUSDT"]:
            chart_bytes = await capture.capture(symbol, "4h")
            assert chart_bytes is not None
            assert len(chart_bytes) > 10000

    finally:
        await capture.close()


@pytest.mark.asyncio
async def test_chart_multiple_timeframes():
    """Test chart generation for multiple timeframes."""
    capture = ChartCapture()

    try:
        for tf in ["1h", "4h", "1d"]:
            chart_bytes = await capture.capture(
                "BTCUSDT",
                tf,
                show_ema=False,
                show_bb=False,
                show_rsi=False,
                show_pivots=False,
            )
            assert chart_bytes is not None

    finally:
        await capture.close()


@pytest.mark.asyncio
async def test_chart_indicator_toggle_flow():
    """Test that toggling indicators regenerates chart with correct state."""
    capture = ChartCapture()

    try:
        # Capture with no indicators
        chart_none = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=False,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_none is not None

        # Capture with EMA only
        chart_ema = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=True,
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_ema is not None

        # Capture with EMA + BB
        chart_ema_bb = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=True,
            show_bb=True,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_ema_bb is not None

        # Toggle EMA off (only BB active)
        chart_bb_only = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=False,
            show_bb=True,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_bb_only is not None

        # Verify cache is working (same params = same bytes)
        chart_bb_cached = await capture.capture(
            "BTCUSDT",
            "4h",
            show_ema=False,
            show_bb=True,
            show_rsi=False,
            show_pivots=False,
        )
        assert chart_bb_only == chart_bb_cached

    finally:
        await capture.close()
