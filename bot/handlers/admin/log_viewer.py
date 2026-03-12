"""Log viewer handler for /logs command."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.core.config import ADMIN_CHAT_IDS, PID, PYTHON_VERSION, STATE, VERSION
from bot.handlers.admin.utils import _
from bot.utils.logger import bot_logger as logger


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /logs para ver las últimas líneas del log."""
    current_chat_id = update.effective_chat.id

    from bot.handlers.admin.utils import _get_logs_data_ref

    # Comprobar si el ID está en la lista de administradores
    if current_chat_id not in ADMIN_CHAT_IDS:
        ultima_actualizacion = "N/A"
        if _get_logs_data_ref:
            log_data_full = _get_logs_data_ref()
            if log_data_full:
                try:
                    timestamp_part = log_data_full[-1].split(" | ")[0].strip()
                    ultima_actualizacion = f"{timestamp_part} UTC"
                except Exception:
                    pass

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
    if not _get_logs_data_ref:
        await update.message.reply_text(
            _("❌ Error interno: La función de logs no ha sido inicializada.", current_chat_id)
        )
        return

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

    log_lines_cleaned = logger.get_log_lines_formatted(n_lineas)
    log_str = "\n".join(log_lines_cleaned)

    ultima_actualizacion = "N/A"
    if log_lines_cleaned:
        try:
            timestamp_part = log_lines_cleaned[-1].split(" | ")[0].strip()
            ultima_actualizacion = f"{timestamp_part} UTC"
        except Exception:
            pass

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

    safe_version = str(VERSION).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_pid = str(PID).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_python_version = str(PYTHON_VERSION).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_estado = str(STATE).replace("_", " ").replace("*", " ").replace("`", " ")
    safe_ultima_actualizacion = (
        str(ultima_actualizacion).replace("_", " ").replace("*", " ").replace("`", " ")
    )

    container = context.bot_data["container"]
    user_repo = container.user_repo

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
