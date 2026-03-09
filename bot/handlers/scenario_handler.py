# bot/handlers/scenario_handler.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.utils.decorators import admin_only, handle_errors


@handle_errors(level="ERROR")
@admin_only
async def scenario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza y muestra escenarios de mercado."""

    msg = await update.message.reply_text("Analizando escenarios de mercado... ⏳")

    container = context.bot_data["container"]
    text = await container.get_scenario_analysis.execute()

    try:
        await msg.delete()
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        # Si no puede borrar el mensaje de espera, al menos enviamos el resultado
        await update.message.reply_text(text, parse_mode="Markdown")


scenario_handlers_list = [
    CommandHandler("scenario", scenario_command),
]
