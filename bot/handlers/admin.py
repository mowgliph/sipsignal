# handlers/admin.py

import os
import time
from collections import Counter
from datetime import UTC, datetime, timedelta

import psutil
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.core.config import (
    ADMIN_CHAT_IDS,
    ADS_PATH,
    LAST_PRICES_PATH,
    PID,
    PYTHON_VERSION,
    STATE,
    TEMPLATE_PATH,
    VERSION,
)
from bot.utils.ads_manager import add_ad, delete_ad, load_ads
from bot.utils.logger import logger
from bot.utils.telemetry import (
    get_commands_per_user_from_repo,
    get_daily_events_from_repo,
    get_retention_metrics_from_repo,
    get_users_registration_stats_from_repo,
)


# Función identidad para reemplazar i18n (textos ya están en español)
def _(message, *args, **kwargs):
    return message


# Definimos los estados para nuestra conversación de mensaje masivo
AWAITING_CONTENT, AWAITING_CONFIRMATION, AWAITING_ADDITIONAL_TEXT, AWAITING_ADDITIONAL_PHOTO = (
    range(4)
)


# --- INICIO: NUEVA LÓGICA PARA /ms INTERACTIVO ---
async def ms_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la conversación para el mensaje masivo."""
    chat_id = update.effective_chat.id

    if chat_id not in ADMIN_CHAT_IDS:
        # Mensaje 1: No autorizado
        await update.message.reply_text(
            _("🚫 Comando no autorizado.", chat_id), parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    # Limpiamos datos de conversaciones anteriores
    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    # Mensaje 2: Instrucciones
    mensaje_instrucciones = _(
        "✍️ *Creación de Mensaje Masivo*\n\n"
        "Por favor, envía el contenido principal del mensaje.\n"
        "Puedes enviar una imagen, un texto, o una imagen con texto.",
        chat_id,
    )

    await update.message.reply_text(mensaje_instrucciones, parse_mode=ParseMode.MARKDOWN)
    return AWAITING_CONTENT


async def handle_initial_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el primer contenido enviado (texto o foto)."""
    message = update.message
    chat_id = update.effective_chat.id

    # Textos de los botones
    btn_add_photo = _("🖼️ Añadir Imagen", chat_id)
    btn_send_only_text = _("➡️ Enviar Solo Texto", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)
    btn_add_edit_text = _("✍️ Añadir/Editar Texto", chat_id)
    btn_send_only_photo = _("➡️ Enviar Solo Imagen", chat_id)

    if message.text:
        context.user_data["ms_text"] = message.text
        keyboard = [
            [InlineKeyboardButton(btn_add_photo, callback_data="ms_add_photo")],
            [InlineKeyboardButton(btn_send_only_text, callback_data="ms_send_final")],
            [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
        ]
        # Mensaje 1: Texto recibido, ¿añadir imagen?
        mensaje_texto_recibido = _(
            "✅ Texto recibido. ¿Deseas añadir una imagen o enviar el mensaje?", chat_id
        )
        await message.reply_text(
            mensaje_texto_recibido, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif message.photo:
        context.user_data["ms_photo_id"] = message.photo[-1].file_id
        # Si la imagen tiene un pie de foto, lo guardamos también
        if message.caption:
            context.user_data["ms_text"] = message.caption

        keyboard = [
            [InlineKeyboardButton(btn_add_edit_text, callback_data="ms_add_text")],
            [InlineKeyboardButton(btn_send_only_photo, callback_data="ms_send_final")],
            [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
        ]
        # Mensaje 2: Imagen recibida, ¿añadir/editar texto?
        mensaje_foto_recibida = _(
            "✅ Imagen recibida. ¿Deseas añadir o editar el texto del pie de foto?", chat_id
        )
        await message.reply_text(mensaje_foto_recibida, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # Mensaje 3: Error de contenido
        mensaje_error_contenido = _("⚠️ Por favor, envía un texto o una imagen.", chat_id)
        await message.reply_text(mensaje_error_contenido)
        return AWAITING_CONTENT

    return AWAITING_CONFIRMATION


async def handle_confirmation_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja los botones de confirmación."""
    query = update.callback_query
    await query.answer()
    choice = query.data
    user_id = query.from_user.id

    if choice == "ms_add_text":
        mensaje_add_text = _(
            "✍️ De acuerdo, por favor envía el texto que quieres usar como pie de foto.", user_id
        )
        await query.edit_message_text(mensaje_add_text)
        return AWAITING_ADDITIONAL_TEXT
    elif choice == "ms_add_photo":
        mensaje_add_photo = _(
            "🖼️ Entendido, por favor envía la imagen que quieres adjuntar.", user_id
        )
        await query.edit_message_text(mensaje_add_photo)
        return AWAITING_ADDITIONAL_PHOTO
    elif choice == "ms_send_final":
        return await send_broadcast(query, context)
    elif choice == "ms_cancel":
        mensaje_cancelar = _("🚫 Operación cancelada.", user_id)
        await query.edit_message_text(mensaje_cancelar)
        return ConversationHandler.END


async def receive_additional_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el texto adicional para una imagen."""
    chat_id = update.effective_chat.id
    context.user_data["ms_text"] = update.message.text

    # Textos de los botones
    btn_send = _("🚀 Enviar a todos los usuarios", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)

    keyboard = [
        [InlineKeyboardButton(btn_send, callback_data="ms_send_final")],
        [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
    ]

    # Mensaje de confirmación
    mensaje_confirmacion = _("✅ Texto añadido. El mensaje está listo para ser enviado.", chat_id)

    await update.message.reply_text(
        mensaje_confirmacion, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_CONFIRMATION


async def receive_additional_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la imagen adicional para un texto."""
    chat_id = update.effective_chat.id
    context.user_data["ms_photo_id"] = update.message.photo[-1].file_id

    # TextOS de los botones
    btn_send = _("🚀 Enviar a todos los usuarios", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)

    keyboard = [
        [InlineKeyboardButton(btn_send, callback_data="ms_send_final")],
        [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
    ]

    # Mensaje de confirmación
    mensaje_confirmacion = _("✅ Imagen añadida. El mensaje está listo para ser enviado.", chat_id)

    await update.message.reply_text(
        mensaje_confirmacion, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_CONFIRMATION


async def send_broadcast(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función final que envía el mensaje a todos los usuarios."""
    chat_id = query.from_user.id

    # Mensaje 1: Iniciando envío
    mensaje_iniciando = _(
        "⏳ *Enviando mensaje a todos los usuarios...*\nEsto puede tardar un momento.", chat_id
    )
    await query.edit_message_text(mensaje_iniciando, parse_mode=ParseMode.MARKDOWN)

    global _enviar_mensaje_telegram_async_ref
    if not _enviar_mensaje_telegram_async_ref:
        # Mensaje 2: Error interno
        mensaje_error_interno = _(
            "❌ Error interno: La función de envío masivo no ha sido inicializada.", chat_id
        )
        await query.message.reply_text(mensaje_error_interno)
        return ConversationHandler.END

    text_to_send = context.user_data.get("ms_text", "")
    photo_id_to_send = context.user_data.get("ms_photo_id")

    # Get container and repository
    container = context.bot_data["container"]
    user_repo = container.user_repo

    # Get all users from PostgreSQL
    usuarios = await user_repo.get_all()
    chat_ids = [str(u["user_id"]) for u in usuarios]

    fallidos = await _enviar_mensaje_telegram_async_ref(
        text_to_send, chat_ids, photo=photo_id_to_send
    )

    total_enviados = len(chat_ids) - len(fallidos)
    if fallidos:
        # Mensaje 3a: Reporte de fallos
        fallidos_reporte = [f"  - `{chat_id}`: _{error}_" for chat_id, error in fallidos.items()]
        fallidos_str = "\n".join(fallidos_reporte)

        mensaje_admin_base = _(
            "✅ Envío completado.\n\n"
            "Enviado a *{total_enviados}* de {total_usuarios} usuarios.\n\n"
            "❌ Fallos ({num_fallos}):\n{fallidos_str}",
            chat_id,
        )
        mensaje_admin = mensaje_admin_base.format(
            total_enviados=total_enviados,
            total_usuarios=len(chat_ids),
            num_fallos=len(fallidos),
            fallidos_str=fallidos_str,
        )
    else:
        # Mensaje 3b: Éxito total
        mensaje_admin_base = _(
            "✅ ¡Éxito! Mensaje enviado a todos los *{total_usuarios}* usuarios.", chat_id
        )
        mensaje_admin = mensaje_admin_base.format(total_usuarios=len(chat_ids))

    await query.message.reply_text(mensaje_admin, parse_mode=ParseMode.MARKDOWN)

    # Limpiar datos al finalizar
    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    return ConversationHandler.END


async def cancel_ms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función para cancelar la conversación."""
    chat_id = update.effective_chat.id

    mensaje_cancelado = _("🚫 Operación cancelada.", chat_id)

    await update.message.reply_text(mensaje_cancelado)

    # Limpiar datos al cancelar
    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    return ConversationHandler.END


# Definición del ConversationHandler para el comando /ms
# Definición del ConversationHandler para el comando /ms
ms_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("ms", ms_start)],
    states={
        AWAITING_CONTENT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_content),
            MessageHandler(filters.PHOTO, handle_initial_content),
        ],
        AWAITING_CONFIRMATION: [CallbackQueryHandler(handle_confirmation_choice)],
        AWAITING_ADDITIONAL_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_additional_text)
        ],
        AWAITING_ADDITIONAL_PHOTO: [MessageHandler(filters.PHOTO, receive_additional_photo)],
    },
    fallbacks=[CommandHandler("cancelar", cancel_ms)],
    conversation_timeout=600,
    # per_message=True # <---  COMENTANDO ESTA LÍNEA
)
# Referencias para inyección de funciones
# Estas referencias se inyectan desde bbalert para enviar mensajes masivos y obtener logs
_enviar_mensaje_telegram_async_ref = None
_get_logs_data_ref = None


def set_admin_util(func):
    """Permite a bbalert inyectar la función de envío masivo."""
    global _enviar_mensaje_telegram_async_ref
    _enviar_mensaje_telegram_async_ref = func


def set_logs_util(func):
    """Permite a bbalert inyectar la función para obtener los logs."""
    global _get_logs_data_ref
    _get_logs_data_ref = func


# ==============================================================================
# COMANDO /users (REFORMADO - DASHBOARD SUPER PRO)
# ==============================================================================

# --- DEFINICIÓN GLOBAL DEL OBJETO PSUTIL
# Al iniciarlo aquí, el objeto se mantiene vivo todo el tiempo que el bot corre.
proc_global = psutil.Process(os.getpid())
# Hacemos una primera lectura "falsa" al arrancar para iniciar el contador
proc_global.cpu_percent(interval=None)


def _clean_markdown(text):
    """Clean text for Markdown by removing problematic characters.

    Replaces Markdown special chars with spaces to prevent parsing errors
    while keeping the text readable (no visible backslashes).
    """
    if text is None:
        return ""
    text = str(text)
    # Replace with spaces to avoid visible escape characters
    return (
        text.replace("_", " ")
        .replace("*", " ")
        .replace("`", " ")
        .replace("[", "(")
        .replace("]", ")")
    )


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dashboard de Administración SUPER PRO.
    Muestra estadísticas de Usuarios, Negocio, Carga, BTC, HBD, Clima y Valerts.
    """
    chat_id = update.effective_chat.id
    chat_id_str = str(chat_id)

    # Get container and repositories
    container = context.bot_data["container"]
    user_repo = container.user_repo
    watchlist_repo = container.user_watchlist_repo
    preference_repo = container.user_preference_repo

    # 1. CARGA DE DATOS (Centralizada)
    # Get all users from PostgreSQL
    usuarios = await user_repo.get_all()
    usuarios_dict = {str(u["user_id"]): u for u in usuarios}

    # Sistemas eliminados: price alerts, valerts, btc - mostrar 0
    all_alerts = {}

    # Nota: Valerts fue eliminado - los contadores de ese servicio se muestran en 0

    # 2. VISTA DE USUARIO NORMAL (Perfil Propio)
    if chat_id not in ADMIN_CHAT_IDS:
        user_data = usuarios_dict.get(chat_id_str)
        if not user_data:
            await update.message.reply_text(_("❌ No estás registrado.", chat_id))
            return

        # Get user's watchlist coins from PostgreSQL
        monedas = await watchlist_repo.get_coins(chat_id)
        # Get user's HBD alerts preference from PostgreSQL
        hbd_enabled = await preference_repo.get_hbd_alerts(chat_id)

        alerts_count = 0  # Sistema de alertas eliminado

        # Estados de servicios - BTC eliminado
        btc_status = "❌ Eliminado"
        hbd_status = "✅ Activado" if hbd_enabled else "❌ Desactivado"

        # Nota: Suscripciones eliminadas - no se muestran
        subs_txt = "_Sin suscripciones activas_"

        msg = (
            f"👤 *TU PERFIL SIPSIGNAL*\n"
            f"—————————————————\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🗣 Idioma: `{user_data.get('language', 'es')}`\n\n"
            f"📊 *Configuración:*\n"
            f"• Monedas Lista: `{', '.join(monedas)}`\n"
            f"• Alertas Cruce: `{alerts_count}` activas\n\n"
            f"📡 *Servicios Activos:*\n"
            f"• Monitor BTC: {btc_status}\n"
            f"• Monitor HBD: {hbd_status}\n\n"
            f"💎 *Suscripciones:*\n"
            f"{subs_txt}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    # 3. VISTA DE ADMINISTRADOR (DASHBOARD PRO)
    msg_loading = await update.message.reply_text(
        _("⏳ *Analizando Big Data...*", chat_id), parse_mode=ParseMode.MARKDOWN
    )

    # --- NUEVAS MÉTRICAS DE TELEMETRÍA (desde PostgreSQL) ---
    retention = get_retention_metrics_from_repo(user_repo)
    cmd_stats = get_commands_per_user_from_repo(user_repo, container.user_usage_stats_repo)
    daily_events = get_daily_events_from_repo(user_repo, container.user_usage_stats_repo)
    reg_stats = get_users_registration_stats_from_repo(user_repo)

    # --- A. CÁLCULOS DE USUARIOS ---
    total_users = len(usuarios)
    active_24h = 0
    active_7d = 0
    active_30d = 0
    lang_es = 0
    lang_en = 0

    # Contadores de nuevos usuarios
    new_today = 0
    new_7d = 0
    new_30d = 0

    # Contadores de Carga (Uso hoy)
    total_usage_today = 0
    usage_breakdown = Counter()

    now = datetime.now(UTC)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    for _uid, u in usuarios.items():
        # 1. Actividad — BUG-1 FIX: usar last_seen (actividad real) con total_seconds
        #    Fallback a last_alert_timestamp para usuarios sin last_seen aún
        last_seen_str = u.get("last_seen") or u.get("last_alert_timestamp")
        if last_seen_str:
            try:
                last_dt = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                delta = now - last_dt
                # BUG-1 FIX: .days < 1 solo cuenta días completos; total_seconds es exacto
                if delta.total_seconds() < 86400:
                    active_24h += 1
                if delta.total_seconds() < 86400 * 7:
                    active_7d += 1
                if delta.total_seconds() < 86400 * 30:
                    active_30d += 1
            except Exception:
                pass

        # 2. Nuevos usuarios (basado en registered_at)
        reg_str = u.get("registered_at")
        if reg_str:
            try:
                reg_dt = datetime.strptime(reg_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                if reg_dt >= cutoff_24h:
                    new_today += 1
                if reg_dt >= cutoff_7d:
                    new_7d += 1
                if reg_dt >= cutoff_30d:
                    new_30d += 1
            except Exception:
                pass

        # 3. Idioma
        if u.get("language") == "en":
            lang_en += 1
        else:
            lang_es += 1

        # 5. Uso Diario (Carga del Bot)
        daily = u.get("daily_usage", {})
        if daily.get("date") == now.strftime("%Y-%m-%d"):
            for cmd, count in daily.items():
                if cmd != "date" and isinstance(count, int):
                    usage_breakdown[cmd] += count
                    total_usage_today += count

    # --- B. CÁLCULOS DE ALERTAS & MONEDAS ---
    total_alerts_active = 0
    coin_popularity = Counter()

    for _uid, alerts in all_alerts.items():
        for a in alerts:
            if a["status"] == "ACTIVE":
                total_alerts_active += 1
                coin_popularity[a["coin"]] += 1

    # top_coins removed - sistema de alertas eliminado

    # --- C. CÁLCULOS DE SERVICIOS (BTC, HBD, VALERTS) ---

    # 1. BTC - Sistema eliminado ya, se usa btc_subscribers = 0 (ya asignado antes)

    # 2. HBD

    # 3. VALERTS (Volatilidad) - Sistema eliminado, mostrar 0

    # --- D. CÁLCULOS DE RECURSOS (RAM, CPU, Uptime) ---
    # BUG-5 FIX: Eliminar doble instanciación de psutil.Process — reusar proc_global
    # 1. Uso de Memoria y CPU
    mem_usage = proc_global.memory_info().rss / 1024 / 1024  # MB
    mem_asignada = proc_global.memory_info().vms / 1024 / 1024  # MB
    cpu_percent = proc_global.cpu_percent(interval=None)

    # 2. Uptime (usando proc_global ya existente)
    uptime_seconds = time.time() - proc_global.create_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))

    # 3. Size file
    size = {"file_size": 0}
    archivos = [
        ADS_PATH,
        LAST_PRICES_PATH,
        TEMPLATE_PATH,
    ]

    total_kb = 0
    for ruta in archivos:
        try:
            if os.path.exists(ruta):  # Verificamos que el archivo exista
                total_kb += os.path.getsize(ruta)
        except Exception:
            continue

    size["file_size"] = total_kb / 1024 / 1024  # MB

    # --- E. TOP COMANDOS DEL DÍA ---
    top_cmds = usage_breakdown.most_common(5)
    top_cmds_lines = []
    cmd_emojis = {
        "ver": "👁",
        "tasa": "💱",
        "ta": "📈",
        "temp_changes": "⏱",
        "reminders": "⏰",
        "btc": "🦁",
    }
    for i, (cmd, cnt) in enumerate(top_cmds, 1):
        emoji = cmd_emojis.get(cmd, "⚙️")
        top_cmds_lines.append(f"  {i}. {emoji} /{cmd}: `{cnt}`")
    top_cmds_str = "\n".join(top_cmds_lines) if top_cmds_lines else "  _Sin datos aún_"

    # --- CONSTRUCCIÓN DEL DASHBOARD v2 ---
    pct_24h = int(active_24h / total_users * 100) if total_users else 0
    pct_7d = int(active_7d / total_users * 100) if total_users else 0
    pct_30d = int(active_30d / total_users * 100) if total_users else 0

    # Escape all values for Markdown to prevent parsing errors
    uptime_str_esc = _clean_markdown(uptime_str)
    mem_usage_esc = _clean_markdown(f"{mem_usage:.2f}")
    mem_asignada_esc = _clean_markdown(f"{mem_asignada:.2f}")
    cpu_percent_esc = _clean_markdown(cpu_percent)
    size_file_esc = _clean_markdown(f"{size['file_size']:.2f}")
    total_usage_today_esc = _clean_markdown(total_usage_today)
    usage_ver_esc = _clean_markdown(usage_breakdown["ver"])
    usage_ta_esc = _clean_markdown(usage_breakdown["ta"])
    top_cmds_str_esc = _clean_markdown(top_cmds_str)
    total_users_esc = _clean_markdown(total_users)
    lang_es_esc = _clean_markdown(lang_es)
    lang_en_esc = _clean_markdown(lang_en)
    active_24h_esc = _clean_markdown(active_24h)
    pct_24h_esc = _clean_markdown(pct_24h)
    active_7d_esc = _clean_markdown(active_7d)
    pct_7d_esc = _clean_markdown(pct_7d)
    active_30d_esc = _clean_markdown(active_30d)
    pct_30d_esc = _clean_markdown(pct_30d)
    new_today_esc = _clean_markdown(new_today)
    new_7d_esc = _clean_markdown(new_7d)
    new_30d_esc = _clean_markdown(new_30d)
    reg_stats_with_esc = _clean_markdown(reg_stats["with_registered_at"])
    reg_stats_quality_esc = _clean_markdown(reg_stats["data_quality_pct"])
    retention_7d_esc = _clean_markdown(retention["retention_7d"])
    churn_rate_esc = _clean_markdown(retention["churn_rate"])
    stickiness_esc = _clean_markdown(retention["stickiness"])
    daily_joins_esc = _clean_markdown(daily_events["joins_today"])
    daily_commands_esc = _clean_markdown(daily_events["commands_today"])
    cmd_avg_esc = _clean_markdown(cmd_stats["avg_per_user"])
    version_esc = _clean_markdown(VERSION)
    now_str_esc = _clean_markdown(now.strftime("%Y-%m-%d %H:%M"))
    top_coins_str_esc = _clean_markdown("")  # Sin datos de alertas
    dashboard = (
        f"👮‍♂️ *PANEL DE CONTROL* v{version_esc}\n"
        f"📅 {now_str_esc}\n"
        f"———————————————————\n\n"
        f"*🖥️ ESTADO DEL SISTEMA*\n"
        f"├ *Uptime:* `{uptime_str_esc}`\n"
        f"├ *RAM:* `{mem_usage_esc} MB`\n"
        f"├ *VMS:* `{mem_asignada_esc} MB`\n"
        f"├ *CPU:* `{cpu_percent_esc}%`\n"
        f"└ *DATA:* `{size_file_esc} MB`\n\n"
        f"⚙️ *CARGA DEL SISTEMA (Hoy)*\n"
        f"├ Comandos Procesados: `{total_usage_today_esc}`\n"
        f"├ /ver: `{usage_ver_esc}` | /ta: `{usage_ta_esc}`\n"
        f"└ Top Comandos:\n{top_cmds_str_esc}\n\n"
        f"👥 *USUARIOS*\n"
        f"├ Totales: `{total_users_esc}` | 🇪🇸 {lang_es_esc} | 🇺🇸 {lang_en_esc}\n"
        f"├ Activos 24h: `{active_24h_esc}` ({pct_24h_esc}%)\n"
        f"├ Activos 7d:  `{active_7d_esc}` ({pct_7d_esc}%)\n"
        f"├ Activos 30d: `{active_30d_esc}` ({pct_30d_esc}%)\n"
        f"├ Nuevos: hoy `{new_today_esc}` | 7d `{new_7d_esc}` | 30d `{new_30d_esc}`\n"
        f"└ Datos completos: `{reg_stats_with_esc}/{total_users_esc}` ({reg_stats_quality_esc}%)\n\n"
        f"📊 *MÉTRICAS DE RETENCIÓN*\n"
        f"├ Retención 7d: `{retention_7d_esc}%`\n"
        f"├ Churn: `{churn_rate_esc}%`\n"
        f"└ Stickiness: `{stickiness_esc}%` (DAU/MAU)\n\n"
        f"📈 *EVENTOS HOY*\n"
        f"├ Nuevos: `{daily_joins_esc}`\n"
        f"├ Comandos: `{daily_commands_esc}`\n"
        f"└ Promedio/cmd: `{cmd_avg_esc}`\n\n"
        f"🏆 *TENDENCIAS DE MERCADO*\n"
        f"🔥 Top Monedas:\n"
        f"`{top_coins_str_esc}`\n"
    )

    await msg_loading.edit_text(dashboard, parse_mode=ParseMode.MARKDOWN)


# COMANDO /logs para ver las últimas líneas del log
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_chat_id = update.effective_chat.id  # <-- Obtener chat_id
    global _get_logs_data_ref  # <--- ¡ARREGLO 1: Mover esta línea aquí!

    # Comprobar si el ID está en la lista de administradores
    if current_chat_id not in ADMIN_CHAT_IDS:
        # Obtener la última actualización desde el log si es posible
        # global _get_logs_data_ref <--- Quitarla de aquí
        ultima_actualizacion = "N/A"
        if _get_logs_data_ref:
            log_data_full = _get_logs_data_ref()
            if log_data_full:
                try:
                    timestamp_part = log_data_full[-1].split(" | ")[0].strip()
                    ultima_actualizacion = f"{timestamp_part} UTC"
                except Exception:
                    pass

        # --- PLANTILLA ENVUELTA ---
        mensaje_template = _(
            "🤖 *Estado de Sip Signal*\n\n"
            "—————————————————\n"
            "• Versión: {version} 🤖\n"
            "• Estado: {estado} 👌\n"
            "• Última Actualización: {ultima_actualizacion} 🕒 \n"
            "—————————————————\n\n"
            "_Ya, eso es todo lo que puedes ver mi tanke 🙂👍_",
            current_chat_id,
        )

        # --- ¡NUEVA SECCIÓN DE ESCAPE! ---
        # Escapamos las variables para evitar errores de Markdown
        safe_version = str(VERSION).replace("_", " ").replace("*", " ").replace("`", " ")
        safe_estado = str(STATE).replace("_", " ").replace("*", " ").replace("`", " ")
        safe_ultima_actualizacion = (
            str(ultima_actualizacion).replace("_", " ").replace("*", " ").replace("`", " ")
        )

        mensaje = mensaje_template.format(
            version=safe_version, estado=safe_estado, ultima_actualizacion=safe_ultima_actualizacion
        )
        await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)
        return

    # --- Lógica de Administrador ---

    # Verificar que la función de logs ha sido inyectada correctamente
    if not _get_logs_data_ref:
        await update.message.reply_text(
            _("❌ Error interno: La función de logs no ha sido inicializada.", current_chat_id)
        )
        return

    # Obtener últimas N líneas de log formateadas
    n_lineas_default = 10
    try:
        n_lineas = (
            int(context.args[0]) if context.args and context.args[0].isdigit() else n_lineas_default
        )
        n_lineas = max(1, min(n_lineas, 100))
    except ValueError:
        await update.message.reply_text(
            _("⚠️ El argumento debe ser un número entero.", current_chat_id)
        )
        return

    # Get formatted log lines from logger
    log_lines_cleaned = logger.get_log_lines_formatted(n_lineas)
    log_str = "\n".join(log_lines_cleaned)

    # Extraer la marca de tiempo de la última línea del log
    ultima_actualizacion = "N/A"
    if log_lines_cleaned:
        try:
            timestamp_part = log_lines_cleaned[-1].split(" | ")[0].strip()
            ultima_actualizacion = f"{timestamp_part} UTC"
        except Exception:
            pass

    # 3. Mensaje de respuesta completo para administradores
    # --- PLANTILLA ENVUELTA ---
    mensaje_template = _(
        "🤖 *Estado de Sip Signal*\n"
        "—————————————————\n"
        "• Versión: {version} 🤖\n"
        "• PID: {pid} 🪪\n"
        "• Python: {python_version} 🐍\n"
        "• Usuarios: {num_usuarios} 👥\n"
        "• Estado: {estado} 👌\n"
        "• Última Actualización: {ultima_actualizacion} 🕒 \n"
        "—————————————————\n"
        "•📜 *Últimas {num_lineas} líneas*\n ```{log_str}```\n",
        current_chat_id,
    )

    # --- ¡NUEVA SECCIÓN DE ESCAPE (PARA ADMIN)! ---
    # Escapamos todas las variables que podrían contener _ * `
    safe_version = str(VERSION).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_pid = str(PID).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_python_version = str(PYTHON_VERSION).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_estado = str(STATE).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_ultima_actualizacion = (
        str(ultima_actualizacion).replace("_", " ").replace("*", " ").replace("`", " ")
    )

    # Get container and repository
    container = context.bot_data["container"]
    user_repo = container.user_repo

    # Get user count from PostgreSQL
    usuarios = await user_repo.get_all()
    num_usuarios = len(usuarios)

    mensaje = mensaje_template.format(
        version=safe_version,
        pid=safe_pid,
        python_version=safe_python_version,
        num_usuarios=num_usuarios,
        estado=safe_estado,
        ultima_actualizacion=safe_ultima_actualizacion,
        num_lineas=len(log_lines_cleaned),
        log_str=log_str,
    )

    await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)


# --- COMANDO /ad SUPER ROBUSTO ---
async def ad_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestión de anuncios robusta.
    Si el Markdown del usuario falla, se envía en texto plano.
    """
    chat_id = update.effective_chat.id

    if chat_id not in ADMIN_CHAT_IDS:
        return

    args = context.args

    # --- LISTAR ANUNCIOS ---
    if not args:
        ads = load_ads()
        if not ads:
            await update.message.reply_text(
                _("📭 No hay anuncios activos.\nUsa `/ad add Mi Anuncio` para crear uno.", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        mensaje = _("📢 *Lista de Anuncios Activos:*\n\n", chat_id)
        for i, ad in enumerate(ads):
            # Intentamos preservar el formato que haya puesto el usuario
            mensaje += f"*{i + 1}.* {ad}\n"

        mensaje += _("\nPara borrar: `/ad del N` (ej: `/ad del 1`)", chat_id)

        try:
            await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)
        except BadRequest:
            # FALLBACK: Si falla el Markdown (ej: un '_' sin cerrar), enviamos texto plano
            fallback_msg = _(
                "⚠️ *Error de visualización Markdown*\n"
                "Alguno de tus anuncios tiene caracteres especiales sin cerrar, pero aquí está la lista en texto plano:\n\n",
                chat_id,
            )
            for i, ad in enumerate(ads):
                fallback_msg += f"{i + 1}. {ad}\n"

            fallback_msg += _("\nUsa /ad del N para eliminar.", chat_id)
            await update.message.reply_text(fallback_msg)  # Sin parse_mode
        return

    accion = args[0].lower()

    # --- AÑADIR ANUNCIO ---
    if accion == "add":
        if len(args) < 2:
            await update.message.reply_text(
                _("⚠️ Escribe el texto del anuncio.\nEj: `/ad add Visita mi canal @canal`", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        texto_nuevo = " ".join(args[1:])
        add_ad(texto_nuevo)  # Guardamos EXACTAMENTE lo que escribió el usuario

        # Intentamos confirmar con Markdown bonito
        try:
            await update.message.reply_text(
                _("✅ Anuncio añadido:\n\n_{ad_text}_", chat_id).format(ad_text=texto_nuevo),
                parse_mode=ParseMode.MARKDOWN,
            )
        except BadRequest:
            # Si falla (ej: usuario puso 'pepe_bot' sin escapar), confirmamos en texto plano
            await update.message.reply_text(
                _(
                    "✅ Anuncio añadido (Sintaxis MD inválida, mostrado plano):\n\n{ad_text}",
                    chat_id,
                ).format(ad_text=texto_nuevo)
            )

    # --- BORRAR ANUNCIO ---
    elif accion == "del":
        try:
            indice = int(args[1]) - 1
            eliminado = delete_ad(indice)
            if eliminado:
                # Intentamos mostrar confirmación bonita
                try:
                    await update.message.reply_text(
                        _("🗑️ Anuncio eliminado:\n\n_{ad_text}_", chat_id).format(ad_text=eliminado),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except BadRequest:
                    # Si falla, confirmamos en texto plano
                    await update.message.reply_text(
                        _("🗑️ Anuncio eliminado:\n\n{ad_text}", chat_id).format(ad_text=eliminado)
                    )
            else:
                await update.message.reply_text(
                    _("⚠️ Número de anuncio no válido.", chat_id), parse_mode=ParseMode.MARKDOWN
                )
        except (IndexError, ValueError):
            await update.message.reply_text(
                _("⚠️ Uso: `/ad del N` (N es el número del anuncio).", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        await update.message.reply_text(
            _("⚠️ Comandos: `/ad`, `/ad add <txt>`, `/ad del <num>`", chat_id),
            parse_mode=ParseMode.MARKDOWN,
        )
