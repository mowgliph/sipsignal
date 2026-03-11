from datetime import UTC, datetime

from bot.domain.ports import AIAnalysisPort, ChartPort, MarketDataPort
from bot.domain.signal import Signal
from bot.utils.logger import logger

DEFAULT_ANALYSIS_CONFIG = {
    "supertrend_period": 14,
    "supertrend_mult": 1.8,
    "ash_length": 14,
    "ash_smooth": 4,
    "tp_period": 14,
    "sl_period": 14,
    "tp_mult": 1.5,
    "sl_mult": 1.5,
}


class GetSignalAnalysis:
    def __init__(
        self,
        market_data: MarketDataPort,
        chart: ChartPort,
        ai: AIAnalysisPort,
    ):
        self._market_data = market_data
        self._chart = chart
        self._ai = ai

    async def execute(self, timeframe: str = "1h") -> dict:
        df = await self._market_data.get_ohlcv("BTCUSDT", timeframe, 200)

        from bot.trading.technical_analysis import calculate_all

        df = calculate_all(df, DEFAULT_ANALYSIS_CONFIG)

        last = df.iloc[-1]
        atr_col = f"ATRr_{DEFAULT_ANALYSIS_CONFIG['tp_period']}"

        signal = Signal(
            id=None,
            direction="LONG",
            entry_price=float(last["close"]),
            tp1_level=float(last["long_tp"]),
            sl_level=float(last["long_sl"]),
            rr_ratio=float(last["rr_ratio"]),
            atr_value=float(last[atr_col]),
            supertrend_line=float(last["supertrend_line"]),
            timeframe=timeframe,
            detected_at=datetime.now(UTC),
            status="ANALISIS",
        )

        ai_context = ""
        try:
            ai_context = await self._ai.analyze_signal(signal)
        except Exception as e:
            logger.warning(f"AI analysis failed in GetSignalAnalysis: {e}")

        chart_bytes = None
        try:
            chart_bytes = await self._chart.capture("BTCUSDT", timeframe)
        except Exception as e:
            logger.warning(f"Chart capture failed in GetSignalAnalysis: {e}")

        return {
            "signal": signal,
            "ai_context": ai_context,
            "chart_bytes": chart_bytes,
        }
