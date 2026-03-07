"""
Módulo de gestión de drawdown para el sistema de trading.

Maneja el tracking del drawdown, avisos al 50% del máximo,
y pausa automática cuando se alcanza el límite de drawdown.
"""

from datetime import UTC, datetime
from typing import Any

from core.config import ADMIN_CHAT_IDS
from core.database import execute, fetchrow
from utils.logger import logger


async def get_or_create_drawdown(user_id: int) -> dict[str, Any]:
    """
    Obtiene el drawdown del usuario o lo crea si no existe.

    Args:
        user_id: ID del usuario

    Returns:
        Dict con el estado actual del drawdown
    """
    # Intentar obtener drawdown existente
    dd = await fetchrow("SELECT * FROM drawdown_tracker WHERE user_id = $1", user_id)

    if dd:
        return dd

    # Crear nuevo drawdown
    await execute(
        """
        INSERT INTO drawdown_tracker
        (user_id, current_drawdown_usdt, current_drawdown_percent, losses_count, is_paused, updated_at)
        VALUES ($1, 0.00, 0.000, 0, false, NOW())
        """,
        user_id,
    )

    return await fetchrow("SELECT * FROM drawdown_tracker WHERE user_id = $1", user_id)


async def get_drawdown(user_id: int) -> dict[str, Any] | None:
    """
    Obtiene el estado actual del drawdown de un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Dict con el estado del drawdown o None si no existe
    """
    # Join con user_config para obtener capital y max_drawdown
    result = await fetchrow(
        """
        SELECT
            dt.user_id,
            dt.current_drawdown_usdt,
            dt.current_drawdown_percent,
            dt.losses_count,
            dt.is_paused,
            dt.last_reset_at,
            dt.updated_at,
            uc.capital_total,
            uc.max_drawdown_percent
        FROM drawdown_tracker dt
        LEFT JOIN user_config uc ON dt.user_id = uc.user_id
        WHERE dt.user_id = $1
        """,
        user_id,
    )

    return result


async def update_drawdown(user_id: int, pnl_usdt: float, bot) -> dict[str, Any]:
    """
    Actualiza el drawdown del usuario con el PnL dado.

    Args:
        user_id: ID del usuario
        pnl_usdt: PnL en USDT (positivo = ganancia, negativo = pérdida)
        bot: Instancia del bot para enviar notificaciones

    Returns:
        Dict con el estado actualizado del drawdown
    """
    # 1. Obtener configuración del usuario
    user_config = await fetchrow(
        "SELECT capital_total, max_drawdown_percent FROM user_config WHERE user_id = $1", user_id
    )

    if not user_config:
        logger.warning(f"No hay configuración para usuario {user_id}")
        return {"error": "No user config"}

    capital_total = float(user_config["capital_total"])
    max_drawdown_percent = float(user_config["max_drawdown_percent"])
    capital_total * (max_drawdown_percent / 100)

    # 2. Obtener o crear drawdown actual
    dd = await get_or_create_drawdown(user_id)

    # 3. Calcular nuevo drawdown
    current_drawdown_usdt = float(dd["current_drawdown_usdt"]) + pnl_usdt
    current_drawdown_percent = (
        (current_drawdown_usdt / capital_total * 100) if capital_total > 0 else 0
    )

    # 4. Determinar si es pérdida
    is_loss = pnl_usdt < 0
    losses_count = int(dd["losses_count"])
    if is_loss:
        losses_count += 1

    # 5. Verificar umbrales
    abs_percent = abs(current_drawdown_percent)
    warning_triggered = abs_percent >= (max_drawdown_percent * 0.5)
    pause_triggered = abs_percent >= max_drawdown_percent

    # 6. Actualizar base de datos
    await execute(
        """
        UPDATE drawdown_tracker
        SET current_drawdown_usdt = $1,
            current_drawdown_percent = $2,
            losses_count = $3,
            is_paused = $4,
            updated_at = NOW()
        WHERE user_id = $5
        """,
        current_drawdown_usdt,
        current_drawdown_percent,
        losses_count,
        pause_triggered,
        user_id,
    )

    # 7. Enviar notificaciones
    if warning_triggered and not pause_triggered:
        # Warning al 50%
        warning_msg = (
            f"⚠️ *Drawdown Warning*\n\n"
            f"Tu drawdown actual es de {current_drawdown_percent:.1f}%\n"
            f"({abs(current_drawdown_usdt):.2f} USDT)\n\n"
            f"Has alcanzado el 50% del límite máximo ({max_drawdown_percent}%).\n"
            f"Revisa tu gestión de riesgo."
        )
        try:
            await bot.send_message(chat_id=user_id, text=warning_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error enviando warning de drawdown: {e}")

    if pause_triggered:
        # Pausa al 100%
        pause_msg = (
            f"🚨 *SISTEMA PAUSADO*\n\n"
            f"Drawdown máximo alcanzado: {current_drawdown_percent:.1f}%\n"
            f"({abs(current_drawdown_usdt):.2f} USDT)\n\n"
            f"Las señales están suspendidas.\n"
            f"Usa /resume cuando estés listo para continuar."
        )
        try:
            await bot.send_message(chat_id=user_id, text=pause_msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error enviando mensaje de pausa: {e}")

        # Notificar a admins
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 Sistema pausado para usuario {user_id} por drawdown máximo ({current_drawdown_percent:.1f}%)",
                )
            except Exception as e:
                logger.error(f"Error notificando a admin: {e}")

    logger.info(
        f"📉 Drawdown actualizado para user {user_id}: {current_drawdown_usdt:.2f} USDT ({current_drawdown_percent:.2f}%)"
    )

    return {
        "user_id": user_id,
        "current_drawdown_usdt": current_drawdown_usdt,
        "current_drawdown_percent": current_drawdown_percent,
        "losses_count": losses_count,
        "is_paused": pause_triggered,
        "warning_sent": warning_triggered,
        "pause_triggered": pause_triggered,
    }


async def reset_drawdown(user_id: int) -> dict[str, Any]:
    """
    Resetea el drawdown a cero.

    Args:
        user_id: ID del usuario

    Returns:
        Dict con el estado del drawdown después del reset
    """
    now = datetime.now(UTC)

    await execute(
        """
        UPDATE drawdown_tracker
        SET current_drawdown_usdt = 0.00,
            current_drawdown_percent = 0.000,
            losses_count = 0,
            is_paused = false,
            last_reset_at = $1,
            updated_at = NOW()
        WHERE user_id = $2
        """,
        now,
        user_id,
    )

    logger.info(f"🔄 Drawdown reseteado para usuario {user_id}")

    return await get_drawdown(user_id)


async def resume_trading(user_id: int) -> dict[str, Any]:
    """
    Reanuda el trading estableciendo is_paused=False.

    Args:
        user_id: ID del usuario

    Returns:
        Dict con el estado del drawdown después de reanudar
    """
    await execute(
        """
        UPDATE drawdown_tracker
        SET is_paused = false,
            updated_at = NOW()
        WHERE user_id = $1
        """,
        user_id,
    )

    logger.info(f"▶️ Trading reanudado para usuario {user_id}")

    return await get_drawdown(user_id)


async def is_trading_paused(user_id: int) -> bool:
    """
    Verifica si el trading está pausado para un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        True si el trading está pausado
    """
    dd = await fetchrow("SELECT is_paused FROM drawdown_tracker WHERE user_id = $1", user_id)

    if not dd:
        return False

    return bool(dd["is_paused"])
