"""
Tests para trading/drawdown_manager.py
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest


class TestDrawdownManager:
    """Tests para el módulo de gestión de drawdown."""

    @pytest.mark.asyncio
    async def test_get_or_create_drawdown_creates_new(self):
        """Debe crear un nuevo drawdown si no existe."""
        with (
            patch("trading.drawdown_manager.fetchrow") as mock_fetch,
            patch("trading.drawdown_manager.execute") as mock_exec,
        ):
            mock_fetch.return_value = None

            mock_fetch.side_effect = [
                None,
                {
                    "user_id": 1,
                    "current_drawdown_usdt": Decimal("0.00"),
                    "current_drawdown_percent": Decimal("0.000"),
                    "losses_count": 0,
                    "is_paused": False,
                },
            ]

            from trading.drawdown_manager import get_or_create_drawdown

            await get_or_create_drawdown(1)

            assert mock_exec.called

    @pytest.mark.asyncio
    async def test_reset_drawdown_zeros_values(self):
        """Reset debe poner drawdown a 0."""
        with (
            patch("trading.drawdown_manager.execute") as mock_exec,
            patch("trading.drawdown_manager.get_drawdown") as mock_get,
        ):
            mock_get.return_value = {
                "user_id": 1,
                "current_drawdown_usdt": Decimal("0.00"),
                "current_drawdown_percent": Decimal("0.000"),
                "losses_count": 0,
                "is_paused": False,
                "last_reset_at": None,
            }

            from trading.drawdown_manager import reset_drawdown

            await reset_drawdown(1)

            assert mock_exec.called

    @pytest.mark.asyncio
    async def test_resume_trading_sets_paused_false(self):
        """Resume debe establecer is_paused=False."""
        with (
            patch("trading.drawdown_manager.execute"),
            patch("trading.drawdown_manager.get_drawdown") as mock_get,
        ):
            mock_get.return_value = {
                "user_id": 1,
                "current_drawdown_usdt": Decimal("-100.00"),
                "current_drawdown_percent": Decimal("-10.000"),
                "losses_count": 3,
                "is_paused": False,
            }

            from trading.drawdown_manager import resume_trading

            result = await resume_trading(1)

            assert not result["is_paused"]

    @pytest.mark.asyncio
    async def test_get_drawdown_returns_current_state(self):
        """Get drawdown debe retornar el estado actual."""
        with patch("trading.drawdown_manager.fetchrow") as mock_fetch:
            mock_fetch.return_value = {
                "user_id": 1,
                "current_drawdown_usdt": Decimal("-250.00"),
                "current_drawdown_percent": Decimal("-2.500"),
                "losses_count": 5,
                "is_paused": False,
                "capital_total": Decimal("10000.00"),
                "max_drawdown_percent": Decimal("5.00"),
            }

            from trading.drawdown_manager import get_drawdown

            result = await get_drawdown(1)

            assert result is not None
            assert result["current_drawdown_usdt"] == Decimal("-250.00")
            assert result["losses_count"] == 5

    @pytest.mark.asyncio
    async def test_is_trading_paused_returns_false_when_not_paused(self):
        """is_trading_paused debe retornar False cuando no está pausado."""
        with patch("trading.drawdown_manager.fetchrow") as mock_fetch:
            mock_fetch.return_value = {"is_paused": False}

            from trading.drawdown_manager import is_trading_paused

            result = await is_trading_paused(1)

            assert not result

    @pytest.mark.asyncio
    async def test_is_trading_paused_returns_true_when_paused(self):
        """is_trading_paused debe retornar True cuando está pausado."""
        with patch("trading.drawdown_manager.fetchrow") as mock_fetch:
            mock_fetch.return_value = {"is_paused": True}

            from trading.drawdown_manager import is_trading_paused

            result = await is_trading_paused(1)

            assert result

    @pytest.mark.asyncio
    async def test_update_drawdown_calculates_correctly(self):
        """update_drawdown debe calcular correctamente el nuevo drawdown."""
        with (
            patch("trading.drawdown_manager.fetchrow") as mock_fetch,
            patch("trading.drawdown_manager.execute"),
            patch("trading.drawdown_manager.get_or_create_drawdown") as mock_get_or_create,
        ):
            mock_fetch.return_value = {
                "capital_total": Decimal("10000.00"),
                "max_drawdown_percent": Decimal("5.00"),
            }

            mock_get_or_create.return_value = {
                "user_id": 1,
                "current_drawdown_usdt": Decimal("-100.00"),
                "current_drawdown_percent": Decimal("-1.000"),
                "losses_count": 1,
                "is_paused": False,
            }

            mock_bot = AsyncMock()

            from trading.drawdown_manager import update_drawdown

            result = await update_drawdown(1, -50.0, mock_bot)

            assert result["current_drawdown_usdt"] == -150.0
            assert result["losses_count"] == 2
