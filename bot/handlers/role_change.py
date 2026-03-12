"""
Role change command handlers.

Commands:
- /change_role - Request a role change (viewer/trader only)
- /my_role - Show current role and permissions
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.users import get_user
from bot.utils.decorators import permitted_only
from bot.utils.inline_keyboards import build_my_role_keyboard, build_role_change_keyboard


@permitted_only
async def change_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /change_role command.
    Shows role change menu for viewer/trader users.
    """
    chat_id = update.effective_chat.id
    user = await get_user(chat_id)

    if not user:
        await update.message.reply_text("❌ Error: Usuario no encontrado.")
        return

    status = user.get("status")

    # Admin cannot request role change
    if status == "admin":
        await update.message.reply_text("⛔ Los administradores no pueden solicitar cambio de rol.")
        return

    # Check if already pending
    if status == "role_change_pending":
        requested_role = user.get("requested_role", "desconocido")
        await update.message.reply_text(
            f"⏳ Ya tienes una solicitud de cambio de rol pendiente.\n"
            f"Rol solicitado: {requested_role}\n\n"
            "Espera a que un administrador la revise."
        )
        return

    # Determine available roles based on current status
    available_roles = []
    current_role_display = ""

    if status == "viewer":
        available_roles = ["trader", "admin"]
        current_role_display = "👁️ Viewer"
    elif status == "trader":
        available_roles = ["admin"]
        current_role_display = "📊 Trader"
    elif status == "non_permitted":
        await update.message.reply_text("⛔ Necesitas acceso aprobado para solicitar un rol.")
        return
    else:
        # approved status - treat as viewer
        available_roles = ["trader", "admin"]
        current_role_display = "Viewer"

    # Build keyboard
    keyboard = build_role_change_keyboard(available_roles)

    await update.message.reply_text(
        f"🔄 *Solicitud de Cambio de Rol*\n\n"
        f"Rol actual: {current_role_display}\n\n"
        f"Selecciona el rol que deseas solicitar:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def my_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /my_role command.
    Shows current role and permissions.
    """
    chat_id = update.effective_chat.id
    user = await get_user(chat_id)

    if not user:
        await update.message.reply_text("❌ Error: Usuario no encontrado.")
        return

    status = user.get("status")
    username = user.get("username", "usuario")

    # Role display mapping
    role_info = {
        "non_permitted": {
            "emoji": "⛔",
            "name": "Sin Acceso",
            "commands": "Ninguno. Solicita acceso con /start.",
        },
        "pending": {
            "emoji": "⏳",
            "name": "Pendiente",
            "commands": "Esperando aprobación del administrador.",
        },
        "role_change_pending": {
            "emoji": "⏳",
            "name": "Cambio Pendiente",
            "commands": "Tu solicitud está siendo revisada. Usa /help, /change_role, o /my_role.",
        },
        "viewer": {
            "emoji": "👁️",
            "name": "Viewer",
            "commands": (
                "• /help - Ver ayuda\n"
                "• /ta <symbol> - Análisis técnico\n"
                "• /mk - Ver mercados\n"
                "• /p <symbol> - Ver precio\n"
                "• /myid - Ver tu ID\n"
                "• /lang - Cambiar idioma"
            ),
        },
        "trader": {
            "emoji": "📊",
            "name": "Trader",
            "commands": (
                "• /help - Ver ayuda\n"
                "• /ta <symbol> - Análisis técnico\n"
                "• /signal - Generar señal\n"
                "• /chart [tf] - Gráfico con análisis IA\n"
                "• /scenario - Escenarios de mercado\n"
                "• /journal - Historial de señales\n"
                "• /active - Ver trades activos\n"
                "• /capital - Gestión de capital\n"
                "• /setup - Configurar trading\n"
                "• /myid - Ver tu ID\n"
                "• /lang - Cambiar idioma"
            ),
        },
        "admin": {
            "emoji": "⭐",
            "name": "Admin",
            "commands": (
                "• /help - Ver ayuda\n"
                "• /users - Dashboard de usuarios\n"
                "• /logs - Ver logs\n"
                "• /status - Estado del bot\n"
                "• /ad - Gestión de anuncios\n"
                "• /ms - Mensaje masivo\n"
                "• /signal - Generar señal\n"
                "• /journal - Historial\n"
                "• /capital - Gestión de capital\n"
                "• /list_users - Listar usuarios\n"
                "• /set_role - Cambiar rol de usuario"
            ),
        },
    }

    info = role_info.get(status, role_info["non_permitted"])

    message = (
        f"👤 *Tu Rol*\n\n"
        f"Usuario: @{username}\n"
        f"Rol: {info['emoji']} {info['name']}\n"
        f"Estado: `{status}`\n\n"
        f"Comandos disponibles:\n"
        f"{info['commands']}"
    )

    # Add change role button for viewer/trader
    if status in ("viewer", "trader"):
        keyboard = build_my_role_keyboard()
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(message, parse_mode="Markdown")
