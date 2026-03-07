"""
Handler para comandos de gestión de capital y drawdown.

Maneja:
- /capital → Mostrar estado actual del capital y drawdown
- /resume → Reanudar trading después de pausa por drawdown
- /resetdd → Resetear el drawdown a cero
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from core.database import fetch, fetchrow
from trading.drawdown_manager import get_drawdown, is_trading_paused, reset_drawdown, resume_trading
from utils.logger import logger


async def capital_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado actual del capital y drawdown."""
    user_id = update.effective_chat.id

    try:
        # Obtener configuración del usuario
        user_config = await fetchrow(
            "SELECT capital_total, max_drawdown_percent FROM user_config WHERE user_id = $1",
            user_id,
        )

        if not user_config:
            await update.message.reply_text(
                "⚠️ No tienes configuración de capital.\nUsa /setup para configurar tu cuenta."
            )
            return

        capital = float(user_config["capital_total"])
        max_dd_pct = float(user_config["max_drawdown_percent"])

        # Obtener estado del drawdown
        dd = await get_drawdown(user_id)

        if dd:
            dd_usdt = float(dd.get("current_drawdown_usdt", 0))
            dd_pct = float(dd.get("current_drawdown_percent", 0))
            losses_count = dd.get("losses_count", 0)
            is_paused = dd.get("is_paused", False)
        else:
            dd_usdt = 0
            dd_pct = 0
            losses_count = 0
            is_paused = False

        # Calcular PnL del mes actual
        pnl_mes = await _get_pnl_mes(user_id)

        # Contar operaciones activas
        active_trades = await fetch(
            "SELECT COUNT(*) as count FROM active_trades WHERE status = 'ABIERTO'"
        )
        ops_activas = active_trades[0]["count"] if active_trades else 0

        # Construir mensaje
        estado_sistema = "⛔ PAUSADO" if is_paused else "✅ ACTIVO"

        # Emoji según estado del drawdown
        if dd_pct <= 0:
            dd_emoji = "📈"
        elif dd_pct < max_dd_pct * 0.5:
            dd_emoji = "⚠️"
        else:
            dd_emoji = "🚨"

        mensaje = (
            f"💰 *ESTADO DE CAPITAL*\n"
            f"─────────────────────\n\n"
            f"*Capital Total:* ${capital:,.2f}\n"
            f"*Drawdown Actual:* {dd_emoji} ${abs(dd_usdt):,.2f} ({dd_pct:.2f}%)\n"
            f"*Límite Máximo:* {max_dd_pct}%\n"
            f"*Rachas de pérdida:* {losses_count}\n"
            f"*PnL del mes:* {'+' if pnl_mes >= 0 else ''}{pnl_mes:,.2f} USDT\n"
            f"*Operaciones activas:* {ops_activas}\n"
            f"*Estado del sistema:* {estado_sistema}\n\n"
            f"─────────────────────\n"
            f"Usa /resume para reanudar o /resetdd para resetear el drawdown."
        )

        await update.message.reply_text(mensaje, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error en /capital: {e}")
        await update.message.reply_text("⚠️ Error al obtener los datos. Intenta de nuevo.")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reanuda el trading si está pausado."""
    user_id = update.effective_chat.id

    try:
        # Verificar si está pausado
        paused = await is_trading_paused(user_id)

        if not paused:
            await update.message.reply_text(
                "ℹ️ El sistema ya está activo.\nNo hay nada que reanudar."
            )
            return

        # Reanudar trading
        await resume_trading(user_id)

        await update.message.reply_text(
            "✅ *TRADING REANUDADO*\n\n"
            "El sistema ha sido reactivado.\n"
            "Recibirás señales normalmente.",
            parse_mode="Markdown",
        )

        logger.info(f"▶️ Usuario {user_id} reanudó el trading")

    except Exception as e:
        logger.error(f"Error en /resume: {e}")
        await update.message.reply_text("⚠️ Error al reanudar. Intenta de nuevo.")


async def resetdd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de reset de drawdown."""
    user_id = update.effective_chat.id

    try:
        # Verificar que hay algo que resetear
        dd = await get_drawdown(user_id)

        if not dd or float(dd.get("current_drawdown_usdt", 0)) == 0:
            await update.message.reply_text(
                "ℹ️ Tu drawdown ya está en cero.\nNo hay nada que resetear."
            )
            return

        dd_usdt = float(dd.get("current_drawdown_usdt", 0))

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ CONFIRMAR", callback_data="resetdd_confirm"),
                    InlineKeyboardButton("❌ CANCELAR", callback_data="resetdd_cancel"),
                ]
            ]
        )

        await update.message.reply_text(
            f"⚠️ *RESETEAR DRAWDOWN*\n\n"
            f"Estás a punto de resetear tu drawdown a cero.\n\n"
            f"Drawdown actual: ${abs(dd_usdt):,.2f}\n\n"
            f"Esta acción no se puede deshacer.\n"
            f"¿Confirmas?",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error en /resetdd: {e}")
        await update.message.reply_text("⚠️ Error al procesar. Intenta de nuevo.")


async def resetdd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de confirmación de reset."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "resetdd_confirm":
        try:
            await reset_drawdown(user_id)

            await query.edit_message_text(
                "✅ *DRAWDOWN RESETEADO*\n\n"
                "Tu drawdown ha sido puesto a cero.\n"
                "El sistema está listo para operar.",
                parse_mode="Markdown",
            )

            logger.info(f"🔄 Usuario {user_id} reseteó el drawdown")

        except Exception as e:
            logger.error(f"Error en resetdd_confirm: {e}")
            await query.edit_message_text("⚠️ Error al resetear. Intenta de nuevo.")

    elif data == "resetdd_cancel":
        await query.edit_message_text(
            "❌ *CANCELADO*\n\nEl reset de drawdown ha sido cancelado.\nTu drawdown se mantiene.",
            parse_mode="Markdown",
        )


async def _get_pnl_mes(user_id: int) -> float:
    """Calcula el PnL del mes actual para un usuario específico."""
    try:
        # Obtener señales cerradas este mes para el usuario
        # Unimos con active_trades para obtener el user_id
        result = await fetchrow(
            """
            SELECT COALESCE(SUM(s.pnl_usdt), 0) as pnl_total
            FROM signals s
            JOIN active_trades at ON at.signal_id = s.id
            WHERE s.status = 'CERRADA'
            AND s.pnl_usdt IS NOT NULL
            AND at.user_id = $1
            AND EXTRACT(MONTH FROM s.close_at) = EXTRACT(MONTH FROM NOW())
            AND EXTRACT(YEAR FROM s.close_at) = EXTRACT(YEAR FROM NOW())
            """,
            user_id,
        )

        if result:
            return float(result["pnl_total"])

        return 0.0

    except Exception as e:
        logger.error(f"Error calculando PnL del mes: {e}")
        return 0.0


# Handlers para registrar en el bot
capital_handler = CommandHandler("capital", capital_command)
resume_handler = CommandHandler("resume", resume_command)
resetdd_handler = CommandHandler("resetdd", resetdd_command)
resetdd_callback_handler = CallbackQueryHandler(
    resetdd_callback, pattern=r"^resetdd_(confirm|cancel)$"
)
