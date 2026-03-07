"""
Constructor de mensajes Telegram con botones.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from trading.strategy_engine import SignalDTO, UserConfig


async def build_signal_message(
    signal: SignalDTO, config: UserConfig, ai_context: str, chart_bytes: bytes
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Construye mensaje formateado para Telegram con botones inline.

    Args:
        signal: Señal detecteda con precios de entrada, SL y TP
        config: Configuración del usuario (capital, riesgo, etc.)
        ai_context: Contexto adicional del análisis IA
        chart_bytes: Bytes del gráfico (no usado directamente en el mensaje)

    Returns:
        Tupla con (mensaje_markdown, inline_keyboard)
    """
    entry_price = signal.entry_price
    sl_level = signal.sl_level
    tp1_level = signal.tp1_level
    direction = signal.direction

    signal_icon = "🟢" if direction == "LONG" else "🔴"
    signal_text = f"{signal_icon} *SEÑAL {direction} BTC/USDT*"

    tf = signal.timeframe
    detected_at = signal.detected_at.strftime("%Y-%m-%d %H:%M:%S") if signal.detected_at else "N/A"

    sl_distance = abs(entry_price - sl_level)
    sl_pct = (sl_distance / entry_price) * 100

    tp_distance = abs(tp1_level - entry_price)
    tp_pct = (tp_distance / entry_price) * 100

    rr_ratio = signal.rr_ratio if signal.rr_ratio else tp_pct / sl_pct if sl_pct > 0 else 0

    capital = getattr(config, "capital", 10000)
    risk_pct = getattr(config, "risk_percent", 1.0)
    risk_usdt = capital * (risk_pct / 100)

    if sl_distance > 0:
        position_size = risk_usdt / sl_distance
    else:
        position_size = 0

    signal_id = (
        f"{signal.direction}_{int(signal.detected_at.timestamp()) if signal.detected_at else 0}"
    )

    message = (
        f"{signal_text}\n"
        f"Timeframe: {tf.upper()} | Vela cerrada: ✅\n\n"
        f"💵 *Entrada:* `${entry_price:,.2f}`\n"
        f"🛑 *Stop-Loss (ATR×1.5):* `${sl_level:,.2f}` ({sl_pct:.1f}%)\n"
        f"🎯 *Take Profit 1 (ATR×1.0):* `${tp1_level:,.2f}` (+{tp_pct:.1f}%)\n"
        f"📊 *Ratio R:R:* 1:{rr_ratio:.2f}\n\n"
        f"💼 *Posición sugerida:* {position_size:.5f} BTC\n"
        f"⚠️ *Arriesgas:* `${risk_usdt:.2f}` ({risk_pct}% del capital)\n\n"
        f"🤖 {ai_context}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Tomé la señal", callback_data=f"taken:{signal_id}"),
            InlineKeyboardButton("❌ No la tomé", callback_data=f"skipped:{signal_id}"),
        ],
        [InlineKeyboardButton("📊 Ver análisis completo", callback_data=f"detail:{signal_id}")],
    ]

    return message, InlineKeyboardMarkup(keyboard)
