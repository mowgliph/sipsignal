"""
Tests para journal_handler.py - /journal y /active commands
"""

import os
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestJournalEmojiMapping:
    """Tests para el mapeo de emojis según resultado/status"""

    @pytest.mark.parametrize(
        "result,status,expected_emoji",
        [
            ("GANADA", None, "🏆"),
            ("PERDIDA", None, "📉"),
            ("BREAKEVEN", None, "⚖️"),
            (None, "NO_TOMADA", "⏭️"),
            (None, "SIN_RESPUESTA", "❓"),
            (None, "TOMADA", "⏳"),
        ],
    )
    def test_emoji_mapping(self, result, status, expected_emoji):
        """Verifica que el emoji correcto se asigna según result y status"""
        from bot.handlers.journal_handler import get_signal_emoji

        emoji = get_signal_emoji(result, status)
        assert emoji == expected_emoji


class TestJournalStats:
    """Tests para cálculo de estadísticas del journal"""

    def test_calculate_stats_empty(self):
        """Estadísticas con lista vacía"""
        from bot.handlers.journal_handler import calculate_journal_stats

        stats = calculate_journal_stats([])
        assert stats["total"] == 0
        assert stats["taken"] == 0
        assert stats["winrate"] == 0
        assert stats["profit_factor"] == 0
        assert stats["pnl_total"] == 0

    def test_calculate_stats_with_signals(self):
        """Estadísticas con señales de prueba"""
        from bot.handlers.journal_handler import calculate_journal_stats

        signals = [
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "PERDIDA", "pnl_usdt": -50},
            {"result": "GANADA", "pnl_usdt": 80},
            {"result": "PERDIDA", "pnl_usdt": -40},
            {"result": "GANADA", "pnl_usdt": 120},
        ]
        stats = calculate_journal_stats(signals)

        assert stats["total"] == 5
        assert stats["taken"] == 5
        assert stats["wins"] == 3
        assert stats["losses"] == 2
        assert stats["winrate"] == 60.0
        # gross_profit = 100+80+120 = 300, gross_loss = 50+40 = 90
        assert stats["profit_factor"] == 300 / 90  # gross_profit / gross_loss
        assert stats["pnl_total"] == 210

    def test_best_worst_streak(self):
        """Cálculo de rachas"""
        from bot.handlers.journal_handler import calculate_journal_stats

        # W, W, W, L, L, W, W, L, W
        signals = [
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "PERDIDA", "pnl_usdt": -50},
            {"result": "PERDIDA", "pnl_usdt": -50},
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "GANADA", "pnl_usdt": 100},
            {"result": "PERDIDA", "pnl_usdt": -50},
            {"result": "GANADA", "pnl_usdt": 100},
        ]
        stats = calculate_journal_stats(signals)

        assert stats["best_streak"] == 3
        assert stats["worst_streak"] == 2


class TestJournalFormat:
    """Tests para formateo de mensajes"""

    def test_format_signal_line(self):
        """Formatear una línea de señal"""
        from bot.handlers.journal_handler import format_signal_line

        signal = {
            "detected_at": datetime(2026, 3, 15, 14, 30, tzinfo=UTC),
            "direction": "LONG",
            "entry_price": 45000.00,
            "result": "GANADA",
            "status": "CERRADA",
        }
        line = format_signal_line(signal)

        assert "🏆" in line
        assert "15/03" in line
        assert "LONG" in line
        assert "$45,000" in line
        assert "GANADA" in line

    def test_format_stats_block(self):
        """Formatear bloque de estadísticas"""
        from bot.handlers.journal_handler import format_stats_block

        stats = {
            "total": 10,
            "taken": 8,
            "winrate": 62.5,
            "profit_factor": 1.85,
            "pnl_total": 350.50,
            "best_streak": 4,
            "worst_streak": 2,
        }

        block = format_stats_block(stats, n=10)

        assert "📊" in block
        assert "Total: 10" in block
        assert "Tomadas: 8" in block
        assert "Winrate: 62%" in block
        assert "Profit Factor: 1.85" in block
        assert "$350.50" in block or "$+350.50" in block
        assert "Mejor racha: 4" in block
        assert "Peor racha: 2" in block


class TestActiveTrades:
    """Tests para el comando /active"""

    @pytest.mark.asyncio
    async def test_get_active_trades(self):
        """Obtener trades activos"""
        from bot.handlers.journal_handler import get_active_trades

        mock_signals = [
            {
                "id": 1,
                "direction": "LONG",
                "entry_price": 45000,
                "tp1_level": 46000,
                "sl_level": 44000,
            },
            {
                "id": 2,
                "direction": "SHORT",
                "entry_price": 45500,
                "tp1_level": 44500,
                "sl_level": 46500,
            },
        ]

        with patch("bot.handlers.journal_handler.fetch") as mock_fetch:
            mock_fetch.return_value = mock_signals

            with patch("bot.handlers.journal_handler.BinanceDataFetcher") as mock_fetcher:
                mock_instance = AsyncMock()
                mock_instance.get_current_price.return_value = 45250.00
                mock_fetcher.return_value.__aenter__.return_value = mock_instance

                trades = await get_active_trades()

                assert len(trades) == 2
                assert trades[0]["direction"] == "LONG"

    @pytest.mark.asyncio
    async def test_format_active_trade(self):
        """Formatear trade activo con precios"""
        from bot.handlers.journal_handler import format_active_trade

        trade = {
            "id": 1,
            "direction": "LONG",
            "entry_price": 45000.00,
            "tp1_level": 46000.00,
            "sl_level": 44000.00,
            "current_price": 45250.00,
        }

        formatted = await format_active_trade(trade, 45250.00)

        assert "LONG" in formatted
        assert "$45,000" in formatted
        assert "$45,250" in formatted
        assert "TP:" in formatted
        assert "SL:" in formatted
