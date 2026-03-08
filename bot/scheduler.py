"""
Scheduler autónomo de análisis de señales.
"""

import asyncio
import contextlib

from loguru import logger

from bot.container import Container
from bot.core.database import execute
from bot.domain.user_config import UserConfig

CYCLE_INTERVALS = {
    "4h": 900,  # 15 minutos
    "1d": 3600,  # 60 minutos
}

SIGNAL_TIMEOUT = 3600  # 60 minutos para respuesta del trader


class SignalScheduler:
    """Autonomous signal analysis scheduler.

    Runs periodic analysis cycles to detect trading signals
    based on chart analysis and AI interpretation.
    """

    def __init__(self, timeframe: str = "4h"):
        self._running = False
        self._task: asyncio.Task | None = None
        self._config = UserConfig(
            user_id=0,
            chat_id=0,
            timeframe=timeframe,
        )

    async def start(self, bot, config: UserConfig | None = None):
        """Inicia el loop del scheduler."""
        if self._running:
            logger.warning("Scheduler ya está corriendo")
            return

        self._running = True
        if config:
            self._config = config

        timeframe = self._config.timeframe
        interval = CYCLE_INTERVALS.get(timeframe, 900)

        logger.info(f"🔄 SignalScheduler iniciado - timeframe: {timeframe}, intervalo: {interval}s")

        self._task = asyncio.create_task(self._run_loop(bot, interval))

    async def _run_loop(self, bot, interval):
        """Internal loop that can be tracked as a task."""
        while self._running:
            try:
                container: Container = bot.bot_data.get("container")
                if container is None:
                    logger.error("Container not found in bot_data")
                    await asyncio.sleep(interval)
                    continue

                signal = await container.run_signal_cycle.execute(self._config)

                if signal:
                    logger.info(f"📡 Señal detectada: {signal.direction} en {signal.timeframe}")

                    chart_capture = container.run_signal_cycle._chart
                    chart_bytes = await chart_capture.capture("BTCUSDT", self._config.timeframe)

                    ai_context = ""
                    try:
                        ai_client = container.run_signal_cycle._ai
                        ai_context = await ai_client.analyze_signal(signal)
                    except Exception as e:
                        logger.warning(f"AI analysis failed: {e}")

                    text, keyboard = await self._build_signal_message(
                        signal, ai_context, chart_bytes
                    )

                    admin_id = (
                        container.run_signal_cycle._admin_chat_ids[0]
                        if container.run_signal_cycle._admin_chat_ids
                        else None
                    )
                    if not admin_id:
                        logger.warning("No admin configured - seal descartada")
                    elif chart_bytes:
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=chart_bytes,
                            caption=text,
                            reply_markup=keyboard,
                        )
                    else:
                        await bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
                    logger.info(f"✅ Seal enviada al admin {admin_id}")

                    signal_id = await self._save_signal(signal)
                    if signal_id:
                        signal.id = signal_id

                    asyncio.create_task(self._signal_timeout(signal, bot))

                else:
                    logger.debug("No se detect seal en este ciclo")

            except Exception as e:
                logger.error(f"Error en ciclo de scheduler: {e}")

            await asyncio.sleep(interval)

        logger.info("🛑 SignalScheduler detenido")

    async def _build_signal_message(self, signal, ai_context: str, chart_bytes: bytes | None):
        """Build signal message text and keyboard."""
        from bot.trading.signal_builder import build_signal_message

        return await build_signal_message(signal, self._config, ai_context, chart_bytes)

    async def _save_signal(self, signal) -> int | None:
        """Guarda la señal en la base de datos."""
        try:
            detected_at = signal.detected_at
            if detected_at is None:
                logger.warning("signal.detected_at is None - skipping DB insert")
                return None

            query = """
                INSERT INTO signals
                (direction, entry_price, tp1_level, sl_level, rr_ratio, atr_value, timeframe, status, detected_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                RETURNING id
            """
            signal_id = await execute(
                query,
                signal.direction,
                signal.entry_price,
                signal.tp1_level,
                signal.sl_level,
                signal.rr_ratio,
                signal.atr_value,
                signal.timeframe,
                "EMITIDA",
                detected_at,
            )
            logger.info(f"💾 Señal guardada en DB con ID: {signal_id}")
            return signal_id
        except Exception as e:
            logger.error(f"Error guardando señal en DB: {e}")
            return None

    async def _signal_timeout(self, signal, bot):
        """Timeout de 60 min para respuesta del trader."""
        await asyncio.sleep(SIGNAL_TIMEOUT)
        logger.info(f"⏰ Timeout alcanzado para señal {signal.direction} {signal.detected_at}")

    async def stop(self):
        """Detiene el scheduler limpiamente."""
        if not self._running:
            logger.warning("Scheduler no está corriendo")
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("🛑 SignalScheduler solicitado stop")
