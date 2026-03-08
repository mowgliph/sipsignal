# handlers/signal_handler.py

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from bot.core.config import settings


async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado actual de Supertrend + ASH y señal activa para BTC/USDT 4H."""
    chat_id = update.effective_chat.id

    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    msg = await update.message.reply_text(
        "⏳ *Analizando mercado...*", parse_mode=ParseMode.MARKDOWN
    )

    try:
        container = context.bot_data["container"]
        result = await container.get_signal_analysis.execute(timeframe="4h")

        signal = result["signal"]
        chart_bytes = result["chart_bytes"]

        signal_active = signal.direction in ("LONG", "SHORT")
        is_long = signal.direction == "LONG"

        signal_text = "📈 *SEÑAL LARGO*" if is_long else "📉 *SEÑAL CORTO*"

        supertrend_state = "🟢 Alcista" if is_long else "🔴 Bajista"
        ash_state = "🟢 Bullish" if is_long else "🔴 Bearish"

        message = (
            f"📊 *BTC/USDT — Análisis 4H*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Precio:* `${signal.entry_price:,.2f}`\n\n"
            f"*Indicadores (última vela cerrada):*\n"
            f"• *Supertrend:* {supertrend_state}\n"
            f"• *ASH:* {ash_state}\n"
        )

        if signal_active:
            message += (
                f"\n{signal_text}\n"
                f"├ Entrada: `${signal.entry_price:,.2f}`\n"
                f"├ TP: `${signal.tp1_level:,.2f}`\n"
                f"├ SL: `${signal.sl_level:,.2f}`\n"
                f"└ R:R: `{signal.rr_ratio:.2f}`"
            )
        else:
            message += "\n⚪ *Sin señal activa en este momento*"

        if chart_bytes:
            await msg.delete()
            await update.message.reply_photo(
                photo=chart_bytes, caption=message, parse_mode=ParseMode.MARKDOWN
            )
        else:
            await msg.edit_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        try:
            await msg.edit_text(
                f"⚠️ *Error en el análisis:*\n_{str(e)}_", parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await msg.edit_text(f"⚠️ Error: {str(e)}")


signal_handlers_list = [
    CommandHandler("signal", signal_command),
]
