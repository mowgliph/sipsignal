# handlers/general.py

from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core.api_client import obtener_precios_control
from db.users import register_or_update_user
from utils.ads_manager import get_random_ad_text
from utils.file_manager import (
    check_feature_access,
    load_last_prices_status,
    obtener_datos_usuario,
    obtener_monedas_usuario,
    registrar_uso_comando,
)

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


# COMANDO /ver REFACTORIZADO
async def ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # === GUARDIA DE PAGO ===
    # 1. Verificar acceso
    acceso, mensaje = check_feature_access(chat_id, "ver_limit")
    if not acceso:
        # Si no tiene acceso, enviamos el mensaje de error (que contiene la info de venta) y paramos.
        await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)
        return

    # 2. Registrar el uso (se descuenta 1 del contador)
    registrar_uso_comando(chat_id, "ver")
    # =======================
    # === LÓGICA DEL COMANDO /ver ====
    # 1. Obtener las monedas configuradas por el usuario
    monedas = obtener_monedas_usuario(chat_id)

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

    # 4. Cargar precios anteriores (SOLO LECTURA) para mostrar tendencias
    # No guardamos nada aquí para no romper la lógica de "cambio desde la última alerta".
    todos_precios_anteriores = load_last_prices_status()
    precios_anteriores_usuario = todos_precios_anteriores.get(str(chat_id), {})

    # 5. Construir el mensaje
    mensaje = "📊 *Precios Actuales (Tu Lista):*\n─────────────\n\n"

    tolerancia = 0.0000001

    for moneda in monedas:
        p_actual = precios_actuales.get(moneda)
        p_anterior = precios_anteriores_usuario.get(moneda)

        if p_actual is not None:
            # Calcular indicador visual
            indicador = ""
            if p_anterior:
                if p_actual > p_anterior + tolerancia:
                    indicador = " 🔺"
                elif p_actual < p_anterior - tolerancia:
                    indicador = " 🔻"
                else:
                    indicador = " ▫️"

            mensaje += f"*{moneda}/USD*: ${p_actual:,.4f}{indicador}\n"
        else:
            mensaje += f"*{moneda}/USD*: N/A\n"

    # Añadir fecha
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    # 1. Obtener los datos del usuario del JSON
    datos_usuario = obtener_datos_usuario(user_id)

    # 2. Obtener el idioma (por defecto español)
    # Nota: Asegúrate de usar 'language', que es como se guarda en file_manager.py
    lang = datos_usuario.get("language", "es")

    # 3. Validación extra por seguridad
    if lang not in ["es", "en"]:
        lang = "es"

    # 4. Obtener el texto directamente del diccionario HELP_MSG
    # Si por alguna razón falla el idioma, usa español como respaldo
    texto = HELP_MSG.get(lang, HELP_MSG["es"])

    # 5. Enviar mensaje
    await update.message.reply_text(
        text=texto, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
    )
