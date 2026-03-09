import os

import httpx

from bot.domain.ports import AIAnalysisPort
from bot.domain.signal import Signal
from bot.utils.decorators import handle_errors


class GroqAdapter(AIAnalysisPort):
    """Async adapter for Groq API using httpx."""

    MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    ENDPOINT = os.getenv("GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions")
    MAX_TOKENS = 150
    TEMPERATURE = 0.3

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    async def analyze_signal(self, signal: Signal) -> str:
        """
        Analyze a trading signal using Groq.

        Args:
            signal: Signal with trading data

        Returns:
            Analysis text or empty string on failure
        """
        direction_text = "alcista" if signal.direction == "LONG" else "bajista"
        supertrend_status = "alcista" if signal.entry_price > signal.supertrend_line else "bajista"

        prompt = (
            f"Analiza el contexto de mercado para esta señal {direction_text} en BTC/USDT "
            f"timeframe {signal.timeframe}. "
            f"Dirección: {signal.direction}. "
            f"Precio entrada: ${signal.entry_price:,.2f}. "
            f"SL: ${signal.sl_level:,.2f}. "
            f"TP1: ${signal.tp1_level:,.2f}. "
            f"Estado Supertrend: {supertrend_status} "
            f"(línea en ${signal.supertrend_line:,.2f}). "
            f"Ratio R:R: {signal.rr_ratio:.2f}. "
            f"Proporciona un análisis de contexto de mercado en 2-3 oraciones en español."
        )

        return await self._call_groq(prompt)

    async def analyze_scenario(self) -> str:
        """
        Analyze BTC scenario with bullish, neutral, and bearish perspectives.

        Returns:
            Scenario analysis or empty string on failure
        """
        prompt = (
            "Proporciona un análisis de escenario para BTC/USDT en tres perspectivas:\n"
            "1. ESCENARIO ALCISTA: ¿Qué necesitaría pasar para confirmar tendencia alcista?\n"
            "2. ESCENARIO NEUTRAL: Condiciones actuales y rangos probables\n"
            "3. ESCENARIO BAJISTA: ¿Qué señales indicarían debilidad?\n"
            "Sé conciso y práctico."
        )

        return await self._call_groq(prompt)

    @handle_errors(fallback_value="", level="WARNING")
    async def _call_groq(self, prompt: str) -> str:
        """Make API call to Groq and return response text."""
        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente de análisis de trading. Responde de forma concisa.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
        }

        response = await self._client.post(self.ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
