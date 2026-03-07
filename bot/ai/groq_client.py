"""
Cliente Groq para análisis de señales.
"""

import os

from groq import AsyncGroq
from loguru import logger

from bot.ai.prompts import build_signal_prompt
from bot.trading.strategy_engine import SignalDTO


class GroqClient:
    """Cliente async para análisis de señales con Groq."""

    MODEL = "llama3-70b-8192"
    MAX_TOKENS = 150
    TEMPERATURE = 0.3

    def __init__(self, api_key: str | None = None):
        self._client: AsyncGroq | None = None
        self._api_key = api_key or os.getenv("GROQ_API_KEY")

    @property
    def client(self) -> AsyncGroq:
        if self._client is None:
            if not self._api_key:
                raise ValueError("GROQ_API_KEY not configured")
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    async def analyze_signal(self, signal: SignalDTO) -> str:
        """
        Analiza una señal usando Groq.

        Args:
            signal: SignalDTO con los datos de la señal

        Returns:
            Análisis en español (2-3 oraciones) o string vacío si falla
        """
        if not self._api_key:
            logger.warning("GROQ_API_KEY not configured, skipping analysis")
            return ""

        prompt = build_signal_prompt(signal)

        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente de análisis de trading. Responde de forma concisa.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning(f"Groq analysis failed: {e}")
            return ""
