"""
Telegram notifier implementation using NotifierPort.
"""

from telegram.error import BadRequest

from bot.domain.ports.notifier_port import NotifierPort
from bot.domain.signal import Signal
from bot.trading.signal_builder import build_signal_message
from bot.trading.strategy_engine import SignalDTO, UserConfig


class TelegramNotifier(NotifierPort):
    """Telegram notifier that sends signals and messages to users."""

    async def send_signal(
        self,
        bot,
        chat_id: int,
        signal: Signal,
        chart: bytes | None,
        ai_context: str,
        user_config: UserConfig,
    ) -> None:
        """
        Send a trading signal to the specified chat.

        Args:
            bot: Telegram bot instance
            chat_id: Target chat ID
            signal: Signal to send
            chart: Chart image bytes (or None)
            ai_context: AI analysis context
            user_config: User configuration for message formatting
        """
        signal_dto = SignalDTO(
            direction=signal.direction,
            entry_price=signal.entry_price,
            tp1_level=signal.tp1_level,
            sl_level=signal.sl_level,
            rr_ratio=signal.rr_ratio,
            atr_value=signal.atr_value,
            supertrend_line=signal.supertrend_line,
            timeframe=signal.timeframe,
            detected_at=signal.detected_at,
        )

        text, keyboard = await build_signal_message(
            signal_dto, user_config, ai_context, chart or b""
        )

        try:
            if chart:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=chart,
                    caption=text,
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                )
        except BadRequest as e:
            if "parse entities" in str(e) or "can't find end" in str(e):
                if chart:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=chart,
                        caption=text,
                        reply_markup=keyboard,
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                    )
            raise

    async def send_message(self, bot, chat_id: int, text: str) -> None:
        """
        Send a plain message to the specified chat.

        Args:
            bot: Telegram bot instance
            chat_id: Target chat ID
            text: Message text
        """
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    async def send_warning(self, bot, chat_id: int, text: str) -> None:
        """
        Send a warning message to the specified chat.

        Args:
            bot: Telegram bot instance
            chat_id: Target chat ID
            text: Warning text (prefixed with 🚨 if not present)
        """
        if not text.startswith("🚨 "):
            text = "🚨 " + text
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
