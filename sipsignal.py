#!/usr/bin/env python3
# sipsignal.py - Punto de Entrada Principal del Bot de Telegram para SipSignal.
#
# SipSignal Trading Bot - Sistema Inteligente de Señales BTC
# VPS + Telegram · Análisis Técnico Automatizado
# v1.0-dev · Marzo 2026

import asyncio
import warnings
from telegram.warnings import PTBUserWarning
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from utils.logger import logger
from utils.file_manager import cargar_usuarios, guardar_usuarios, add_log_line
from core.btc_loop import btc_monitor_loop, set_btc_sender
from handlers.btc_handlers import btc_handlers_list
from core.config import settings, VERSION, PID
from core.loops import (
    alerta_loop, 
    check_custom_price_alerts,
    programar_alerta_usuario,   
    get_logs_data, 
    set_enviar_mensaje_telegram_async,
)
from handlers.general import start, myid, ver, help_command
from handlers.admin import users, logs_command, set_admin_util, set_logs_util, ms_conversation_handler, ad_command
# from handlers.year_handlers import year_command, year_sub_callback  # Eliminado - no se implementará
# from core.year_loop import year_progress_loop  # Eliminado - no se implementará

from handlers.user_settings import (
    mismonedas, parar, cmd_temp, set_monedas_command,
    set_reprogramar_alerta_util, toggle_hbd_alerts_callback, hbd_alerts_command, lang_command, set_language_callback
)
from handlers.alerts import (
    alerta_command,
    misalertas, 
    borrar_alerta_callback, 
    borrar_todas_alertas_callback,
)
from handlers.trading import graf_command, p_command, refresh_command_callback, mk_command, ta_quick_callback
from handlers.ta import ta_command, ta_switch_callback, ai_analysis_callback
from handlers.signal_handler import signal_handlers_list
from handlers.chart_handler import chart_handlers_list

from handlers.valerts_handlers import valerts_handlers_list
from handlers.setup_handler import setup_conversation_handler
from core.valerts_loop import valerts_monitor_loop, set_valerts_sender 
from core.btc_advanced_analysis import BTCAdvancedAnalyzer
from scheduler import SignalScheduler
from trading.price_monitor import start_price_monitor, get_price_monitor
from core.database import execute, fetchrow


async def price_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones de PriceMonitor (TP/SL)."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        if data.startswith("pm_tp1_done:"):
            trade_id = int(data.split(":")[1])
            # Mover SL a breakeven y cerrar 50%
            trade = await fetchrow(
                "SELECT * FROM active_trades WHERE id = $1",
                trade_id
            )
            if trade:
                entry_price = float(trade['entry_price'])
                # Actualizar SL a breakeven
                await execute(
                    "UPDATE active_trades SET sl_level = $1, updated_at = NOW() WHERE id = $2",
                    entry_price, trade_id
                )
                await query.edit_message_text(
                    f"✅ *Confirmado*\n\n"
                    f"SL movido a ${entry_price:,.2f} (breakeven)\n"
                    f"50% de posición cerrado teóricamente.",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"TP1 confirmado para trade {trade_id} - SL movido a breakeven")
                
        elif data.startswith("pm_tp1_wait:"):
            trade_id = int(data.split(":")[1])
            # Re-habilitar notificación TP1 para que pueda volver a notificar
            monitor = get_price_monitor()
            if trade_id in monitor._notified_trades:
                monitor._notified_trades[trade_id].discard('TP1')
            await query.edit_message_text(
                "⏳ *Esperando*\n\n"
                "Seguiremos monitoreando. Te notificaremos si el precio vuelve a TP1.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"TP1 diferido para trade {trade_id} - notificación re-habilitada")
            
        elif data.startswith("pm_sl_closed:"):
            trade_id = int(data.split(":")[1])
            # Marcar trade como cerrado
            await execute(
                "UPDATE active_trades SET status = 'CERRADO', updated_at = NOW() WHERE id = $1",
                trade_id
            )
            # También actualizar la señal relacionada
            trade = await fetchrow(
                "SELECT signal_id FROM active_trades WHERE id = $1",
                trade_id
            )
            if trade and trade['signal_id']:
                await execute(
                    "UPDATE signals SET status = 'CERRADA', updated_at = NOW() WHERE id = $1",
                    trade['signal_id']
                )
            await query.edit_message_text(
                "✅ *Trade cerrado*\n\n"
                "La posición ha sido cerrada. Usa /ver para ver el resumen.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Trade {trade_id} marcado como cerrado")
            
        elif data.startswith("pm_sl_summary:"):
            trade_id = int(data.split(":")[1])
            trade = await fetchrow(
                "SELECT * FROM active_trades WHERE id = $1",
                trade_id
            )
            if trade:
                entry_price = float(trade['entry_price'])
                sl_level = float(trade['sl_level'])
                direction = trade['direction']
                
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
from datetime import datetime, timezone
import platform

# --- Metadata ---
START_TIME = datetime.now(timezone.utc)


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

    # 1. Iniciar los bucles de fondo globales
    asyncio.create_task(alerta_loop(app.bot))
    asyncio.create_task(check_custom_price_alerts(app.bot))
    logger.info("✅ Bucles de fondo (HBD y Alertas de Cruce) iniciados.")

    # 2. Programar las alertas periódicas para cada usuario registrado
    usuarios = cargar_usuarios()
    if usuarios:
        add_log_line(f"👥 Encontrados {len(usuarios)} usuarios. Programando sus alertas periódicas...")
        for user_id, data in usuarios.items():
            intervalo_h = data.get('intervalo_alerta_h', 2.5)
            programar_alerta_usuario(int(user_id), intervalo_h)
    else:
        logger.info("👥 No hay usuarios registrados. Esperando a que se unan.")
    
    logger.info("✅ Todas las tareas de fondo han sido iniciadas.")

    try:
        startup_message_template = (
            "⚡ *SipSignal Trading Bot* ⚡\n"
            "─────────────\n\n"
            "🤖 `Sistema de Señales BTC v{version}`\n"
            "🪪 `PID: {pid}`\n"
            "🐍 `Python: v{python_version}`\n\n"
            "📊 Análisis técnico automatizado 24/7\n"
            "🔔 Alertas inteligentes en tiempo real\n\n"
            "─────────────\n"
            "✅ *Sistema activo y operativo*"
        )
        startup_message = startup_message_template.format(
            version=VERSION,
            pid=PID,
            python_version=platform.python_version()
        )

        for admin_id in settings.admin_chat_ids:
            await app.bot.send_message(chat_id=admin_id, text=startup_message, parse_mode=ParseMode.MARKDOWN)

        logger.info("📬 Notificación de inicio enviada a los administradores.")
    except Exception as e:
        logger.error(f"⚠️ Fallo al enviar notificación de inicio a los admins: {e}")
        
    # Inicio de Loops de Monitoreo (BTC y VALERTS)
    asyncio.create_task(btc_monitor_loop(app.bot))
    asyncio.create_task(valerts_monitor_loop(app.bot))

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


def main():
    """Inicia el bot y configura todos los handlers."""
    
    builder = ApplicationBuilder().token(settings.token_telegram)
    app = builder.build()
    
    # 1. FUNCIÓN DE ENVÍO DE MENSAJES
    async def enviar_mensajes(mensaje, chat_ids, parse_mode=ParseMode.MARKDOWN, reply_markup=None, photo=None):
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
                        reply_markup=reply_markup
                    )
                elif mensaje:
                    await app.bot.send_message(
                        chat_id=int(chat_id),
                        text=mensaje,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup
                    )
                await asyncio.sleep(0.05) # Pequeña pausa para evitar flood limits

            except BadRequest as e:
                # SI FALLA EL FORMATO (Markdown roto), REINTENTAMOS EN TEXTO PLANO
                error_str = str(e)
                if "parse entities" in error_str or "can't find end" in error_str:
                    try:
                        logger.warning(f"⚠️ Formato Markdown fallido para {chat_id}. Reenviando como texto plano.")
                        if photo:
                            await app.bot.send_photo(
                                chat_id=int(chat_id),
                                photo=photo,
                                caption=mensaje, # Sin parse_mode
                                reply_markup=reply_markup
                            )
                        else:
                            await app.bot.send_message(
                                chat_id=int(chat_id),
                                text=mensaje, 
                                parse_mode=None, # <--- Sin formato
                                reply_markup=reply_markup
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
                        logger.info(f"🗑️ Usuario {chat_id} ha bloqueado el bot. Eliminado de la lista.")

        if usuarios_actualizados is not None:
            guardar_usuarios(usuarios_actualizados)

        return fallidos

    # 2. INYECCIÓN DE DEPENDENCIAS
    set_admin_util(enviar_mensajes)
    set_logs_util(get_logs_data)
    set_reprogramar_alerta_util(programar_alerta_usuario)
    set_enviar_mensaje_telegram_async(enviar_mensajes, app)
    set_btc_sender(enviar_mensajes)
    set_valerts_sender(enviar_mensajes)
    
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
    app.add_handler(CommandHandler("graf", graf_command))
    app.add_handler(CommandHandler("p", p_command))
    app.add_handler(CommandHandler("ta", ta_command))
    
    # ============================================
    # Comandos de Usuario
    # ============================================
    app.add_handler(CommandHandler("mismonedas", mismonedas))
    app.add_handler(CommandHandler("monedas", set_monedas_command))
    app.add_handler(CommandHandler("parar", parar))
    app.add_handler(CommandHandler("temp", cmd_temp))
    app.add_handler(CommandHandler("hbdalerts", hbd_alerts_command))
    app.add_handler(CommandHandler("lang", lang_command))
    
    # ============================================
    # Comandos de Alertas
    # ============================================
    app.add_handler(CommandHandler("alerta", alerta_command))
    app.add_handler(CommandHandler("misalertas", misalertas))
    
    # ============================================
    # Handlers de BTC y VALERTS (listas)
    # ============================================
    for handler in btc_handlers_list:
        app.add_handler(handler)
    
    app.add_handlers(valerts_handlers_list)
    
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
    
    # Callbacks de Alertas
    app.add_handler(CallbackQueryHandler(borrar_alerta_callback, pattern='^delete_alert_'))
    app.add_handler(CallbackQueryHandler(borrar_todas_alertas_callback, pattern="^delete_all_alerts$"))
    
    # Callbacks de Configuración
    app.add_handler(CallbackQueryHandler(toggle_hbd_alerts_callback, pattern="^toggle_hbd_alerts$"))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))
    
    # Callbacks de PriceMonitor (TP/SL)
    app.add_handler(CallbackQueryHandler(price_monitor_callback, pattern=r"^pm_"))
    
    # 4. Asignar la función post_init
    app.post_init = post_init
    
    # 5. Iniciar el polling
    print("✅ SipSignal iniciado. Esperando mensajes...")
    add_log_line("----------- ⚡ SipSignal INICIADO -----------")
    app.run_polling()

if __name__ == "__main__":
    main()
