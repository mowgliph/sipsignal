# handlers/general.py

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.db.users import register_or_update_user

logger = logging.getLogger(__name__)

# Mensajes estáticos (sin internacionalización)
HELP_MSG = {
    "es": """📚 *Ayuda de SipSignal*

*Comandos Básicos:*
/start - Iniciar el bot
/help - Mostrar esta ayuda
/status - Ver estado del bot
/myid - Obtener tu ID
/mk - Datos de mercado
/p <símbolo> - Precio de cripto
/ta <símbolo> - Análisis técnico
/signal - Análisis técnico instantáneo de BTC
/chart [tf] - Ver gráfico (5m, 15m, 1h, 4h, 1D)
/journal - Historial de señales emitidas
/capital - Gestión de capital y drawdown
/lang - Cambiar idioma
/ref - Tu enlace de referido

*Para más información:* Contacta a un administrador.
"""
}


#  Telegram comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start. Registra al usuario."""

    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or "es"

    # Check for referral code in args (from deep link)
    referral_code = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0].strip()

    # Register user (pass referral code if exists)
    result = await register_or_update_user(user_id, user_lang, referral_code)

    nombre_usuario = update.effective_user.first_name

    # Build referral success message if applicable
    referral_msg = ""
    if referral_code and result.get("referral_applied"):
        # Get referrer info for display
        from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

        try:
            repo = PostgreSQLReferralRepository()
            referrer_id = result.get("referred_by")
            if referrer_id:
                referrer_data = await repo.get_referrer_info(referrer_id)
                if referrer_data:
                    referrer_username = referrer_data.get("username")
                    if referrer_username:
                        referral_msg = f"✅ Has sido referido por @{referrer_username}\n\n"
                    else:
                        referral_msg = "✅ ¡Código de referido aplicado con éxito!\n\n"
        except Exception as e:
            logger.warning(f"Error getting referrer info: {e}")

    mensaje = (
        "*⚡ SIPSIGNAL - Sistema de Señales BTC*\n"
        "─────────────\n\n"
        f"{referral_msg}"
        f"Hola {nombre_usuario}! 👋 Bienvenido a SipSignal, tu asistente de trading automatizado para Bitcoin.\n\n"
        "*🎯 ¿Qué hace SipSignal?*\n\n"
        "SipSignal analiza el mercado de BTC/USDT 24/7 y te envía señales de trading cuando detecta oportunidades según tu estrategia. "
        "Incluye monitoreo de TP/SL en tiempo real. No ejecuta órdenes automáticamente - te notifica para que tú decidas.\n\n"
        "*📱 Comandos disponibles:*\n\n"
        "/signal - Análisis técnico instantáneo de BTC\n"
        "/chart [tf] - Ver gráfico (5m, 15m, 1h, 4h, 1D)\n"
        "/risk [entrada] [sl] [tp] - Calcular ratio riesgo/beneficio\n"
        "/journal - Historial de señales emitidas\n"
        "/capital - Gestión de capital y drawdown\n"
        "/status - Estado del sistema y último análisis\n\n"
        "*🔍 Análisis incluye:*\n\n"
        "• RSI, MACD, Bollinger Bands, EMA\n"
        "• Soportes y resistencias\n"
        "• Contexto de mercado con IA (Groq)\n"
        "• Ratio riesgo:beneficio recomendado\n\n"
        "Usa /help para más detalles o /status para ver el estado actual del sistema."
    )

    await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)


# ============================================================


# COMANDO /myid para ver datos del usuario
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /myid. Muestra el ID de chat del usuario."""
    user_id = update.effective_user.id
    user = update.effective_user

    nombre_completo = user.first_name or "N/A"
    username_str = f"@{user.username}" if user.username else "N/A"

    mensaje_template = (
        "Estos son tus datos de Telegram:\n─────────────\n\n"
        "Nombre: {nombre}\n"
        "Usuario: {usuario}\n"
        "ID: `{id_chat}`"
    )

    mensaje = mensaje_template.format(nombre=nombre_completo, usuario=username_str, id_chat=user_id)

    await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)


# COMANDO /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de ayuda unificado."""
    user = update.effective_user
    user_id = user.id

    # Get container from context
    container = context.bot_data["container"]
    user_repo = container.user_repo

    # Obtain user data from repository
    datos_usuario = await user_repo.get(user_id)

    # Obtain language (default Spanish)
    # Repository uses 'language' field
    lang = datos_usuario.get("language", "es") if datos_usuario else "es"

    # Extra validation for safety
    if lang not in ["es", "en"]:
        lang = "es"

    # Get text directly from HELP_MSG dictionary
    # If language fails for some reason, use Spanish as fallback
    texto = HELP_MSG.get(lang, HELP_MSG["es"])

    # Send message
    await update.message.reply_text(
        text=texto, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
    )
