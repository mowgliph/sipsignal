"""
Tests para strategy_engine.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from bot.trading.strategy_engine import Database, SignalDTO, UserConfig, run_cycle


def _create_test_df() -> pd.DataFrame:
    """Crea un DataFrame de test con datos válidos."""
    np.random.seed(42)
    n = 50
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.random.rand(n) * 3
    low = close - np.random.rand(n) * 3
    open_price = low + np.random.rand(n) * (high - low)

    return pd.DataFrame({"open": open_price, "high": high, "low": low, "close": close}, index=dates)


def _create_mock_df_with_signals(
    is_bullish: bool, ash_signal: bool, rr_ratio: float, direction: str
) -> pd.DataFrame:
    """Crea un DataFrame con las columnas necesarias para la señal."""
    mock_df = _create_test_df()
    mock_df["supertrend_line"] = 95.0
    mock_df["sup_is_bullish"] = not is_bullish
    mock_df["sup_cross_bullish"] = False
    mock_df["sup_cross_bearish"] = False
    mock_df["ash_smth_bulls"] = 1.0
    mock_df["ash_smth_bears"] = 0.5
    mock_df["ash_difference"] = 0.8
    mock_df["ash_bullish"] = is_bullish if direction == "LONG" else False
    mock_df["ash_bearish"] = not is_bullish if direction == "SHORT" else False
    mock_df["ash_neutral"] = not is_bullish
    mock_df["ash_bullish_signal"] = is_bullish and ash_signal and direction == "LONG"
    mock_df["ash_bearish_signal"] = not is_bullish and ash_signal and direction == "SHORT"
    mock_df["ATRr_14"] = 2.0
    mock_df["long_tp"] = 105.0
    mock_df["long_sl"] = 97.0
    mock_df["short_tp"] = 95.0
    mock_df["short_sl"] = 103.0
    mock_df["rr_ratio"] = rr_ratio

    idx = mock_df.index[-1]
    mock_df.loc[idx, "sup_is_bullish"] = is_bullish
    if direction == "LONG":
        mock_df.loc[idx, "ash_bullish_signal"] = ash_signal
        mock_df.loc[idx, "ash_bearish_signal"] = False
    else:
        mock_df.loc[idx, "ash_bullish_signal"] = False
        mock_df.loc[idx, "ash_bearish_signal"] = ash_signal

    return mock_df


class TestReturnsNoneIfActiveTrade:
    """Tests para verificar que no hay señal cuando hay trade activo."""

    @pytest.mark.asyncio
    async def test_returns_none_if_active_trade(self):
        """Debe retornar None si ya hay una operación activa."""
        config = UserConfig(timeframe="1h", enable_long=True, enable_short=True)

        mock_df = _create_test_df()

        with patch("bot.trading.strategy_engine.BinanceDataFetcher") as mock_fetcher:
            mock_instance = AsyncMock()
            mock_instance.get_ohlcv = AsyncMock(return_value=mock_df)
            mock_instance.close = AsyncMock()
            mock_fetcher.return_value = mock_instance

            with patch.object(Database, "fetch_active_trade", new_callable=AsyncMock) as mock_db:
                mock_db.return_value = {"id": 1, "direction": "LONG"}

                result = await run_cycle(config)

                assert result is None


class TestLongSignal:
    """Tests para señales LONG."""

    @pytest.mark.asyncio
    async def test_long_signal_when_both_conditions(self):
        """Debe retornar SignalDTO LONG cuando supertrend bullish + ASH bullish signal + RR >= 1."""
        config = UserConfig(timeframe="1h", enable_long=True, enable_short=False)

        mock_df = _create_mock_df_with_signals(
            is_bullish=True, ash_signal=True, rr_ratio=1.5, direction="LONG"
        )

        with patch("bot.trading.strategy_engine.BinanceDataFetcher") as mock_fetcher:
            mock_instance = AsyncMock()
            mock_instance.get_ohlcv = AsyncMock(return_value=mock_df)
            mock_instance.close = AsyncMock()
            mock_fetcher.return_value = mock_instance

            with (
                patch("bot.trading.strategy_engine.calculate_all", return_value=mock_df),
                patch.object(Database, "fetch_active_trade", new_callable=AsyncMock) as mock_db,
            ):
                mock_db.return_value = None

                result = await run_cycle(config)

                assert result is not None
                assert result.direction == "LONG"
                assert result.entry_price == mock_df["close"].iloc[-1]
                assert result.tp1_level == mock_df["long_tp"].iloc[-1]
                assert result.sl_level == mock_df["long_sl"].iloc[-1]
                assert result.rr_ratio >= 1.0


class TestRrRatio:
    """Tests para validación de ratio riesgo/beneficio."""

    @pytest.mark.asyncio
    async def test_no_signal_when_rr_below_1(self):
        """Debe retornar None cuando RR ratio < 1.0."""
        config = UserConfig(timeframe="1h", enable_long=True, enable_short=True)

        mock_df = _create_mock_df_with_signals(
            is_bullish=True, ash_signal=True, rr_ratio=0.8, direction="LONG"
        )

        with patch("bot.trading.strategy_engine.BinanceDataFetcher") as mock_fetcher:
            mock_instance = AsyncMock()
            mock_instance.get_ohlcv = AsyncMock(return_value=mock_df)
            mock_instance.close = AsyncMock()
            mock_fetcher.return_value = mock_instance

            with (
                patch("bot.trading.strategy_engine.calculate_all", return_value=mock_df),
                patch.object(Database, "fetch_active_trade", new_callable=AsyncMock) as mock_db,
            ):
                mock_db.return_value = None

                result = await run_cycle(config)

                assert result is None


class TestShortSignal:
    """Tests para señales SHORT."""

    @pytest.mark.asyncio
    async def test_short_signal_when_conditions_met(self):
        """Debe retornar SignalDTO SHORT cuando supertrend bearish + ASH bearish signal + RR >= 1."""
        config = UserConfig(timeframe="1h", enable_long=False, enable_short=True)

        mock_df = _create_mock_df_with_signals(
            is_bullish=False, ash_signal=True, rr_ratio=1.5, direction="SHORT"
        )

        with patch("bot.trading.strategy_engine.BinanceDataFetcher") as mock_fetcher:
            mock_instance = AsyncMock()
            mock_instance.get_ohlcv = AsyncMock(return_value=mock_df)
            mock_instance.close = AsyncMock()
            mock_fetcher.return_value = mock_instance

            with (
                patch("bot.trading.strategy_engine.calculate_all", return_value=mock_df),
                patch.object(Database, "fetch_active_trade", new_callable=AsyncMock) as mock_db,
            ):
                mock_db.return_value = None

                result = await run_cycle(config)

                assert result is not None
                assert result.direction == "SHORT"
                assert result.entry_price == mock_df["close"].iloc[-1]
                assert result.tp1_level == mock_df["short_tp"].iloc[-1]
                assert result.sl_level == mock_df["short_sl"].iloc[-1]


class TestSignalDTO:
    """Tests para el dataclass SignalDTO."""

    def test_signal_dto_creation(self):
        """Verifica que SignalDTO se crea correctamente."""
        dto = SignalDTO(
            direction="LONG",
            entry_price=100.0,
            tp1_level=105.0,
            sl_level=97.0,
            rr_ratio=1.5,
            atr_value=2.0,
            supertrend_line=99.0,
            timeframe="1h",
            detected_at=datetime.now(UTC),
        )

        assert dto.direction == "LONG"
        assert dto.entry_price == 100.0
        assert dto.tp1_level == 105.0
        assert dto.sl_level == 97.0
        assert dto.rr_ratio == 1.5
        assert dto.atr_value == 2.0
        assert dto.supertrend_line == 99.0
        assert dto.timeframe == "1h"
        assert isinstance(dto.detected_at, datetime)


class TestUserConfig:
    """Tests para el dataclass UserConfig."""

    def test_user_config_defaults(self):
        """Verifica los valores por defecto de UserConfig."""
        config = UserConfig(timeframe="4h")

        assert config.timeframe == "4h"
        assert config.enable_long is True
        assert config.enable_short is True
        assert config.supertrend_period == 14
        assert config.supertrend_mult == 1.8
        assert config.ash_length == 14
        assert config.ash_smooth == 4
        assert config.tp_period == 14
        assert config.sl_period == 14
        assert config.tp_mult == 1.5
        assert config.sl_mult == 1.5

    def test_user_config_custom(self):
        """Verifica valores personalizados de UserConfig."""
        config = UserConfig(
            timeframe="15m",
            enable_long=False,
            enable_short=True,
            supertrend_period=10,
            supertrend_mult=2.0,
            tp_mult=2.0,
            sl_mult=1.0,
        )

        assert config.timeframe == "15m"
        assert config.enable_long is False
        assert config.enable_short is True
        assert config.supertrend_period == 10
        assert config.supertrend_mult == 2.0
        assert config.tp_mult == 2.0
        assert config.sl_mult == 1.0
