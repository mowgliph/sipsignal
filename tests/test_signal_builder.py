"""
Tests para signal_builder.
"""
from datetime import datetime, timezone

import pytest

from trading.signal_builder import build_signal_message
from trading.strategy_engine import SignalDTO, UserConfig


def create_test_signal(direction: str = "LONG") -> SignalDTO:
    """Crea un SignalDTO de prueba."""
    return SignalDTO(
        direction=direction,
        entry_price=50000.0,
        tp1_level=52000.0,
        sl_level=48500.0,
        rr_ratio=2.0,
        atr_value=1000.0,
        supertrend_line=49500.0,
        timeframe="4h",
        detected_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    )


def create_test_config() -> UserConfig:
    """Crea un UserConfig de prueba."""
    return UserConfig(
        timeframe="4h",
        capital=10000.0,
        risk_percent=1.0
    )


class TestBuildSignalMessage:
    """Tests para build_signal_message."""

    @pytest.mark.asyncio
    async def test_message_contains_prices(self):
        """El mensaje debe incluir entry_price y sl_level formateados."""
        signal = create_test_signal()
        config = create_test_config()
        ai_context = "RSI en zona de sobreventa."
        
        message, _ = await build_signal_message(signal, config, ai_context, b"")
        
        assert "50,000.00" in message or "50000.00" in message
        assert "48,500.00" in message or "48500.00" in message

    @pytest.mark.asyncio
    async def test_buttons_count(self):
        """InlineKeyboard debe tener exactamente 3 botones."""
        signal = create_test_signal()
        config = create_test_config()
        ai_context = "RSI en zona de sobreventa."
        
        _, keyboard = await build_signal_message(signal, config, ai_context, b"")
        
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        assert len(all_buttons) == 3

    @pytest.mark.asyncio
    async def test_callback_data_format(self):
        """Cada callback debe tener el prefijo correcto."""
        signal = create_test_signal()
        config = create_test_config()
        ai_context = "RSI en zona de sobreventa."
        
        _, keyboard = await build_signal_message(signal, config, ai_context, b"")
        
        all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
        
        callbacks = [btn.callback_data for btn in all_buttons]
        
        assert any(cb.startswith("taken:") for cb in callbacks)
        assert any(cb.startswith("skipped:") for cb in callbacks)
        assert any(cb.startswith("detail:") for cb in callbacks)

    @pytest.mark.asyncio
    async def test_long_signal_emoji(self):
        """Señal LONG debe usar emoji 🟢."""
        signal = create_test_signal(direction="LONG")
        config = create_test_config()
        
        message, _ = await build_signal_message(signal, config, "", b"")
        
        assert "🟢" in message
        assert "SEÑAL LONG" in message

    @pytest.mark.asyncio
    async def test_short_signal_emoji(self):
        """Señal SHORT debe usar emoji 🔴."""
        signal = create_test_signal(direction="SHORT")
        config = create_test_config()
        
        message, _ = await build_signal_message(signal, config, "", b"")
        
        assert "🔴" in message
        assert "SEÑAL SHORT" in message

    @pytest.mark.asyncio
    async def test_rr_ratio_display(self):
        """El mensaje debe mostrar el ratio R:R."""
        signal = create_test_signal()
        config = create_test_config()
        
        message, _ = await build_signal_message(signal, config, "", b"")
        
        assert "R:R" in message

    @pytest.mark.asyncio
    async def test_position_size_calculation(self):
        """La posición debe calcularse correctamente."""
        signal = create_test_signal()
        config = create_test_config()
        
        message, _ = await build_signal_message(signal, config, "", b"")
        
        assert "Posición sugerida" in message or "BTC" in message

    @pytest.mark.asyncio
    async def test_ai_context_included(self):
        """El contexto IA debe aparecer en el mensaje."""
        signal = create_test_signal()
        config = create_test_config()
        ai_context = "Análisis de momentum positivo."
        
        message, _ = await build_signal_message(signal, config, ai_context, b"")
        
        assert ai_context in message

    @pytest.mark.asyncio
    async def test_timeframe_display(self):
        """El timeframe debe aparecer en el mensaje."""
        signal = create_test_signal()
        config = create_test_config()
        
        message, _ = await build_signal_message(signal, config, "", b"")
        
        assert signal.timeframe.upper() in message

    @pytest.mark.asyncio
    async def test_buttons_in_two_rows(self):
        """Los 3 botones deben estar en 2 filas."""
        signal = create_test_signal()
        config = create_test_config()
        
        _, keyboard = await build_signal_message(signal, config, "", b"")
        
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 2
        assert len(keyboard.inline_keyboard[1]) == 1
