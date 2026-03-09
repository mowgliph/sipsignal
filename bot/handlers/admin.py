"""Admin handlers - backward compatibility module.

This module re-exports all admin handlers from the modular admin package
for backward compatibility with existing imports.

New code should import directly from bot.handlers.admin package.
"""

from bot.handlers.admin import (
    ad_command,
    logs_command,
    ms_conversation_handler,
    set_admin_util,
    set_logs_util,
    users,
)

__all__ = [
    "ad_command",
    "logs_command",
    "ms_conversation_handler",
    "set_admin_util",
    "set_logs_util",
    "users",
]
