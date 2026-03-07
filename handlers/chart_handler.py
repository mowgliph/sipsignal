# handlers/chart_handler.py

import asyncio
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from core.config import settings
from trading.chart_capture import ChartCapture

VALID_TIMEFRAMES = ["1d", "4h", "1h", "15m"]
DEFAULT_TIMEFRAME = "4h"


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura y envía el gráfico del timeframe indicado."""
    chat_id = update.effective_chat.id

    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    args = context.args
    timeframe = DEFAULT_TIMEFRAME

    if args:
        tf_input = args[0].lower()
        if tf_input in VALID_TIMEFRAMES:
            timeframe = tf_input
        else:
            await update.message.reply_text(
                f"⚠️ *Timeframe inválido.*\n"
                f"Usar: `{', '.join(VALID_TIMEFRAMES)}`\n"
                f"Default: `{DEFAULT_TIMEFRAME}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    msg = await update.message.reply_text(
        f"⏳ *Generando gráfico {timeframe.upper()}...*",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture("BTCUSDT", timeframe)
        await chart_capture.close()

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if chart_bytes:
            await msg.delete()
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 BTC/USDT {timeframe.upper()} — {now_utc}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await msg.edit_text(
                f"⚠️ *Error generando gráfico.*\n"
                f"Intenta de nuevo en unos segundos.",
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        try:
            await msg.edit_text(
                f"⚠️ *Error:*\n_{str(e)}_",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await msg.edit_text(f"⚠️ Error: {str(e)}")


chart_handlers_list = [
    CommandHandler("chart", chart_command),
]
