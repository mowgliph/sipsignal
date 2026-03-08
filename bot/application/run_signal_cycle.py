from datetime import UTC, datetime

from loguru import logger

from bot.domain.ports import (
    ActiveTradeRepository,
    AIAnalysisPort,
    ChartPort,
    MarketDataPort,
    NotifierPort,
    SignalRepository,
)
from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig

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


class RunSignalCycle:
    def __init__(
        self,
        market_data: MarketDataPort,
        signal_repo: SignalRepository,
        trade_repo: ActiveTradeRepository,
        chart: ChartPort,
        ai: AIAnalysisPort,
        notifier: NotifierPort,
        admin_chat_ids: list[int],
    ):
        self._market_data = market_data
        self._signal_repo = signal_repo
        self._trade_repo = trade_repo
        self._chart = chart
        self._ai = ai
        self._notifier = notifier
        self._admin_chat_ids = admin_chat_ids

    async def execute(self, user_config: UserConfig) -> Signal | None:
        try:
            active_trade = await self._trade_repo.get_active()
            if active_trade is not None:
                return None

            timeframe = user_config.timeframe
            df = await self._market_data.get_ohlcv("BTCUSDT", timeframe, 200)

            from bot.trading.technical_analysis import calculate_all

            df = calculate_all(df, DEFAULT_ANALYSIS_CONFIG)

            last = df.iloc[-1]

            signal = None
            if last["sup_is_bullish"] and last["ash_bullish_signal"] and last["rr_ratio"] >= 1.0:
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
                )
            elif (
                not last["sup_is_bullish"]
                and last["ash_bearish_signal"]
                and last["rr_ratio"] >= 1.0
            ):
                atr_col = f"ATRr_{DEFAULT_ANALYSIS_CONFIG['tp_period']}"
                signal = Signal(
                    id=None,
                    direction="SHORT",
                    entry_price=float(last["close"]),
                    tp1_level=float(last["short_tp"]),
                    sl_level=float(last["short_sl"]),
                    rr_ratio=float(last["rr_ratio"]),
                    atr_value=float(last[atr_col]),
                    supertrend_line=float(last["supertrend_line"]),
                    timeframe=timeframe,
                    detected_at=datetime.now(UTC),
                )

            if signal is None:
                return None

            chart_bytes = await self._chart.capture("BTCUSDT", timeframe)

            ai_context = ""
            try:
                ai_context = await self._ai.analyze_signal(signal)
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
                ai_context = ""

            for chat_id in self._admin_chat_ids:
                await self._notifier.send_signal(chat_id, signal, chart_bytes, ai_context)

            saved_signal = await self._signal_repo.save(signal)
            signal.id = saved_signal.id

            return signal

        except Exception as e:
            logger.error(f"Error in RunSignalCycle: {e}")
            return None
