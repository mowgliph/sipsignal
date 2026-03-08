# handlers/trading.py

from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Importamos configuraciones y utilidades existentes
from bot.core.api_client import obtener_datos_moneda
from bot.utils import permitted_only
from bot.utils.ads_manager import get_random_ad_text

# from core.i18n import _  # TODO: Implementar i18n en el futuro


# Función identidad para reemplazar i18n (textos ya están en español)
def _(message, *args, **kwargs):
    return message


@permitted_only
async def p_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el precio y otros datos de una criptomoneda.
    Uso: /p <MONEDA>
    """
    user_id = update.effective_user.id

    if not context.args:
        error_msg = _("⚠️ *Formato incorrecto*.\nUso: `/p <MONEDA>` (ej: `/p BTC`)", user_id)
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        return

    moneda = context.args[0].upper()

    # Notificar que estamos 'escribiendo' para dar feedback visual si tarda la API
    # Solo si es un mensaje nuevo (no un callback de refresh)
    if update.message:
        await update.message.reply_chat_action("typing")

    datos = obtener_datos_moneda(moneda)

    if not datos:
        error_msg = _("😕 No se pudieron obtener los datos para *{moneda}*.", user_id).format(
            moneda=moneda
        )
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        return

    # Helper para formatear cambios porcentuales
    def format_change(change):
        if change is None:
            return "0.00%"
        icon = (
            "😄" if change > 0.5 else ("😕" if change > -0.5 else ("😔" if change > -5 else "😢"))
        )
        sign = "+" if change > 0 else ""
        return f"{sign}{change:.2f}%  {icon}"

    # Helpers de etiquetas
    lbl_eth = _("Ξ:", user_id)
    lbl_btc = _("₿:", user_id)
    lbl_cap = _("Cap:", user_id)
    lbl_vol = _("Vol:", user_id)

    # --- LÓGICA HIGH / LOW ---
    high_24h = datos.get("high_24h", 0)
    low_24h = datos.get("low_24h", 0)

    # Si high es 0, asumimos que no hay datos disponibles y mostramos N/A
    if high_24h > 0:
        str_high = f"${high_24h:,.4f}"
        str_low = f"${low_24h:,.4f}"
    else:
        str_high = "N/A"
        str_low = "N/A"

    # Construcción del Mensaje
    mensaje = (
        f"*{datos['symbol']}*\n—————————————————\n"
        f"💰 *Precio:* ${datos['price']:,.4f}\n"
        f"📈 *High 24h:* {str_high}\n"
        f"📉 *Low 24h:* {str_low}\n"
        f"—————————————————\n"
        f"{lbl_eth} {datos['price_eth']:.8f}\n"
        f"{lbl_btc} {datos['price_btc']:.8f}\n"
        f"1h  {format_change(datos['percent_change_1h'])}\n"
        f"24h {format_change(datos['percent_change_24h'])}\n"
        f"7d  {format_change(datos['percent_change_7d'])}\n"
        f"{lbl_cap} #{datos['market_cap_rank']} | ${datos['market_cap']:,.0f}\n"
        f"{lbl_vol} ${datos['volume_24h']:,.0f}"
    )

    # Inyección de publicidad
    mensaje += get_random_ad_text()

    # Botones de actualizar y análisis técnico
    btn_refresh = _("🔄 Actualizar /p {symbol}", user_id).format(symbol=datos["symbol"])
    btn_ta = _("📊 Ver Análisis Técnico (4H)", user_id)
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(btn_refresh, callback_data=f"refresh_{datos['symbol']}")],
            [InlineKeyboardButton(btn_ta, callback_data=f"ta_quick|{datos['symbol']}|4h")],
        ]
    )

    # Detectar si es un callback (refresh) o un comando nuevo
    # Si es callback, editamos el mensaje existente; si es nuevo, enviamos uno nuevo
    if update.callback_query:
        query = update.callback_query
        try:
            await query.edit_message_text(
                mensaje, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
            )
        except Exception as e:
            # Si el mensaje no cambió (mismo contenido), Telegram lanza error
            # En ese caso, simplemente notificamos al usuario
            if "Message is not modified" in str(e):
                await query.answer("Los datos ya están actualizados")
            else:
                raise
    else:
        await update.message.reply_text(
            mensaje, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )


async def refresh_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    moneda = query.data.replace("refresh_", "").upper()
    context.args = [moneda]
    await p_command(update, context)


@permitted_only
async def ta_quick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback para el botón "Ver Análisis Técnico" en el comando /p.
    Llama al comando /ta con la moneda y timeframe 4h.
    Fuerza el uso de TradingView para evitar el check early de Binance.
    """
    query = update.callback_query
    await query.answer()

    # Parsear callback_data: ta_quick|SYMBOL|4h
    parts = query.data.split("|")
    if len(parts) >= 2:
        moneda = parts[1].upper()
        pair = "USDT"
        timeframe = "4h"

        # Importar y llamar al comando ta con override_args
        # Esto permite el flujo completo: intenta Binance, si falla hace fallback a TV
        from handlers.ta import ta_command

        await ta_command(
            update,
            context,
            override_source="BINANCE",
            override_args=[moneda, pair, timeframe],
            skip_binance_check=True,
        )


# === NUEVA LÓGICA PARA /MK ===


def get_time_str(minutes_delta):
    """Convierte minutos a formato legible (ej: 'in an hour', 'in 2 hours')."""
    hours = int(minutes_delta // 60)
    minutes = int(minutes_delta % 60)

    if hours == 0:
        return f"in {minutes} minutes"
    elif hours == 1:
        return "in an hour"
    else:
        return f"in {hours} hours"


@permitted_only
async def mk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el estado de los mercados globales (Abierto/Cerrado).
    """
    user_id = update.effective_user.id

    # Configuración de Mercados: (Nombre, Emoji, Timezone, Hora Apertura, Hora Cierre)
    # Horas en formato 24h local
    markets = [
        {
            "name": "NYC",
            "flag": "🇺🇸",
            "tz": "America/New_York",
            "open": 9.5,
            "close": 16.0,
        },  # 9:30 - 16:00
        {"name": "Hong Kong", "flag": "🇭🇰", "tz": "Asia/Hong_Kong", "open": 9.5, "close": 16.0},
        {"name": "Tokyo", "flag": "🇯🇵", "tz": "Asia/Tokyo", "open": 9.0, "close": 15.0},
        {"name": "Seoul", "flag": "🇰🇷", "tz": "Asia/Seoul", "open": 9.0, "close": 15.5},
        {"name": "London", "flag": "🇬🇧", "tz": "Europe/London", "open": 8.0, "close": 16.5},
        {"name": "Shanghai", "flag": "🇨🇳", "tz": "Asia/Shanghai", "open": 9.5, "close": 15.0},
        {
            "name": "South Africa",
            "flag": "🇿🇦",
            "tz": "Africa/Johannesburg",
            "open": 9.0,
            "close": 17.0,
        },
        {"name": "Dubai", "flag": "🇦🇪", "tz": "Asia/Dubai", "open": 10.0, "close": 15.0},
        {"name": "Australia", "flag": "🇦🇺", "tz": "Australia/Sydney", "open": 10.0, "close": 16.0},
        {"name": "India", "flag": "🇮🇳", "tz": "Asia/Kolkata", "open": 9.25, "close": 15.5},  # 9:15
        {
            "name": "Russia",
            "flag": "🇷🇺",
            "tz": "Europe/Moscow",
            "open": 10.0,
            "close": 18.75,
        },  # 18:45
        {
            "name": "Germany",
            "flag": "🇩🇪",
            "tz": "Europe/Berlin",
            "open": 9.0,
            "close": 17.5,
        },  # 17:30
        {"name": "Canada", "flag": "🇨🇦", "tz": "America/Toronto", "open": 9.5, "close": 16.0},
        {"name": "Brazil", "flag": "🇧🇷", "tz": "America/Sao_Paulo", "open": 10.0, "close": 17.0},
    ]

    lines = []
    now_utc = datetime.now(pytz.utc)

    for m in markets:
        try:
            tz = pytz.timezone(m["tz"])
            now_local = now_utc.astimezone(tz)

            # Convertir hora actual a float para comparar fácil (ej: 9:30 = 9.5)
            current_float = now_local.hour + (now_local.minute / 60.0)

            # Determinar si es fin de semana (Saturday=5, Sunday=6)
            is_weekend = now_local.weekday() >= 5

            # Estado base
            msg_status = ""

            if not is_weekend and m["open"] <= current_float < m["close"]:
                # Calcular tiempo para cerrar
                minutes_to_close = (m["close"] - current_float) * 60
                time_str = get_time_str(minutes_to_close)
                msg_status = f"Open ✅ closes {time_str}"
            else:
                # Calcular tiempo para abrir
                if is_weekend:
                    # Si es finde, abre el Lunes (calculo aproximado sumando días)
                    days_ahead = 7 - now_local.weekday()  # 7 - 5(Sab) = 2 dias
                    if days_ahead == 0:
                        days_ahead = 1  # Si es Domingo noche y ya pasó la hora 0
                    # Simplificación: "Opens on Monday" o calcular horas reales es complejo
                    msg_status = "Closed ❌ opens Monday"
                elif current_float < m["open"]:
                    # Abre hoy más tarde
                    minutes_to_open = (m["open"] - current_float) * 60
                    time_str = get_time_str(minutes_to_open)
                    msg_status = f"Closed ❌ opens {time_str}"
                else:
                    # Ya cerró hoy, abre mañana
                    # Calculamos horas hasta la medianoche + hora de apertura
                    hours_remaining_today = 24.0 - current_float
                    total_hours = hours_remaining_today + m["open"]
                    time_str = get_time_str(total_hours * 60)
                    msg_status = f"Closed ❌ opens {time_str}"

            lines.append(f"{m['flag']}*{m['name']}*: {msg_status}")

        except Exception as e:
            print(f"Error procesando {m['name']}: {e}")
            lines.append(f"{m['flag']}*{m['name']}*: Error Data")

    # Construir mensaje final con estética del bot
    header = _("🌍 *Estado de Mercados Globales*\n—————————————————\n\n", user_id)
    body = "\n".join(lines)
    footer = get_random_ad_text()

    full_message = header + body + footer

    await update.message.reply_text(full_message, parse_mode=ParseMode.MARKDOWN)
