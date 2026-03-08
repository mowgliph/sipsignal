"""
Funciones para gestionar usuarios en la base de datos.
"""

from datetime import datetime

from bot.core.database import execute, fetch, fetchrow


async def create_user(user_id: int, language: str = "es") -> dict:
    """Crea un nuevo usuario en la base de datos."""
    now = datetime.now()
    await execute(
        """
        INSERT INTO users (user_id, language, registered_at, last_seen, is_active)
        VALUES ($1, $2, $3, $3, TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        user_id,
        language,
        now,
    )
    return await get_user(user_id)


async def get_user(user_id: int) -> dict | None:
    """Obtiene un usuario por su ID."""
    return await fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def user_exists(user_id: int) -> bool:
    """Verifica si un usuario existe en la base de datos."""
    user = await fetchrow("SELECT 1 FROM users WHERE user_id = $1", user_id)
    return user is not None


async def update_last_seen(user_id: int) -> None:
    """Actualiza el campo last_seen del usuario."""
    await execute(
        "UPDATE users SET last_seen = $1, is_active = TRUE WHERE user_id = $2",
        datetime.now(),
        user_id,
    )


async def register_or_update_user(user_id: int, language: str = "es") -> dict:
    """
    Registra un nuevo usuario o actualiza last_seen si ya existe.
    Retorna los datos del usuario.
    """
    existing = await get_user(user_id)
    if existing:
        await update_last_seen(user_id)
        return await get_user(user_id)
    else:
        return await create_user(user_id, language)


async def get_all_users() -> list:
    """Obtiene todos los usuarios."""
    return await fetch("SELECT * FROM users ORDER BY registered_at DESC")


async def get_active_users() -> list:
    """Obtiene todos los usuarios activos."""
    return await fetch("SELECT * FROM users WHERE is_active = TRUE ORDER BY last_seen DESC")


# =============================================================================
# Access Control Functions
# =============================================================================


async def get_user_status(user_id: int) -> str | None:
    """
    Get user's access status.

    Args:
        user_id: The Telegram user ID.

    Returns:
        The user's status string (e.g., 'non_permitted', 'pending', 'approved', 'admin')
        or None if user not found.
    """
    user = await fetchrow("SELECT status FROM users WHERE user_id = $1", user_id)
    return user["status"] if user else None


async def request_access(user_id: int) -> bool:
    """
    Mark user as pending and set requested_at timestamp.

    Args:
        user_id: The Telegram user ID.

    Returns:
        True if successful, False if user not found.
    """
    now = datetime.now()
    result = await execute(
        """
        UPDATE users
        SET status = 'pending', requested_at = $2
        WHERE user_id = $1
        """,
        user_id,
        now,
    )
    # Parse "UPDATE X" to get row count
    return result.startswith("UPDATE") and int(result.split()[-1]) > 0


async def approve_user(user_id: int) -> bool:
    """
    Change user status to 'approved'.

    Args:
        user_id: The Telegram user ID.

    Returns:
        True if successful, False if user not found.
    """
    result = await execute(
        """
        UPDATE users
        SET status = 'approved'
        WHERE user_id = $1
        """,
        user_id,
    )
    # Parse "UPDATE X" to get row count
    return result.startswith("UPDATE") and int(result.split()[-1]) > 0


async def deny_user(user_id: int) -> bool:
    """
    Change user status back to 'non_permitted'.

    Args:
        user_id: The Telegram user ID.

    Returns:
        True if successful, False if user not found.
    """
    result = await execute(
        """
        UPDATE users
        SET status = 'non_permitted', requested_at = NULL
        WHERE user_id = $1
        """,
        user_id,
    )
    # Parse "UPDATE X" to get row count
    return result.startswith("UPDATE") and int(result.split()[-1]) > 0


async def make_admin(user_id: int) -> bool:
    """
    Change user status to 'admin'.

    Args:
        user_id: The Telegram user ID.

    Returns:
        True if successful, False if user not found.
    """
    result = await execute(
        """
        UPDATE users
        SET status = 'admin'
        WHERE user_id = $1
        """,
        user_id,
    )
    # Parse "UPDATE X" to get row count
    return result.startswith("UPDATE") and int(result.split()[-1]) > 0


async def list_users(status_filter: str | None = None) -> list[dict]:
    """
    List users with optional status filter.

    Args:
        status_filter: Optional status to filter by ('pending', 'approved', 'admin', 'non_permitted').

    Returns:
        List of user dictionaries.
    """
    if status_filter:
        return await fetch(
            "SELECT * FROM users WHERE status = $1 ORDER BY registered_at DESC", status_filter
        )
    return await fetch("SELECT * FROM users ORDER BY registered_at DESC")


async def get_pending_users() -> list[dict]:
    """
    Get all pending users waiting for approval.

    Returns:
        List of pending user dictionaries.
    """
    return await fetch(
        """
        SELECT * FROM users
        WHERE status = 'pending'
        ORDER BY requested_at DESC
        """
    )


async def is_admin(chat_id: int) -> bool:
    """
    Check if user has admin status.

    Args:
        chat_id: The Telegram user ID.

    Returns:
        True if user is an admin, False otherwise.
    """
    user = await fetchrow("SELECT status FROM users WHERE user_id = $1", chat_id)
    return user is not None and user["status"] == "admin"
