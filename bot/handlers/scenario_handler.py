# bot/handlers/scenario_handler.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.core.config import settings


async def scenario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza y muestra escenarios de mercado."""
    chat_id = update.effective_chat.id

    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Acceso denegado.")
        return

    msg = await update.message.reply_text("Analizando escenarios de mercado... ⏳")

    try:
        container = context.bot_data["container"]
        text = await container.get_scenario_analysis.execute()

        await msg.delete()
        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        try:
            await msg.edit_text(f"⚠️ Error en el análisis:\n{str(e)}")
        except Exception:
            await msg.edit_text("⚠️ Error en el análisis.")


scenario_handlers_list = [
    CommandHandler("scenario", scenario_command),
]
