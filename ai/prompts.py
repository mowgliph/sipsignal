"""
Plantillas de prompts para Groq.
"""

from trading.strategy_engine import SignalDTO


def build_signal_prompt(signal: SignalDTO) -> str:
    """
    Construye prompt para análisis de contexto de mercado.

    Args:
        signal: SignalDTO con los datos de la señal

    Returns:
        Prompt en español para análisis de 2-3 oraciones
    """
    direction_text = "alcista" if signal.direction == "LONG" else "bajista"

    return (
        f"Analiza el contexto de mercado para esta señal {direction_text} en BTC/USDT "
        f"timeframe {signal.timeframe}. "
        f"Dirección: {signal.direction}. "
        f"Precio entrada: ${signal.entry_price:,.2f}. "
        f"Estado Supertrend: {'alcista' if signal.entry_price > signal.supertrend_line else 'bajista'} "
        f"(línea en ${signal.supertrend_line:,.2f}). "
        f"ATR actual: ${signal.atr_value:,.2f}. "
        f"Ratio R:R: {signal.rr_ratio:.2f}. "
        f"Proporciona un análisis de contexto de mercado en 2-3 oraciones en español."
    )
