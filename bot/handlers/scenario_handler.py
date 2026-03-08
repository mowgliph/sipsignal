# bot/handlers/scenario_handler.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.utils import admin_only


@admin_only
async def scenario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza y muestra escenarios de mercado."""

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
