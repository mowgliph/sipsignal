"""
Callback handlers for role change requests.

Handles:
- role_change_request:<role> - Create role change request, notify admins
- role_change_approve:<user_id>:<role> - Approve role change
- role_change_deny:<user_id> - Deny role change
- role_change_cancel - Cancel role change request
- my_role_change_request - Trigger role change request from /my_role
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.core.config import settings
from bot.db.users import (
    approve_role_change,
    deny_role_change,
    get_user,
    request_role_change,
)
from bot.utils.inline_keyboards import (
    build_role_change_admin_keyboard,
    build_role_change_keyboard,
)
from bot.utils.logger import logger


async def role_change_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role change request button click.
    Creates role change request and notifies admins.
    """
    query = update.callback_query
    await query.answer()

    chat_id = query.from_user.id

    # Extract role from callback data
    data = query.data
    parts = data.split(":")
    if len(parts) != 2 or parts[0] != "role_change_request":
        logger.error(f"Invalid role_change_request callback: {data}")
        await query.edit_message_text("❌ Error: Datos de callback inválidos.")
        return

    role = parts[1]

    # Validate role
    valid_roles = ["viewer", "trader", "admin"]
    if role not in valid_roles:
        logger.error(f"Invalid role in callback: {role}")
        await query.edit_message_text(f"❌ Rol inválido: {role}")
        return

    # Get current user
    user = await get_user(chat_id)
    if not user:
        await query.edit_message_text("❌ Error: Usuario no encontrado.")
        return

    current_status = user.get("status")

    # Check if already pending
    if current_status == "role_change_pending":
        await query.edit_message_text(
            "⏳ Ya tienes una solicitud pendiente. Espera la revisión del administrador."
        )
        return

    # Validate role change is allowed
    if current_status == "viewer" and role not in ["trader", "admin"]:
        await query.edit_message_text("❌ Rol no disponible para tu nivel actual.")
        return
    if current_status == "trader" and role != "admin":
        await query.edit_message_text("❌ Rol no disponible para tu nivel actual.")
        return
    if current_status == "admin":
        await query.edit_message_text("⛔ Los administradores no pueden solicitar cambio de rol.")
        return

    # Create role change request
    await request_role_change(chat_id, role)

    # Role display mapping
    role_display = {
        "viewer": "👁️ Viewer",
        "trader": "📊 Trader",
        "admin": "⭐ Admin",
    }

    # Update user's message
    await query.edit_message_text(
        f"✅ Solicitud enviada.\n\n"
        f"Rol solicitado: {role_display[role]}\n\n"
        f"Un administrador revisará tu solicitud. "
        f"Tu cuenta está BLOQUEADA hasta que sea aprobada o rechazada."
    )

    # Notify admins
    username = user.get("username")
    user_info = f"@{username}" if username else f"Chat ID: `{chat_id}`"

    notification = (
        f"🔔 *Solicitud de Cambio de Rol*\n\n"
        f"Usuario: {user_info}\n"
        f"Rol actual: {role_display.get(current_status, 'Desconocido')}\n"
        f"Rol solicitado: {role_display[role]}\n"
        f"Estado: BLOQUEADO hasta aprobación\n\n"
    )

    keyboard = build_role_change_admin_keyboard(chat_id, role)

    for admin_id in settings.admin_chat_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=notification,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id} of role change request: {e}")


async def role_change_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role change approve button click from admin.
    Approves the role change and notifies the user.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para aprobar cambios de rol.")
        return

    # Extract data from callback
    data = query.data
    parts = data.split(":")
    if len(parts) != 3 or parts[0] != "role_change_approve":
        logger.error(f"Invalid role_change_approve callback: {data}")
        await query.edit_message_text("❌ Error: Datos de callback inválidos.")
        return

    try:
        user_chat_id = int(parts[1])
        new_role = parts[2]
    except (ValueError, IndexError):
        logger.error(f"Invalid data in role_change_approve callback: {data}")
        await query.edit_message_text("❌ Error: Datos inválidos.")
        return

    # Verify user exists
    user = await get_user(user_chat_id)
    if not user:
        await query.edit_message_text(f"❌ Usuario {user_chat_id} no encontrado.")
        return

    # Approve role change
    await approve_role_change(user_chat_id, new_role)

    # Role display mapping
    role_display = {
        "viewer": "👁️ Viewer",
        "trader": "📊 Trader",
        "admin": "⭐ Admin",
    }

    # Update admin message
    username = user.get("username")
    await query.edit_message_text(
        f"✅ Cambio de rol aprobado.\n\n"
        f"Usuario: @{username or user_chat_id}\n"
        f"Nuevo rol: {role_display[new_role]}"
    )

    # Notify user
    old_role = user.get("status", "desconocido")
    try:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=(
                f"✅ ¡Tu rol ha sido actualizado!\n\n"
                f"Rol anterior: {role_display.get(old_role, old_role)}\n"
                f"Nuevo rol: {role_display[new_role]}\n\n"
                f"¡Empieza con /help para ver los comandos disponibles!"
            ),
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_chat_id} of role change approval: {e}")


async def role_change_deny_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role change deny button click from admin.
    Denies the role change and restores previous role.
    """
    query = update.callback_query
    await query.answer()

    # Check if admin
    if query.from_user.id not in settings.admin_chat_ids:
        await query.edit_message_text("⛔ No tienes permisos para esta acción.")
        return

    # Extract data from callback
    data = query.data
    parts = data.split(":")
    if len(parts) != 2 or parts[0] != "role_change_deny":
        logger.error(f"Invalid role_change_deny callback: {data}")
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

    # Get requested role before denying
    requested_role = user.get("requested_role", "desconocido")

    # Deny role change (restores previous role)
    await deny_role_change(user_chat_id)

    # Update admin message
    username = user.get("username")
    await query.edit_message_text(
        f"❌ Cambio de rol rechazado.\n\n"
        f"Usuario: @{username or user_chat_id}\n"
        f"Rol solicitado: {requested_role}\n"
        f"El usuario mantiene su rol anterior."
    )

    # Notify user
    role_display = {
        "viewer": "👁️ Viewer",
        "trader": "📊 Trader",
        "admin": "⭐ Admin",
    }
    current_role = user.get("status", "desconocido")

    try:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=(
                f"❌ Tu solicitud de cambio de rol ha sido RECHAZADA.\n\n"
                f"Tu rol actual se mantiene: {role_display.get(current_role, current_role)}"
            ),
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_chat_id} of role change denial: {e}")


async def role_change_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role change cancel button click.
    """
    query = update.callback_query
    await query.answer()

    chat_id = query.from_user.id
    user = await get_user(chat_id)

    if not user:
        await query.edit_message_text("❌ Error: Usuario no encontrado.")
        return

    # Check if user has a pending request
    if user.get("status") != "role_change_pending":
        await query.edit_message_text("ℹ️ No tienes una solicitud pendiente.")
        return

    # Note: We don't automatically cancel the request here.
    # Only admins can approve/deny requests.
    await query.edit_message_text(
        "⏳ Tu solicitud está siendo revisada por un administrador.\n"
        "No puedes cancelarla directamente. Contacta a un admin si necesitas ayuda."
    )


async def my_role_change_request_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle my_role_change_request button click from /my_role command.
    Shows role change menu.
    """
    query = update.callback_query
    await query.answer()

    chat_id = query.from_user.id
    user = await get_user(chat_id)

    if not user:
        await query.edit_message_text("❌ Error: Usuario no encontrado.")
        return

    status = user.get("status")

    # Check if already pending
    if status == "role_change_pending":
        requested_role = user.get("requested_role", "desconocido")
        await query.edit_message_text(
            f"⏳ Ya tienes una solicitud de cambio de rol pendiente.\n"
            f"Rol solicitado: {requested_role}\n\n"
            "Espera a que un administrador la revise."
        )
        return

    # Determine available roles
    available_roles = []
    current_role_display = ""

    if status == "viewer":
        available_roles = ["trader", "admin"]
        current_role_display = "👁️ Viewer"
    elif status == "trader":
        available_roles = ["admin"]
        current_role_display = "📊 Trader"
    else:
        await query.edit_message_text("⛔ No puedes solicitar cambio de rol con tu estado actual.")
        return

    # Build keyboard
    keyboard = build_role_change_keyboard(available_roles)

    await query.edit_message_text(
        f"🔄 *Solicitud de Cambio de Rol*\n\n"
        f"Rol actual: {current_role_display}\n\n"
        f"Selecciona el rol que deseas solicitar:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
