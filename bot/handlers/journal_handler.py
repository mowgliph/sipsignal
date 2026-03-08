"""
Handler para comandos /journal y /active.
Muestra historial de señales con estadísticas y trades activos.
"""

import contextlib
from datetime import datetime
from typing import Any

from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from bot.core.database import fetch
from bot.domain.signal import Signal
from bot.trading.data_fetcher import BinanceDataFetcher


def signal_to_dict(signal: Signal) -> dict[str, Any]:
    """Convierte un objeto Signal a diccionario para compatibilidad."""
    return {
        "id": signal.id,
        "detected_at": signal.detected_at,
        "direction": signal.direction,
        "entry_price": signal.entry_price,
        "status": signal.status,
        "result": signal.result,
        "pnl_usdt": signal.pnl_usdt,
    }


def get_signal_emoji(result: str | None, status: str) -> str:
    """Retorna el emoji según el resultado o status de la señal."""
    if result == "GANADA":
        return "🏆"
    elif result == "PERDIDA":
        return "📉"
    elif result == "BREAKEVEN":
        return "⚖️"
    elif status == "NO_TOMADA":
        return "⏭️"
    elif status == "SIN_RESPUESTA":
        return "❓"
    elif status == "TOMADA":
        return "⏳"
    else:
        return "❓"


def format_signal_line(signal: dict[str, Any]) -> str:
    """Formatea una línea de señal para el journal."""
    detected_at = signal.get("detected_at")
    if detected_at:
        if isinstance(detected_at, datetime):
            fecha = detected_at.strftime("%d/%m")
        else:
            fecha = str(detected_at)[:10].replace("-", "/")[-5:]
    else:
        fecha = "??/??"

    direction = signal.get("direction", "N/A")
    entry_price = signal.get("entry_price")
    result = signal.get("result", signal.get("status", ""))
    emoji = get_signal_emoji(result, signal.get("status", ""))

    entry_str = f"${entry_price:,.0f}" if entry_price else "—"

    return f"{emoji} {fecha} · {direction} · {entry_str} → {result}"


def calculate_journal_stats(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula estadísticas del journal."""
    if not signals:
        return {
            "total": 0,
            "taken": 0,
            "wins": 0,
            "losses": 0,
            "winrate": 0.0,
            "profit_factor": 0.0,
            "pnl_total": 0.0,
            "best_streak": 0,
            "worst_streak": 0,
        }

    total = len(signals)
    # Count as 'taken' if it has a result OR if status is TOMADA
    taken = sum(1 for s in signals if s.get("result") is not None or s.get("status") == "TOMADA")

    wins = sum(1 for s in signals if s.get("result") == "GANADA")
    losses = sum(1 for s in signals if s.get("result") == "PERDIDA")

    winrate = (wins / taken * 100) if taken > 0 else 0.0

    # Calculate PnL
    pnl_values = []
    for s in signals:
        pnl = s.get("pnl_usdt")
        if pnl is not None:
            with contextlib.suppress(TypeError, ValueError):
                pnl_values.append(float(pnl))

    pnl_total = sum(pnl_values)

    # Profit Factor
    gross_profit = sum(p for p in pnl_values if p > 0)
    gross_loss = abs(sum(p for p in pnl_values if p < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

    # Calculate streaks (only for signals with result)
    results = [s.get("result") for s in signals if s.get("result") in ("GANADA", "PERDIDA")]
    best_streak, worst_streak = calculate_streaks(results)

    return {
        "total": total,
        "taken": taken,
        "wins": wins,
        "losses": losses,
        "winrate": winrate,
        "profit_factor": profit_factor,
        "pnl_total": pnl_total,
        "best_streak": best_streak,
        "worst_streak": worst_streak,
    }


def calculate_streaks(results: list[str]) -> tuple:
    """Calcula mejor racha de wins y peor racha de losses."""
    if not results:
        return 0, 0

    best_streak = 0
    worst_streak = 0
    current_win_streak = 0
    current_loss_streak = 0

    for result in results:
        if result == "GANADA":
            current_win_streak += 1
            current_loss_streak = 0
            if current_win_streak > best_streak:
                best_streak = current_win_streak
        elif result == "PERDIDA":
            current_loss_streak += 1
            current_win_streak = 0
            if current_loss_streak > worst_streak:
                worst_streak = current_loss_streak

    return best_streak, worst_streak


def format_stats_block(stats: dict[str, Any], n: int) -> str:
    """Formatea el bloque de estadísticas."""
    pnl_str = (
        f"${stats['pnl_total']:+.2f}" if stats["pnl_total"] >= 0 else f"${stats['pnl_total']:.2f}"
    )
    return (
        f"📊 *Resumen* (últimas {n}):\n"
        f"Total: {stats['total']} | Tomadas: {stats['taken']} | Winrate: {stats['winrate']:.0f}%\n"
        f"Profit Factor: {stats['profit_factor']:.2f} | PnL total: {pnl_str} USDT\n"
        f"Mejor racha: {stats['best_streak']} wins | Peor racha: {stats['worst_streak']} losses"
    )


async def get_signals_history(container, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
    """Obtiene el historial de señales usando el container."""
    try:
        signals = await container.manage_journal.get_recent(limit=limit + offset)
        signals = signals[offset : offset + limit]
        return [signal_to_dict(s) for s in signals]
    except Exception as e:
        logger.error(f"Error fetching signals history: {e}")
        return []


async def get_active_trades() -> list[dict[str, Any]]:
    """Obtiene los trades activos (status=ABIERTO) de la base de datos."""
    query = """
        SELECT id, signal_id, direction, entry_price, tp1_level, sl_level
        FROM active_trades
        WHERE status = 'ABIERTO'
        ORDER BY created_at DESC
    """
    try:
        rows = await fetch(query)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching active trades: {e}")
        return []


async def format_active_trade(trade: dict[str, Any], current_price: float | None = None) -> str:
    """Formatea un trade activo con precios actuales y distancias."""
    direction = trade.get("direction", "N/A")
    entry_price = float(trade.get("entry_price", 0))

    # Accept current_price as param or inside the dict
    if current_price is None:
        current_price = trade.get("current_price")
    if current_price is None:
        current_price = 0.0

    tp1 = float(trade.get("tp1_level", 0)) if trade.get("tp1_level") else None
    sl = float(trade.get("sl_level", 0)) if trade.get("sl_level") else None

    # Calcular distancias
    if direction == "LONG":
        tp_distance = ((tp1 - entry_price) / entry_price * 100) if tp1 else None
        sl_distance = ((entry_price - sl) / entry_price * 100) if sl else None
    else:  # SHORT
        tp_distance = ((entry_price - tp1) / entry_price * 100) if tp1 else None
        sl_distance = ((sl - entry_price) / entry_price * 100) if sl else None

    line = f"🔄 {direction} | Entrada: ${entry_price:,.0f} | Actual: ${current_price:,.0f}\n"

    if tp1 and tp_distance is not None:
        line += f"   TP: ${tp1:,.0f} (+{tp_distance:.1f}%)"
    if sl and sl_distance is not None:
        line += f" | SL: ${sl:,.0f} (-{sl_distance:.1f}%)"

    return line


async def journal_command(container, limit: int = 10, offset: int = 0) -> str:
    """Genera el mensaje completo del comando /journal."""
    signals = await get_signals_history(container, limit=limit, offset=offset)

    if not signals:
        return "📭 No hay señales en el historial."

    # Formatear líneas de señales
    lines = [format_signal_line(s) for s in signals]

    # Calcular estadísticas
    stats = calculate_journal_stats(signals)

    # Construir mensaje
    message = "📔 *Historial de Señales*\n\n"
    message += "\n".join(lines)
    message += "\n\n" + format_stats_block(stats, limit)

    # Añadir botón de paginación si hay más señales
    if len(signals) == limit:
        new_offset = offset + limit
        # El botón se añade desde el handler principal
        message += f"\n\n[Pagina:{new_offset}]"

    return message


async def active_command() -> str:
    """Genera el mensaje completo del comando /active."""
    trades = await get_active_trades()

    if not trades:
        return "✅ No hay trades activos en este momento."

    # Obtener precio actual de BTC
    try:
        async with BinanceDataFetcher() as fetcher:
            current_price = await fetcher.get_current_price("BTCUSDT")
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
        current_price = None

    message = "📈 *Trades Activos*\n\n"

    for trade in trades:
        price = current_price if current_price else 0
        line = await format_active_trade(trade, price)
        message += line + "\n\n"

    return message


# ============== Telegram Handlers ==============


async def journal_cmd(update: Update, context: CallbackContext) -> None:
    """Maneja el comando /journal."""
    container = context.bot_data["container"]

    # Parsear argumentos: /journal [N]
    limit = 10
    offset = 0

    if context.args:
        try:
            limit = int(context.args[0])
            limit = min(max(limit, 1), 100)
        except ValueError:
            limit = 10

    message = await journal_command(container, limit=limit, offset=offset)

    # Añadir keyboard con paginación si hay más señales
    # Por ahora solo text, el handler de callback se puede añadir después

    await update.message.reply_text(message, parse_mode="Markdown")


async def active_cmd(update: Update, context: CallbackContext) -> None:
    """Maneja el comando /active."""
    message = await active_command()
    await update.message.reply_text(message, parse_mode="Markdown")


def register(application) -> None:
    """Registra los handlers en la aplicación del bot."""
    application.add_handler(CommandHandler("journal", journal_cmd))
    application.add_handler(CommandHandler("active", active_cmd))
