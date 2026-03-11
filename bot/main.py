#!/usr/bin/env python3
# sipsignal.py - Punto de Entrada Principal del Bot de Telegram para SipSignal.
#
# SipSignal Trading Bot - Sistema Inteligente de Señales BTC
# VPS + Telegram · Análisis Técnico Automatizado
# v1.0-dev · Marzo 2026

import asyncio
import contextlib
import platform
import warnings
from datetime import UTC, datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from bot.core import database
from bot.core.access_manager import AccessManager
from bot.core.config import PID, VERSION, settings
from bot.core.database import execute, fetchrow
from bot.core.loops import get_logs_data
from bot.handlers.access_admin import (
    approve_command,
    deny_command,
    list_users_command,
    make_admin_command,
)
from bot.handlers.admin import (
    ad_command,
    logs_command,
    ms_conversation_handler,
    set_admin_util,
    set_logs_util,
    users,
)
from bot.handlers.capital_handler import (
    capital_handler,
    resetdd_callback_handler,
    resetdd_handler,
    resume_handler,
)
from bot.handlers.chart_handler import chart_handlers_list
from bot.handlers.general import help_command, myid, start, ver
from bot.handlers.scenario_handler import scenario_handlers_list
from bot.handlers.setup_handler import setup_conversation_handler
from bot.handlers.signal_handler import signal_handlers_list
from bot.handlers.signal_response_handler import process_signal_timeout, signal_response_handler
from bot.handlers.ta import ai_analysis_callback, ta_command, ta_switch_callback
from bot.handlers.trading import mk_command, p_command, refresh_command_callback, ta_quick_callback
from bot.handlers.user_settings import lang_command, set_language_callback
from bot.trading.drawdown_manager import update_drawdown
from bot.trading.price_monitor import get_price_monitor, start_price_monitor
from bot.utils.logger import bot_logger as logger


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
                loss = entry_price - sl_level if direction == "LONG" else sl_level - entry_price

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

                loss = entry_price - sl_level if direction == "LONG" else sl_level - entry_price
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
        with contextlib.suppress(Exception):
            await query.edit_message_text("⚠️ Error al procesar la acción. Intenta de nuevo.")


# Ignorar advertencias específicas de PTB sobre CallbackQueryHandler en ConversationHandler
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*CallbackQueryHandler.*")

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
    Inicializa el pool de base de datos y otras tareas de fondo.
    """

    # 0. Inicializar Pool de Base de Datos
    try:
        await database.connect()
        logger.info("✅ Pool de base de datos inicializado")
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar el pool de base de datos: {e}")
        # En producción, podrías querer abortar aquí
        raise

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

    # Ejecutar ciclo de señales via Container
    try:
        container = app.bot_data.get("container")
        if container is None:
            raise RuntimeError("Container not found in bot_data")

        admin_id = settings.admin_chat_ids[0] if settings.admin_chat_ids else None
        if admin_id is None:
            logger.warning("No admin_chat_ids configured - skipping signal cycle")
        else:
            user_config = await container.user_config_repo.get(admin_id)
            if user_config is None:
                from bot.domain.user_config import UserConfig

                user_config = UserConfig(
                    user_id=admin_id,
                    chat_id=admin_id,
                    timeframe="4h",
                )

            await container.run_signal_cycle.execute(user_config)
            logger.info("✅ Signal cycle executed via Container")

    except Exception as e:
        logger.error(f"❌ Error al ejecutar signal cycle: {e}")

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


async def post_shutdown(app: Application):
    """
    Se ejecuta al apagar el bot.
    Cierra el pool de base de datos de forma limpia.
    """
    logger.info("🛑 Bot deteniéndose: Cerrando recursos...")
    try:
        await database.close()
        logger.info("✅ Pool de base de datos cerrado")
    except Exception as e:
        logger.error(f"❌ Error al cerrar el pool de base de datos: {e}")


def main():
    """Inicia el bot y configura todos los handlers."""

    builder = ApplicationBuilder().token(settings.token_telegram)
    # Registrar hooks de ciclo de vida
    builder.post_init(post_init)
    builder.post_shutdown(post_shutdown)

    app = builder.build()

    from bot.container import Container

    container = Container(settings=settings, bot=app.bot)
    app.bot_data["container"] = container

    # Create AccessManager instance and store in bot_data
    access_manager = AccessManager(admin_chat_ids=settings.admin_chat_ids)
    app.bot_data["access_manager"] = access_manager

    # 1. FUNCIÓN DE ENVÍO DE MENSAJES
    async def enviar_mensajes(
        mensaje, chat_ids, parse_mode=ParseMode.MARKDOWN, reply_markup=None, photo=None
    ):
        """
        Envía mensaje a lista de chat_ids. Si falla el Markdown, reintenta en texto plano.
        """
        fallidos = {}

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

                # Note: User deletion on block is now handled by checking status in repository
                # Legacy JSON removal code removed - users are managed in PostgreSQL

        return fallidos

    # 2. INYECCIÓN DE DEPENDENCIAS
    set_admin_util(enviar_mensajes)
    set_logs_util(get_logs_data)

    # 3. REGISTRO DE HANDLERS

    # ============================================
    # IMPORTANTE: AccessManager PRIMERO (middleware)
    # ============================================

    # 0️⃣ AccessManager - Middleware de control de acceso (PRIMER HANDLER)
    async def access_manager_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper para AccessManager que intercepta todos los mensajes."""
        should_continue = await access_manager.handle_update(update, app)
        if not should_continue:
            # Detener el procesamiento si el usuario no tiene acceso
            return

    # Registrar AccessManager como el primer handler (antes que cualquier otro)
    app.add_handler(MessageHandler(filters.ALL, access_manager_wrapper), group=-100)

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

    # Access control admin commands (with @admin_only decorator)
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("deny", deny_command))
    app.add_handler(CommandHandler("make_admin", make_admin_command))
    app.add_handler(CommandHandler("list_users", list_users_command))

    # Other admin commands
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
    for handler in scenario_handlers_list:
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

    # 5. Iniciar el polling
    print("✅ SipSignal iniciado. Esperando mensajes...")
    logger.add_log_line("----------- ⚡ SipSignal INICIADO -----------")
    app.run_polling()


if __name__ == "__main__":
    main()
