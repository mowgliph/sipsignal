"""Unit tests for TelegramNotifier."""

import os
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.domain.signal import Signal
from bot.infrastructure.telegram.telegram_notifier import TelegramNotifier
from bot.trading.strategy_engine import UserConfig


@pytest.fixture
def notifier():
    return TelegramNotifier()


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot


@pytest.fixture
def sample_signal():
    return Signal(
        id=1,
        direction="LONG",
        entry_price=85000.0,
        tp1_level=86000.0,
        sl_level=84000.0,
        rr_ratio=2.5,
        atr_value=500.0,
        supertrend_line=84500.0,
        timeframe="4h",
        detected_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_config():
    return UserConfig(
        timeframe="4h",
        capital=10000.0,
        risk_percent=1.0,
    )


@pytest.mark.asyncio
async def test_send_signal_with_chart(notifier, mock_bot, sample_signal, sample_config):
    """Test sending signal with chart image."""
    chart_bytes = b"fake_image_data"
    ai_context = "BTC showing strong momentum"
    chat_id = 123456

    await notifier.send_signal(
        mock_bot, chat_id, sample_signal, chart_bytes, ai_context, sample_config
    )

    mock_bot.send_photo.assert_called_once()
    call_kwargs = mock_bot.send_photo.call_args.kwargs
    assert call_kwargs["chat_id"] == chat_id
    assert call_kwargs["photo"] == chart_bytes
    assert call_kwargs["caption"] is not None
    assert call_kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_signal_without_chart(notifier, mock_bot, sample_signal, sample_config):
    """Test sending signal without chart."""
    ai_context = "BTC showing strong momentum"
    chat_id = 123456

    await notifier.send_signal(mock_bot, chat_id, sample_signal, None, ai_context, sample_config)

    mock_bot.send_message.assert_called_once()
    call_kwargs = mock_bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == chat_id
    assert call_kwargs["text"] is not None
    assert call_kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_message(notifier, mock_bot):
    """Test sending plain message."""
    chat_id = 123456
    text = "Hello, world!"

    await notifier.send_message(mock_bot, chat_id, text)

    mock_bot.send_message.assert_called_once_with(chat_id=chat_id, text=text, parse_mode="Markdown")


@pytest.mark.asyncio
async def test_send_warning_without_prefix(notifier, mock_bot):
    """Test sending warning adds prefix if not present."""
    chat_id = 123456
    text = "Risk level exceeded"

    await notifier.send_warning(mock_bot, chat_id, text)

    mock_bot.send_message.assert_called_once()
    call_kwargs = mock_bot.send_message.call_args.kwargs
    assert call_kwargs["text"].startswith("🚨 ")


@pytest.mark.asyncio
async def test_send_warning_with_prefix(notifier, mock_bot):
    """Test sending warning does not duplicate prefix."""
    chat_id = 123456
    text = "🚨 Risk level exceeded"

    await notifier.send_warning(mock_bot, chat_id, text)

    mock_bot.send_message.assert_called_once()
    call_kwargs = mock_bot.send_message.call_args.kwargs
    assert call_kwargs["text"].startswith("🚨 ")
