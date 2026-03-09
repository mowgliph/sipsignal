"""
Decorators for access control in command handlers.

This module provides decorators to restrict access to specific commands
based on user status in the database.

Example usage:
    @admin_only
    async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Admin-only command executed")

    @permitted_only
    async def protected_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Protected command executed")
"""

import asyncio
import contextlib
import functools
from collections.abc import Callable
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.users import get_user
from bot.utils.logger import logger


def admin_only(func: Callable) -> Callable:
    """
    Decorator to restrict command access to admin users only.

    This decorator wraps async command handler functions and checks if the
    user has admin status before allowing execution. If the user is not
    an admin, an "Access denied" message is sent and the handler returns early.

    Args:
        func: The async command handler function to wrap.
              Must accept (update: Update, context: ContextTypes.DEFAULT_TYPE)

    Returns:
        The wrapped function with access control logic.

    Example:
        @admin_only
        async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            await update.message.reply_text(f"Showing logs for admin {chat_id}")
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
    ) -> Any:
        chat_id = update.effective_chat.id

        try:
            # Fetch user from database
            user = await get_user(chat_id)

            # Check if user exists and has admin status
            if not user or user.get("status") != "admin":
                await update.message.reply_text(
                    "⛔ Acceso denegado. No tienes permisos para usar este comando."
                )
                return None

            # User is admin, execute the wrapped function
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in admin_only decorator for chat {chat_id}: {e}")
            # Don't crash - allow the handler to potentially handle the error
            # or fail gracefully
            with contextlib.suppress(Exception):
                await update.message.reply_text("⚠️ Error al verificar permisos.")
            return None

    return wrapper


def permitted_only(func: Callable) -> Callable:
    """
    Decorator to restrict command access to approved and admin users.

    This decorator wraps async command handler functions and checks if the
    user has either 'approved' or 'admin' status before allowing execution.
    If the user is not permitted, an "Access denied" message is sent and
    the handler returns early.

    Args:
        func: The async command handler function to wrap.
              Must accept (update: Update, context: ContextTypes.DEFAULT_TYPE)

    Returns:
        The wrapped function with access control logic.

    Example:
        @permitted_only
        async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            await update.message.reply_text(f"Generating signal for user {chat_id}")
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
    ) -> Any:
        chat_id = update.effective_chat.id

        try:
            # Fetch user from database
            user = await get_user(chat_id)

            # Check if user exists and has permitted status (approved or admin)
            if not user or user.get("status") not in ("approved", "admin"):
                await update.message.reply_text(
                    "⛔ Acceso denegado. Necesitas aprobación para usar este comando."
                )
                return None

            # User is permitted, execute the wrapped function
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in permitted_only decorator for chat {chat_id}: {e}")
            # Don't crash - allow the handler to potentially handle the error
            # or fail gracefully
            with contextlib.suppress(Exception):
                await update.message.reply_text("⚠️ Error al verificar permisos.")
            return None

    return wrapper


def handle_errors(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    fallback_value: Any = None,
    alert_admin: bool = False,
    level: str = "ERROR",
) -> Callable:
    """
    Decorator to catch specific exceptions, log them, and optionally alert the admin.

    Args:
        exceptions: Tuple of exception types to catch.
        fallback_value: Value to return if an exception occurs.
        alert_admin: Whether to send a notification to the bot admin.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        The wrapped function with error handling logic.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except exceptions as e:
                log_msg = f"Error in {func.__name__}: {str(e)}"
                log_level = level.upper()

                if log_level == "ERROR":
                    logger.error(log_msg)
                elif log_level == "WARNING":
                    logger.warning(log_msg)
                elif log_level == "INFO":
                    logger.info(log_msg)
                elif log_level == "CRITICAL":
                    logger.critical(log_msg)
                else:
                    logger.debug(log_msg)

                if alert_admin:
                    # TODO: Implement alert_admin in Task 2
                    pass

                return fallback_value

        return wrapper

    return decorator
