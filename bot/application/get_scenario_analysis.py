from bot.domain.ports import AIAnalysisPort, MarketDataPort
from bot.trading.technical_analysis import calculate_all

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


class GetScenarioAnalysis:
    def __init__(
        self,
        market_data: MarketDataPort,
        ai: AIAnalysisPort,
    ):
        self._market_data = market_data
        self._ai = ai

    async def execute(self) -> str:
        df = await self._market_data.get_ohlcv("BTCUSDT", "1d", 100)

        df = calculate_all(df, DEFAULT_ANALYSIS_CONFIG)

        last = df.iloc[-1]

        price = float(last["close"])
        trend = "ALCISTA" if last["sup_is_bullish"] else "BAJISTA"

        rsi = None
        if "rsi" in last.index:
            rsi = float(last["rsi"])

        ema_position: str | None = None
        if "ema_20" in last.index:
            ema_20 = float(last["ema_20"])
            ema_position = "sobre EMA-20" if price > ema_20 else "bajo EMA-20"

        summary_parts = [
            f"Precio actual: ${price:,.2f}",
            f"Tendencia: {trend}",
        ]

        if rsi is not None:
            summary_parts.append(f"RSI: {rsi:.2f}")

        if ema_position is not None:
            summary_parts.append(f"Precio: {ema_position}")

        analysis = await self._ai.analyze_scenario()
        return analysis
