#!/usr/bin/env python3
# sipsignal.py - Punto de Entrada Principal del Bot de Telegram para SipSignal.
#
# SipSignal Trading Bot - Sistema Inteligente de Señales BTC
# VPS + Telegram · Análisis Técnico Automatizado
# v1.0-dev · Marzo 2026

import asyncio
import warnings

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from telegram.warnings import PTBUserWarning

from core.config import PID, VERSION, settings
from core.database import execute, fetchrow
from core.loops import get_logs_data
from handlers.admin import (
    ad_command,
    logs_command,
    ms_conversation_handler,
    set_admin_util,
    set_logs_util,
    users,
)
from handlers.capital_handler import (
    capital_handler,
    resetdd_callback_handler,
    resetdd_handler,
    resume_handler,
)
from handlers.chart_handler import chart_handlers_list
from handlers.general import help_command, myid, start, ver
from handlers.setup_handler import setup_conversation_handler
from handlers.signal_handler import signal_handlers_list
from handlers.signal_response_handler import process_signal_timeout, signal_response_handler
from handlers.ta import ai_analysis_callback, ta_command, ta_switch_callback
from handlers.trading import mk_command, p_command, refresh_command_callback, ta_quick_callback
from handlers.user_settings import lang_command, set_language_callback
from scheduler import SignalScheduler
from trading.drawdown_manager import update_drawdown
from trading.price_monitor import get_price_monitor, start_price_monitor
from utils.file_manager import add_log_line, cargar_usuarios, guardar_usuarios
from utils.logger import logger


async def price_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones de PriceMonitor (TP/SL)."""
    query = update.callback_query
    await query.answer()

    data = query.data

    try:
        if data.startswith("pm_tp1_done:"):
            trade_id = int(data.split(":")[1])
            # Mover SL a breakeven y cerrar 50%
            trade = await fetchrow("SELECT * FROM active_trades WHERE id = $1", trade_id)
            if trade:
                entry_price = float(trade["entry_price"])
                # Actualizar SL a breakeven
                await execute(
                    "UPDATE active_trades SET sl_level = $1, updated_at = NOW() WHERE id = $2",
                    entry_price,
                    trade_id,
                )
                await query.edit_message_text(
                    f"✅ *Confirmado*\n\n"
                    f"SL movido a ${entry_price:,.2f} (breakeven)\n"
                    f"50% de posición cerrado teóricamente.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                logger.info(f"TP1 confirmado para trade {trade_id} - SL movido a breakeven")

        elif data.startswith("pm_tp1_wait:"):
            trade_id = int(data.split(":")[1])
            # Re-habilitar notificación TP1 para que pueda volver a notificar
            monitor = get_price_monitor()
            if trade_id in monitor._notified_trades:
                monitor._notified_trades[trade_id].discard("TP1")
            await query.edit_message_text(
                "⏳ *Esperando*\n\n"
                "Seguiremos monitoreando. Te notificaremos si el precio vuelve a TP1.",
                parse_mode=ParseMode.MARKDOWN,
            )
            logger.info(f"TP1 diferido para trade {trade_id} - notificación re-habilitada")

        elif data.startswith("pm_sl_closed:"):
            trade_id = int(data.split(":")[1])

            # Obtener datos del trade para calcular pérdida
            trade = await fetchrow("SELECT * FROM active_trades WHERE id = $1", trade_id)

            if trade:
                entry_price = float(trade["entry_price"])
                sl_level = float(trade["sl_level"])
                direction = trade["direction"]

                # Calcular pérdida
                if direction == "LONG":
                    loss = entry_price - sl_level
                else:
                    loss = sl_level - entry_price

                # Actualizar drawdown con la pérdida
                user_id = update.effective_chat.id
                await update_drawdown(user_id, -loss, context.bot)

            # Marcar trade como cerrado
            await execute(
                "UPDATE active_trades SET status = 'CERRADO', updated_at = NOW() WHERE id = $1",
                trade_id,
            )

            # También actualizar la señal relacionada
            if trade and trade["signal_id"]:
                await execute(
                    "UPDATE signals SET status = 'CERRADA', updated_at = NOW() WHERE id = $1",
                    trade["signal_id"],
                )

            await query.edit_message_text(
                "✅ *Trade cerrado*\n\nLa posición ha sido cerrada. Usa /ver para ver el resumen.",
                parse_mode=ParseMode.MARKDOWN,
            )
            logger.info(f"Trade {trade_id} marcado como cerrado - drawdown actualizado")

        elif data.startswith("pm_sl_summary:"):
            trade_id = int(data.split(":")[1])
            trade = await fetchrow("SELECT * FROM active_trades WHERE id = $1", trade_id)
            if trade:
                entry_price = float(trade["entry_price"])
                sl_level = float(trade["sl_level"])
                direction = trade["direction"]

                if direction == "LONG":
                    loss = entry_price - sl_level
                else:
                    loss = sl_level - entry_price
                loss_pct = (loss / entry_price) * 100

                summary = (
                    f"📊 *Resumen del Trade* #{trade_id}\n\n"
                    f"📍 *Dirección:* {direction}\n"
                    f"💵 *Entrada:* ${entry_price:,.2f}\n"
                    f"🛑 *SL:* ${sl_level:,.2f}\n"
                    f"📉 *Pérdida:* -{loss:.2f} USDT ({loss_pct:.1f}%)\n\n"
                    f"Usa /ver para ver el historial completo."
                )
                await query.edit_message_text(summary, parse_mode=ParseMode.MARKDOWN)
                logger.info(f"Resumen enviado para trade {trade_id}")

    except Exception as e:
        logger.error(f"Error en price_monitor_callback: {e}")
        try:
            await query.edit_message_text("⚠️ Error al procesar la acción. Intenta de nuevo.")
        except Exception:
            pass


# Ignorar advertencias específicas de PTB sobre CallbackQueryHandler en ConversationHandler
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*CallbackQueryHandler.*")

# --- Importaciones adicionales para validación ---
import platform
from datetime import UTC, datetime

# --- Metadata ---
START_TIME = datetime.now(UTC)


async def check_admin(update: Update) -> bool:
    """Verifica si el chat_id está en la lista de administradores."""
    chat_id = update.effective_chat.id
    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text(
            "⛔ Acceso denegado. No tienes permisos para usar este bot."
        )
        return False
    return True


async def post_init(app: Application):
    """
    Se ejecuta después de que el bot se inicializa.
    Inicia los bucles de fondo y programa las alertas para todos los usuarios existentes.
    """

    logger.info("🤖 Bot inicializado: Iniciando tareas de fondo...")

    # 1. Signal scheduler started below
    try:
        startup_message_template = (
            "⚡ *SipSignal Trading Bot* ⚡\n"
            "─────────────\n\n"
            "🤖 `Sistema de Señales BTC v{version}`\n"
            "🪪 `PID: {pid}`\n"
            "🐍 `Python: v{python_version}`\n\n"
            "📊 Análisis técnico automatizado 24/7\n"
            "🎯 Señales de trading con TP/SL\n\n"
            "─────────────\n"
            "✅ *Sistema activo y operativo*"
        )
        startup_message = startup_message_template.format(
            version=VERSION, pid=PID, python_version=platform.python_version()
        )

        for admin_id in settings.admin_chat_ids:
            await app.bot.send_message(
                chat_id=admin_id, text=startup_message, parse_mode=ParseMode.MARKDOWN
            )

        logger.info("📬 Notificación de inicio enviada a los administradores.")
    except Exception as e:
        logger.error(f"⚠️ Fallo al enviar notificación de inicio a los admins: {e}")

    # Iniciar SignalScheduler
    try:
        scheduler = SignalScheduler()
        asyncio.create_task(scheduler.start(app.bot))
        logger.info("✅ SignalScheduler iniciado")
    except Exception as e:
        logger.error(f"❌ Error al iniciar SignalScheduler: {e}")

    # Iniciar PriceMonitor (WebSocket TP/SL)
    try:
        await start_price_monitor(app.bot)
        logger.info("✅ PriceMonitor iniciado")
    except Exception as e:
        logger.error(f"❌ Error al iniciar PriceMonitor: {e}")

    # Iniciar proceso de timeout de señales (60 min)
    try:
        asyncio.create_task(process_signal_timeout())
        logger.info("✅ Signal timeout process iniciado")
    except Exception as e:
        logger.error(f"❌ Error al iniciar signal timeout: {e}")


def main():
    """Inicia el bot y configura todos los handlers."""

    builder = ApplicationBuilder().token(settings.token_telegram)
    app = builder.build()

    # 1. FUNCIÓN DE ENVÍO DE MENSAJES
    async def enviar_mensajes(
        mensaje, chat_ids, parse_mode=ParseMode.MARKDOWN, reply_markup=None, photo=None
    ):
        """
        Envía mensaje a lista de chat_ids. Si falla el Markdown, reintenta en texto plano.
        """
        fallidos = {}
        usuarios_actualizados = None

        for chat_id in chat_ids:
            try:
                # Intentamos enviar con el formato original (Markdown)
                if photo:
                    caption = mensaje.strip() if mensaje and mensaje.strip() else None
                    await app.bot.send_photo(
                        chat_id=int(chat_id),
                        photo=photo,
                        caption=caption,
                        parse_mode=parse_mode if caption else None,
                        reply_markup=reply_markup,
                    )
                elif mensaje:
                    await app.bot.send_message(
                        chat_id=int(chat_id),
                        text=mensaje,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                    )
                await asyncio.sleep(0.05)  # Pequeña pausa para evitar flood limits

            except BadRequest as e:
                # SI FALLA EL FORMATO (Markdown roto), REINTENTAMOS EN TEXTO PLANO
                error_str = str(e)
                if "parse entities" in error_str or "can't find end" in error_str:
                    try:
                        logger.warning(
                            f"⚠️ Formato Markdown fallido para {chat_id}. Reenviando como texto plano."
                        )
                        if photo:
                            await app.bot.send_photo(
                                chat_id=int(chat_id),
                                photo=photo,
                                caption=mensaje,  # Sin parse_mode
                                reply_markup=reply_markup,
                            )
                        else:
                            await app.bot.send_message(
                                chat_id=int(chat_id),
                                text=mensaje,
                                parse_mode=None,  # <--- Sin formato
                                reply_markup=reply_markup,
                            )
                    except Exception as e2:
                        # Si falla incluso en texto plano, entonces sí es un error real
                        fallidos[chat_id] = str(e2)
                        logger.error(f"❌ Fallo definitivo al enviar a {chat_id}: {e2}")
                else:
                    # Otros errores BadRequest (ej: chat not found)
                    fallidos[chat_id] = error_str
                    logger.error(f"❌ Error BadRequest en {chat_id}: {error_str}")

            except Exception as e:
                # Errores generales (Bloqueos, red, etc)
                error_str = str(e)
                fallidos[chat_id] = error_str
                logger.error(f"❌ Fallo al enviar a {chat_id}: {error_str}")

                if "Chat not found" in error_str or "bot was blocked" in error_str:
                    if usuarios_actualizados is None:
                        usuarios_actualizados = cargar_usuarios()
                    if chat_id in usuarios_actualizados:
                        del usuarios_actualizados[chat_id]
                        logger.info(
                            f"🗑️ Usuario {chat_id} ha bloqueado el bot. Eliminado de la lista."
                        )

        if usuarios_actualizados is not None:
            guardar_usuarios(usuarios_actualizados)

        return fallidos

    # 2. INYECCIÓN DE DEPENDENCIAS
    set_admin_util(enviar_mensajes)
    set_logs_util(get_logs_data)

    # 3. REGISTRO DE HANDLERS

    # ============================================
    # IMPORTANTE: Handlers de conversación PRIMERO
    # ============================================

    # 1️⃣ ConversationHandlers (PRIMERO)
    app.add_handler(ms_conversation_handler)
    app.add_handler(setup_conversation_handler)

    # ============================================
    # Comandos generales
    # ============================================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("ver", ver))
    app.add_handler(CommandHandler("help", help_command))

    # ============================================
    # Comandos de Admin
    # ============================================
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("status", logs_command))
    app.add_handler(CommandHandler("ad", ad_command))

    # ============================================
    # Comandos de Trading/Cripto
    # ============================================
    app.add_handler(CommandHandler("mk", mk_command))
    app.add_handler(CommandHandler("p", p_command))
    app.add_handler(CommandHandler("ta", ta_command))

    # ============================================
    # Comandos de Usuario
    # ============================================
    app.add_handler(CommandHandler("lang", lang_command))

    # Handlers de Signal y Chart
    for handler in signal_handlers_list:
        app.add_handler(handler)
    for handler in chart_handlers_list:
        app.add_handler(handler)

    # ============================================
    # CallbackQueryHandlers (DEBEN IR AL FINAL)
    # ============================================

    # Callbacks de Trading
    app.add_handler(CallbackQueryHandler(ta_switch_callback, pattern="^ta_switch\\|"))
    app.add_handler(CallbackQueryHandler(ai_analysis_callback, pattern="^ai_analyze\\|"))
    app.add_handler(CallbackQueryHandler(refresh_command_callback, pattern=r"^refresh_"))
    app.add_handler(CallbackQueryHandler(ta_quick_callback, pattern=r"^ta_quick\|"))

    # Callbacks de Configuración
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))

    # Callbacks de PriceMonitor (TP/SL)
    app.add_handler(CallbackQueryHandler(price_monitor_callback, pattern=r"^pm_"))

    # Callbacks de Respuesta de Señales (taken/skipped/detail)
    app.add_handler(signal_response_handler)

    # Handlers de Capital y Drawdown
    app.add_handler(capital_handler)
    app.add_handler(resume_handler)
    app.add_handler(resetdd_handler)
    app.add_handler(resetdd_callback_handler)

    # 4. Asignar la función post_init
    app.post_init = post_init

    # 5. Iniciar el polling
    print("✅ SipSignal iniciado. Esperando mensajes...")
    add_log_line("----------- ⚡ SipSignal INICIADO -----------")
    app.run_polling()


if __name__ == "__main__":
    main()
