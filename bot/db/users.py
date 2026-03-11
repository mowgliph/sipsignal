"""
Funciones para gestionar usuarios en la base de datos.
"""

from datetime import UTC, datetime

from bot.core.database import execute, fetch, fetchrow


async def create_user(user_id: int, language: str = "es") -> dict:
    """Crea un nuevo usuario en la base de datos."""
    now = datetime.now(UTC)
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
        datetime.now(UTC),
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
    now = datetime.now(UTC)
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


async def sync_admins_from_config(admin_chat_ids: list[int]) -> dict:
    """
    Synchronize admin users from configuration to database.

    Ensures that all chat IDs in the admin_chat_ids list are registered
    in the database with 'admin' status. This is typically called on bot
    startup to ensure config-based admins have database admin privileges.

    Args:
        admin_chat_ids: List of Telegram chat IDs that should have admin access.

    Returns:
        Dictionary with synchronization results:
        - synced: Number of admins synced
        - created: Number of new admin users created
        - updated: Number of existing users upgraded to admin
    """
    from datetime import UTC, datetime

    result = {"synced": 0, "created": 0, "updated": 0}

    for admin_id in admin_chat_ids:
        existing_user = await get_user(admin_id)

        if existing_user:
            # User exists, check if already admin
            if existing_user.get("status") != "admin":
                # Upgrade to admin
                await make_admin(admin_id)
                result["updated"] += 1
                result["synced"] += 1
            else:
                # Already admin
                result["synced"] += 1
        else:
            # User doesn't exist, create as admin
            now = datetime.now(UTC)
            await execute(
                """
                INSERT INTO users (user_id, status, language, registered_at, last_seen, is_active)
                VALUES ($1, 'admin', 'es', $2, $2, TRUE)
                """,
                admin_id,
                now,
            )
            result["created"] += 1
            result["synced"] += 1

    return result
