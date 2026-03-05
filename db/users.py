"""
Funciones para gestionar usuarios en la base de datos.
"""
from datetime import datetime
from typing import Optional

from core.database import execute, fetchrow, fetch


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


async def get_user(user_id: int) -> Optional[dict]:
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
