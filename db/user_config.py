"""
Funciones para gestionar la configuración de usuario en la base de datos.
"""

from datetime import datetime
from decimal import Decimal

from core.database import execute, fetch, fetchrow


async def get_user_config(user_id: int) -> dict | None:
    """Obtiene la configuración de un usuario."""
    return await fetchrow("SELECT * FROM user_config WHERE user_id = $1", user_id)


async def create_or_update_user_config(
    user_id: int,
    capital_total: Decimal,
    risk_percent: Decimal,
    max_drawdown_percent: Decimal,
    direction: str,
    timeframe_primary: str,
    setup_completed: bool = True,
) -> dict:
    """
    Crea o actualiza la configuración de un usuario.
    Usa ON CONFLICT para hacer upsert.
    """
    now = datetime.now()
    await execute(
        """
        INSERT INTO user_config 
        (user_id, capital_total, risk_percent, max_drawdown_percent, direction, timeframe_primary, setup_completed, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (user_id) DO UPDATE SET
            capital_total = EXCLUDED.capital_total,
            risk_percent = EXCLUDED.risk_percent,
            max_drawdown_percent = EXCLUDED.max_drawdown_percent,
            direction = EXCLUDED.direction,
            timeframe_primary = EXCLUDED.timeframe_primary,
            setup_completed = EXCLUDED.setup_completed,
            updated_at = EXCLUDED.updated_at
        """,
        user_id,
        capital_total,
        risk_percent,
        max_drawdown_percent,
        direction,
        timeframe_primary,
        setup_completed,
        now,
    )
    return await get_user_config(user_id)


async def is_setup_completed(user_id: int) -> bool:
    """Verifica si el usuario ha completado el setup."""
    config = await get_user_config(user_id)
    if config:
        return config.get("setup_completed", False)
    return False


async def get_users_with_setup_completed() -> list:
    """Obtiene todos los usuarios que han completado el setup."""
    return await fetch("SELECT user_id FROM user_config WHERE setup_completed = TRUE")
