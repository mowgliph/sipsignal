"""
Callback handlers for access control inline buttons.

Handles:
- access_approve:<chat_id> - Show role selection menu
- access_deny:<chat_id> - Deny user access
- role_set:<chat_id>:<role> - Set user role and notify
- role_cancel - Cancel role selection
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.core.config import settings
from bot.db.users import deny_user, get_user, set_user_role
from bot.utils.inline_keyboards import build_role_keyboard
from bot.utils.logger import logger


async def access_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle access approve button click.
    Shows role selection menu to admin.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para asignar roles.")
        return

    # Extract chat_id from callback data
    data = query.data
    parts = data.split(":")
    if len(parts) != 2 or parts[0] != "access_approve":
        logger.error(f"Invalid access_approve callback: {data}")
        await query.edit_message_text("❌ Error: Datos de callback inválidos.")
        return

    try:
        user_chat_id = int(parts[1])
    except ValueError:
        logger.error(f"Invalid chat_id in callback: {data}")
        await query.edit_message_text("❌ Error: ID de usuario inválido.")
        return

    # Verify user exists
    user = await get_user(user_chat_id)
    if not user:
        await query.edit_message_text(f"❌ Usuario {user_chat_id} no encontrado.")
        return

    # Build role selection keyboard
    keyboard = build_role_keyboard(user_chat_id)

    # Edit message to show role selection
    await query.edit_message_text(
        f"✅ Usuario aprobado.\n\nSelecciona el rol para @{user.get('username') or 'usuario'}:",
        reply_markup=keyboard,
    )


async def access_deny_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle access deny button click.
    Denies user access and notifies them.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para esta acción.")
        return

    # Extract chat_id from callback data
    data = query.data
    parts = data.split(":")
    if len(parts) != 2 or parts[0] != "access_deny":
        logger.error(f"Invalid access_deny callback: {data}")
        await query.edit_message_text("❌ Error: Datos de callback inválidos.")
        return

    try:
        user_chat_id = int(parts[1])
    except ValueError:
        logger.error(f"Invalid chat_id in callback: {data}")
        await query.edit_message_text("❌ Error: ID de usuario inválido.")
        return

    # Verify user exists
    user = await get_user(user_chat_id)
    if not user:
        await query.edit_message_text(f"❌ Usuario {user_chat_id} no encontrado.")
        return

    # Update user status to non_permitted
    await deny_user(user_chat_id)

    # Edit admin message
    await query.edit_message_text(f"❌ Acceso denegado para @{user.get('username') or 'usuario'}.")

    # Notify user
    bot = context.bot
    try:
        await bot.send_message(
            chat_id=user_chat_id,
            text=(
                "❌ Tu solicitud de acceso ha sido RECHAZADA.\n\n"
                "Si crees que es un error, contacta al administrador."
            ),
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_chat_id} of denial: {e}")


async def role_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role selection button click.
    Sets user role and notifies them.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para asignar roles.")
        return

    # Extract data from callback
    data = query.data
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "role_set":
        logger.error(f"Invalid role_set callback: {data}")
        await query.edit_message_text("❌ Error: Datos de callback inválidos.")
        return

    try:
        user_chat_id = int(parts[1])
        role = parts[2]
    except (ValueError, IndexError):
        logger.error(f"Invalid data in role_set callback: {data}")
        await query.edit_message_text("❌ Error: Datos inválidos.")
        return

    # Validate role
    valid_roles = ["viewer", "trader", "admin"]
    if role not in valid_roles:
        logger.error(f"Invalid role in callback: {role}")
        await query.edit_message_text(f"❌ Rol inválido: {role}")
        return

    # Verify user exists
    user = await get_user(user_chat_id)
    if not user:
        await query.edit_message_text(f"❌ Usuario {user_chat_id} no encontrado.")
        return

    # Update user role
    await set_user_role(user_chat_id, role)

    # Role display mapping
    role_display = {
        "viewer": "👁️ Viewer",
        "trader": "📊 Trader",
        "admin": "⭐ Admin",
    }

    # Edit admin message
    await query.edit_message_text(
        f"✅ Rol asignado: {role_display[role]}\nUsuario: @{user.get('username') or 'usuario'}"
    )

    # Notify user with role-specific commands
    bot = context.bot
    role_commands = {
        "viewer": (
            "• /help - Ver ayuda\n"
            "• /ta <symbol> - Análisis técnico\n"
            "• /mk - Ver mercados\n"
            "• /p <symbol> - Ver precio\n"
        ),
        "trader": (
            "• /help - Ver ayuda\n"
            "• /ta <symbol> - Análisis técnico\n"
            "• /signal - Generar señal\n"
            "• /chart [tf] - Gráfico con análisis\n"
            "• /journal - Historial\n"
            "• /capital - Gestión de capital\n"
        ),
        "admin": (
            "• /help - Ver ayuda\n"
            "• /users - Dashboard de usuarios\n"
            "• /logs - Ver logs\n"
            "• /status - Estado del bot\n"
            "• /signal - Generar señal\n"
            "• /journal - Historial\n"
        ),
    }

    try:
        await bot.send_message(
            chat_id=user_chat_id,
            text=(
                f"✅ ¡Tu acceso ha sido APROBADO!\n\n"
                f"Rol asignado: {role_display[role]}\n\n"
                f"Comandos disponibles:\n"
                f"{role_commands[role]}\n"
                f"¡Empieza con /help para más información!"
            ),
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_chat_id} of role assignment: {e}")


async def role_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role selection cancel button click.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para esta acción.")
        return

    await query.edit_message_text("❌ Operación cancelada.")
