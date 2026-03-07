"""
Motor de detección de señales TZ.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from trading.data_fetcher import BinanceDataFetcher
from trading.technical_analysis import calculate_all


@dataclass
class SignalDTO:
    direction: str
    entry_price: float
    tp1_level: float
    sl_level: float
    rr_ratio: float
    atr_value: float
    supertrend_line: float
    timeframe: str
    detected_at: datetime


@dataclass
class UserConfig:
    timeframe: str
    enable_long: bool = True
    enable_short: bool = True
    supertrend_period: int = 14
    supertrend_mult: float = 1.8
    ash_length: int = 14
    ash_smooth: int = 4
    tp_period: int = 14
    sl_period: int = 14
    tp_mult: float = 1.5
    sl_mult: float = 1.5
    capital: float = 10000.0
    risk_percent: float = 1.0


class Database:
    """Mock database para operaciones de trade."""

    @staticmethod
    async def fetch_active_trade() -> dict | None:
        """
        Retorna el trade activo actual o None si no hay operación abierta.
        Implementación placeholder - debe integrarse con PostgreSQL.
        """
        return None


async def run_cycle(config: UserConfig) -> SignalDTO | None:
    """
    Ejecuta un ciclo de análisis de estrategia.

    Args:
        config: Configuración del usuario para el análisis

    Returns:
        SignalDTO si hay señal, None otherwise
    """
    fetcher = BinanceDataFetcher()
    try:
        df = await fetcher.get_ohlcv("BTCUSDT", config.timeframe, 200)

        config_dict = {
            "supertrend_period": config.supertrend_period,
            "supertrend_mult": config.supertrend_mult,
            "ash_length": config.ash_length,
            "ash_smooth": config.ash_smooth,
            "tp_period": config.tp_period,
            "sl_period": config.sl_period,
            "tp_mult": config.tp_mult,
            "sl_mult": config.sl_mult,
        }

        df = calculate_all(df, config_dict)

        last = df.iloc[-1]

        active = await Database.fetch_active_trade()
        if active:
            return None

        if config.enable_long and last["sup_is_bullish"] and last["ash_bullish_signal"]:
            if last["rr_ratio"] >= 1.0:
                atr_col = f"ATRr_{config.tp_period}"
                return SignalDTO(
                    direction="LONG",
                    entry_price=float(last["close"]),
                    tp1_level=float(last["long_tp"]),
                    sl_level=float(last["long_sl"]),
                    rr_ratio=float(last["rr_ratio"]),
                    atr_value=float(last[atr_col]),
                    supertrend_line=float(last["supertrend_line"]),
                    timeframe=config.timeframe,
                    detected_at=datetime.now(UTC),
                )

        if config.enable_short and not last["sup_is_bullish"] and last["ash_bearish_signal"]:
            if last["rr_ratio"] >= 1.0:
                atr_col = f"ATRr_{config.tp_period}"
                return SignalDTO(
                    direction="SHORT",
                    entry_price=float(last["close"]),
                    tp1_level=float(last["short_tp"]),
                    sl_level=float(last["short_sl"]),
                    rr_ratio=float(last["rr_ratio"]),
                    atr_value=float(last[atr_col]),
                    supertrend_line=float(last["supertrend_line"]),
                    timeframe=config.timeframe,
                    detected_at=datetime.now(UTC),
                )

        return None

    finally:
        await fetcher.close()
