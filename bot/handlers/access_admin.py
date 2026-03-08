"""
Access control admin command handlers.

This module provides admin commands for managing user access:
- /approve <chat_id> - Approve a user's access request
- /deny <chat_id> - Deny a user's access request
- /make_admin <chat_id> - Make a user an admin
- /list_users [status_filter] - List users with optional status filter

All commands are protected with the @admin_only decorator.
"""

import contextlib
import functools

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.db.users import approve_user, deny_user, get_user, list_users, make_admin
from bot.utils.decorators import admin_only
from bot.utils.rate_limiter import AdminRateLimiter


def rate_limited_admin(func):
    """
    Decorator that applies rate limiting to admin commands.

    Combined with @admin_only decorator.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        limiter = AdminRateLimiter.get_instance()
        if not await limiter.try_acquire():
            # Get update from args
            update = args[0] if args else None
            if update and hasattr(update, "message"):
                await update.message.reply_text(
                    "⏳ Demasiadas solicitudes. Por favor, espera un momento."
                )
            return None
        return await func(*args, **kwargs)

    return wrapper


def format_user_list(users: list[dict], status_filter: str | None = None) -> str:
    """
    Format user list for display.

    Args:
        users: List of user dictionaries from database.
        status_filter: Optional status filter applied.

    Returns:
        Formatted string with user information.
    """
    if not users:
        filter_text = f" (Filtro: {status_filter})" if status_filter else ""
        return f"👥 Usuarios{filter_text}\n\nNo se encontraron usuarios."

    # Group by status if no filter
    if not status_filter:
        grouped: dict[str, list[dict]] = {}
        for user in users:
            status = user.get("status", "unknown")
            if status not in grouped:
                grouped[status] = []
            grouped[status].append(user)

        status_labels = {
            "admin": "🌟 Administradores",
            "approved": "✅ Aprobados",
            "pending": "⏳ Pendientes",
            "non_permitted": "❌ No Permitidos",
        }

        lines = [f"👥 Usuarios (Total: {len(users)})\n"]

        for status in ["admin", "approved", "pending", "non_permitted"]:
            status_users = grouped.get(status, [])
            if status_users:
                label = status_labels.get(status, status)
                lines.append(f"\n[{label}]")
                for user in status_users:
                    chat_id = user.get("user_id", "N/A")
                    username = user.get("username", "N/A")
                    registered_at = user.get("registered_at", "N/A")

                    if registered_at and registered_at != "N/A":
                        try:
                            date_str = registered_at.strftime("%d/%m/%Y")
                        except AttributeError:
                            date_str = str(registered_at).split()[0]
                    else:
                        date_str = "N/A"

                    username_str = (
                        f"@{username}" if username and username != "N/A" else "Sin username"
                    )
                    lines.append(f"• ID: `{chat_id}`, User: {username_str}, Since: {date_str}")

        return "\n".join(lines)

    # Single status view
    status_labels = {
        "admin": "🌟 Administradores",
        "approved": "✅ Aprobados",
        "pending": "⏳ Pendientes",
        "non_permitted": "❌ No Permitidos",
    }

    label = status_labels.get(status_filter, status_filter)
    lines = [f"👥 Usuarios (Total: {len(users)})\n", f"\n[{label}]"]

    for user in users:
        chat_id = user.get("user_id", "N/A")
        username = user.get("username", "N/A")
        registered_at = user.get("registered_at", "N/A")

        if registered_at and registered_at != "N/A":
            try:
                date_str = registered_at.strftime("%d/%m/%Y")
            except AttributeError:
                date_str = str(registered_at).split()[0]
        else:
            date_str = "N/A"

        username_str = f"@{username}" if username and username != "N/A" else "Sin username"
        lines.append(f"• ID: `{chat_id}`, User: {username_str}, Since: {date_str}")

    return "\n".join(lines)


@rate_limited_admin
@admin_only
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Approve a user's access request.

    Usage: /approve <chat_id>

    Args:
        update: The update object.
        context: The context object.
    """
    # Check if argument provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("⚠️ Uso: /approve <chat_id>\n\nEjemplo: /approve 123456789")
        return

    try:
        target_chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El chat_id debe ser un número válido.")
        return

    # Check if user exists
    user = await get_user(target_chat_id)
    if not user:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    # Approve the user
    success = await approve_user(target_chat_id)
    if not success:
        await update.message.reply_text("❌ Error al aprobar el usuario.")
        return

    # Send notification to the approved user
    with contextlib.suppress(Exception):
        await context.bot.send_message(
            chat_id=target_chat_id,
            text="✅ ¡Tu acceso ha sido aprobado! Ahora puedes usar todos los comandos del bot.",
            parse_mode=ParseMode.MARKDOWN,
        )

    # Confirm to admin
    await update.message.reply_text(f"✅ Usuario `{target_chat_id}` aprobado exitosamente.")


@rate_limited_admin
@admin_only
async def deny_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Deny a user's access request.

    Usage: /deny <chat_id>

    Args:
        update: The update object.
        context: The context object.
    """
    # Check if argument provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("⚠️ Uso: /deny <chat_id>\n\nEjemplo: /deny 123456789")
        return

    try:
        target_chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El chat_id debe ser un número válido.")
        return

    # Check if user exists
    user = await get_user(target_chat_id)
    if not user:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    # Deny the user
    success = await deny_user(target_chat_id)
    if not success:
        await update.message.reply_text("❌ Error al denegar el usuario.")
        return

    # Send notification to the denied user
    with contextlib.suppress(Exception):
        await context.bot.send_message(
            chat_id=target_chat_id,
            text="❌ Tu solicitud de acceso ha sido denegada.",
            parse_mode=ParseMode.MARKDOWN,
        )

    # Confirm to admin
    await update.message.reply_text(f"✅ Usuario `{target_chat_id}` denegado.")


@rate_limited_admin
@admin_only
async def make_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Make a user an admin.

    Usage: /make_admin <chat_id>

    Args:
        update: The update object.
        context: The context object.
    """
    # Check if argument provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Uso: /make_admin <chat_id>\n\nEjemplo: /make_admin 123456789"
        )
        return

    try:
        target_chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El chat_id debe ser un número válido.")
        return

    # Prevent self-demotion edge case (though this is make_admin, not demote)
    if target_chat_id == update.effective_chat.id:
        await update.message.reply_text(
            "⚠️ Ya eres administrador. Usa este comando para otros usuarios."
        )
        return

    # Check if user exists
    user = await get_user(target_chat_id)
    if not user:
        await update.message.reply_text("❌ Usuario no encontrado.")
        return

    # Make the user an admin
    success = await make_admin(target_chat_id)
    if not success:
        await update.message.reply_text("❌ Error al hacer administrador al usuario.")
        return

    # Send notification to the new admin
    with contextlib.suppress(Exception):
        await context.bot.send_message(
            chat_id=target_chat_id,
            text="🌟 ¡Ahora eres administrador! Tienes acceso total al bot.",
            parse_mode=ParseMode.MARKDOWN,
        )

    # Confirm to admin
    await update.message.reply_text(f"✅ Usuario `{target_chat_id}` ahora es administrador.")


@admin_only
async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    List users with optional status filter.

    Usage: /list_users [status_filter]
    Status filters: non_permitted, pending, approved, admin

    Args:
        update: The update object.
        context: The context object.
    """
    # Get optional status filter
    status_filter = None
    if context.args and len(context.args) > 0:
        status_filter = context.args[0].lower()

        valid_filters = ["non_permitted", "pending", "approved", "admin"]
        if status_filter not in valid_filters:
            await update.message.reply_text(
                f"⚠️ Filtro inválido. Filtros válidos: {', '.join(valid_filters)}"
            )
            return

    # Fetch users from database
    users = await list_users(status_filter)

    # Format and send the list
    formatted_list = format_user_list(users, status_filter)
    await update.message.reply_text(formatted_list, parse_mode=ParseMode.MARKDOWN)
