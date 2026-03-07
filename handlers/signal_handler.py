# handlers/signal_handler.py

import asyncio
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from core.config import settings
from trading.data_fetcher import BinanceDataFetcher
from trading.technical_analysis import calculate_all
from trading.chart_capture import ChartCapture

DEFAULT_CONFIG = {
    'supertrend_period': 14,
    'supertrend_mult': 1.8,
    'ash_length': 14,
    'ash_smooth': 4,
    'tp_period': 14,
    'sl_period': 14,
    'tp_mult': 1.5,
    'sl_mult': 1.5,
}

CHART_CACHE_TTL = 300


async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado actual de Supertrend + ASH y señal activa para BTC/USDT 4H."""
    chat_id = update.effective_chat.id

    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    msg = await update.message.reply_text("⏳ *Analizando mercado...*", parse_mode=ParseMode.MARKDOWN)

    try:
        fetcher = BinanceDataFetcher()
        df = await fetcher.get_ohlcv("BTCUSDT", "4h", limit=200)
        await fetcher.close()

        if df is None or len(df) < 50:
            await msg.edit_text("⚠️ *Datos insuficientes de Binance.*\nIntenta de nuevo en unos segundos.")
            return

        df = calculate_all(df, DEFAULT_CONFIG)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        supertrend_state = "🟢 Alcista" if last['sup_is_bullish'] else "🔴 Bajista"

        if last['ash_bullish']:
            ash_state = "🟢 Bullish"
        elif last['ash_bearish']:
            ash_state = "🔴 Bearish"
        else:
            ash_state = "⚪ Neutral"

        signal_active = False
        signal_text = ""
        entry_price = last['close']
        tp_price = None
        sl_price = None
        rr_ratio = None

        supertrend_cross = (last['sup_is_bullish'] and not prev['sup_is_bullish']) or \
                          (not last['sup_is_bullish'] and prev['sup_is_bullish'])
        ash_signal = last['ash_bullish_signal'] or last['ash_bearish_signal']

        if last['sup_is_bullish'] and last['ash_bullish']:
            signal_active = True
            signal_text = "📈 *SEÑAL LARGO*"
            entry_price = last['close']
            tp_price = last['long_tp']
            sl_price = last['long_sl']
            rr_ratio = last['rr_ratio']
        elif not last['sup_is_bullish'] and last['ash_bearish']:
            signal_active = True
            signal_text = "📉 *SEÑAL CORTO*"
            entry_price = last['close']
            tp_price = last['short_tp']
            sl_price = last['short_sl']
            rr_ratio = last['rr_ratio']

        message = (
            f"📊 *BTC/USDT — Análisis 4H*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Precio:* `${last['close']:,.2f}`\n\n"
            f"*Indicadores (última vela cerrada):*\n"
            f"• *Supertrend:* {supertrend_state}\n"
            f"• *ASH:* {ash_state}\n"
        )

        if signal_active:
            message += (
                f"\n{signal_text}\n"
                f"├ Entrada: `${entry_price:,.2f}`\n"
                f"├ TP: `${tp_price:,.2f}`\n"
                f"├ SL: `${sl_price:,.2f}`\n"
                f"└ R:R: `{rr_ratio:.2f}`"
            )
        else:
            message += (
                f"\n⚪ *Sin señal activa en este momento*"
            )

        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture("BTCUSDT", "4h")
        await chart_capture.close()

        if chart_bytes:
            await msg.delete()
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await msg.edit_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        try:
            await msg.edit_text(f"⚠️ *Error en el análisis:*\n_{str(e)}_", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await msg.edit_text(f"⚠️ Error: {str(e)}")


signal_handlers_list = [
    CommandHandler("signal", signal_command),
]
