"""Tests for chart inline keyboard builder."""

from bot.handlers.chart_handler import build_chart_keyboard, parse_bool


def test_parse_bool_t_to_true():
    """Test T string parses to True boolean."""
    assert parse_bool("T") is True


def test_parse_bool_f_to_false():
    """Test F string parses to False boolean."""
    assert parse_bool("F") is False


def test_parse_bool_case_insensitive():
    """Test parsing is case insensitive."""
    assert parse_bool("t") is True
    assert parse_bool("f") is False
    assert parse_bool("T") is True
    assert parse_bool("F") is False


def test_parse_bool_true_string():
    """Test 'True' string parses to True boolean."""
    assert parse_bool("True") is True
    assert parse_bool("true") is True
    assert parse_bool("TRUE") is True


def test_parse_bool_false_string():
    """Test 'False' string parses to False boolean."""
    assert parse_bool("False") is False
    assert parse_bool("false") is False
    assert parse_bool("FALSE") is False


def test_build_keyboard_defaults():
    """Test keyboard with default values (no indicators)."""
    keyboard = build_chart_keyboard("BTCUSDT", "4h")

    # Verify structure: 3 rows
    assert len(keyboard.inline_keyboard) == 3

    # Row 1: 5 timeframe buttons
    assert len(keyboard.inline_keyboard[0]) == 5

    # Row 2: 4 indicator buttons
    assert len(keyboard.inline_keyboard[1]) == 4

    # Row 3: 1 refresh button
    assert len(keyboard.inline_keyboard[2]) == 1


def test_build_keyboard_active_timeframe():
    """Test that active timeframe has checkmark."""
    keyboard = build_chart_keyboard("BTCUSDT", "4h")

    # Find 4H button
    tf_buttons = keyboard.inline_keyboard[0]
    h4_button = tf_buttons[1]  # 4h is second button

    assert "✅" in h4_button.text
    assert "4H" in h4_button.text

    # Other buttons should not have checkmark
    h1_button = tf_buttons[2]
    assert "✅" not in h1_button.text


def test_build_keyboard_with_ema():
    """Test keyboard with EMA activated."""
    keyboard = build_chart_keyboard("BTCUSDT", "4h", show_ema=True)

    # Find EMA button
    ind_buttons = keyboard.inline_keyboard[1]
    ema_button = ind_buttons[0]

    assert "✅" in ema_button.text
    assert "EMA" in ema_button.text

    # Callback should toggle EMA off next
    assert "|ema|F" in ema_button.callback_data


def test_build_keyboard_callback_data_format():
    """Test callback data format fits within limits."""
    keyboard = build_chart_keyboard(
        "BTCUSDT",
        "4h",
        show_ema=True,
        show_bb=True,
        show_rsi=True,
        show_pivots=True,
    )

    # Check all callback data is under 64 bytes
    for row in keyboard.inline_keyboard:
        for button in row:
            assert len(button.callback_data.encode()) <= 64, (
                f"Callback data too long: {button.callback_data}"
            )


def test_build_keyboard_all_timeframes():
    """Test all timeframe buttons have correct callback data."""
    keyboard = build_chart_keyboard("BTCUSDT", "1h")

    tf_buttons = keyboard.inline_keyboard[0]
    expected_timeframes = ["1d", "4h", "1h", "15m", "30m"]

    for i, expected_tf in enumerate(expected_timeframes):
        button = tf_buttons[i]
        assert f"|BTCUSDT|{expected_tf}|" in button.callback_data

        # Only 1h should have checkmark
        if expected_tf == "1h":
            assert "✅" in button.text
        else:
            assert "✅" not in button.text


def test_build_keyboard_indicator_toggles():
    """Test indicator buttons toggle correctly."""
    # Test with all indicators off
    keyboard = build_chart_keyboard("BTCUSDT", "4h")
    ind_buttons = keyboard.inline_keyboard[1]

    # All should toggle ON (T) when clicked
    assert "|ema|T" in ind_buttons[0].callback_data
    assert "|bb|T" in ind_buttons[1].callback_data
    assert "|rsi|T" in ind_buttons[2].callback_data
    assert "|pivots|T" in ind_buttons[3].callback_data

    # Test with all indicators on
    keyboard = build_chart_keyboard(
        "BTCUSDT", "4h", show_ema=True, show_bb=True, show_rsi=True, show_pivots=True
    )
    ind_buttons = keyboard.inline_keyboard[1]

    # All should toggle OFF (F) when clicked
    assert "|ema|F" in ind_buttons[0].callback_data
    assert "|bb|F" in ind_buttons[1].callback_data
    assert "|rsi|F" in ind_buttons[2].callback_data
    assert "|pivots|F" in ind_buttons[3].callback_data
