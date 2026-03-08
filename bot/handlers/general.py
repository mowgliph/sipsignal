# handlers/general.py

from datetime import UTC, datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.core.api_client import obtener_precios_control
from bot.db.users import register_or_update_user
from bot.utils import permitted_only
from bot.utils.ads_manager import get_random_ad_text

# Mensajes estáticos (sin internacionalización)
HELP_MSG = {
    "es": """📚 *Ayuda de SipSignal*

*Comandos Básicos:*
/start - Iniciar el bot
/help - Mostrar esta ayuda
/status - Ver estado del bot
/myid - Obtener tu ID
/ver - Ver precios de tus monedas
/mk - Datos de mercado
/p <símbolo> - Precio de cripto
/ta <símbolo> - Análisis técnico
/signal - Análisis técnico instantáneo de BTC
/chart [tf] - Ver gráfico (5m, 15m, 1h, 4h, 1D)
/journal - Historial de señales emitidas
/capital - Gestión de capital y drawdown
/lang - Cambiar idioma

*Para más información:* Contacta a un administrador.
"""
}


#  Telegram comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start. Registra al usuario."""

    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or "es"

    await register_or_update_user(user_id, user_lang)

    nombre_usuario = update.effective_user.first_name

    mensaje = (
        "*⚡ SIPSIGNAL - Sistema de Señales BTC*\n"
        "─────────────\n\n"
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


@permitted_only
async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Get container and repository
    container = context.bot_data["container"]
    watchlist_repo = container.user_watchlist_repo

    # Get user's watchlist coins from PostgreSQL
    monedas = await watchlist_repo.get_coins(chat_id)

    if not monedas:
        await update.message.reply_text(
            "⚠️ No tienes monedas configuradas. Usa /monedas para añadir algunas.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # 2. Notificar que estamos cargando (ya que la API puede tardar un segundo)
    mensaje_espera = await update.message.reply_text("⏳ Consultando precios actuales...")

    # 3. Obtener precios en tiempo real
    precios_actuales = obtener_precios_control(monedas)

    if not precios_actuales:
        await mensaje_espera.edit_text(
            "❌ No se pudieron obtener los precios en este momento. Intenta luego."
        )
        return

    # 4. Construir el mensaje con precios actuales
    mensaje = "📊 *Precios Actuales (Tu Lista):*\n─────────────\n\n"

    for moneda in monedas:
        p_actual = precios_actuales.get(moneda)

        if p_actual is not None:
            mensaje += f"*{moneda}/USD*: ${p_actual:,.4f}\n"
        else:
            mensaje += f"*{moneda}/USD*: N/A\n"

    # Añadir fecha con UTC
    fecha_actual = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    mensaje += f"\n─────────────\n_📅 Consulta: {fecha_actual}_"

    mensaje += get_random_ad_text()

    # 6. Editar el mensaje de espera con el resultado final
    await mensaje_espera.edit_text(mensaje, parse_mode=ParseMode.MARKDOWN)


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
