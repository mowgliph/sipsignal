"""
Inline keyboard builders for access control and role management.

This module provides functions to build inline keyboards for:
- Access approval/denial
- Role selection
- Role change requests
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_access_keyboard(user_chat_id: int) -> InlineKeyboardMarkup:
    """
    Build keyboard with Approve/Deny buttons for access requests.

    Args:
        user_chat_id: The chat ID of the user requesting access.

    Returns:
        InlineKeyboardMarkup with approve and deny buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Aprobar",
                callback_data=f"access_approve:{user_chat_id}",
            ),
            InlineKeyboardButton(
                "❌ Rechazar",
                callback_data=f"access_deny:{user_chat_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_role_keyboard(user_chat_id: int) -> InlineKeyboardMarkup:
    """
    Build keyboard with role selection buttons.

    Args:
        user_chat_id: The chat ID of the user to assign role to.

    Returns:
        InlineKeyboardMarkup with role selection buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton("👁️ Viewer", callback_data=f"role_set:{user_chat_id}:viewer"),
            InlineKeyboardButton("📊 Trader", callback_data=f"role_set:{user_chat_id}:trader"),
            InlineKeyboardButton("⭐ Admin", callback_data=f"role_set:{user_chat_id}:admin"),
        ],
        [
            InlineKeyboardButton("❌ Cancelar", callback_data="role_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_role_change_keyboard(available_roles: list[str]) -> InlineKeyboardMarkup:
    """
    Build keyboard for role change request.

    Args:
        available_roles: List of roles the user can request (excludes current role).
                        Valid values: 'trader', 'admin'.

    Returns:
        InlineKeyboardMarkup with role change request buttons.
    """
    buttons = []

    # Map roles to display
    role_display = {
        "viewer": "👁️ Viewer",
        "trader": "📊 Trader",
        "admin": "⭐ Admin",
    }

    # Create buttons for available roles
    row = []
    for role in available_roles:
        if role in role_display:
            row.append(
                InlineKeyboardButton(
                    role_display[role],
                    callback_data=f"role_change_request:{role}",
                )
            )
    if row:
        buttons.append(row)

    # Add cancel button
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="role_change_cancel")])

    return InlineKeyboardMarkup(buttons)


def build_role_change_admin_keyboard(user_chat_id: int, new_role: str) -> InlineKeyboardMarkup:
    """
    Build approve/deny keyboard for admin role change notification.

    Args:
        user_chat_id: The chat ID of the user requesting role change.
        new_role: The role being requested.

    Returns:
        InlineKeyboardMarkup with approve and deny buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Aprobar",
                callback_data=f"role_change_approve:{user_chat_id}:{new_role}",
            ),
            InlineKeyboardButton(
                "❌ Rechazar",
                callback_data=f"role_change_deny:{user_chat_id}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_my_role_keyboard() -> InlineKeyboardMarkup:
    """
    Build keyboard for viewing role info and requesting change.

    Returns:
        InlineKeyboardMarkup with role change button.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Solicitar Cambio de Rol",
                callback_data="my_role_change_request",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
