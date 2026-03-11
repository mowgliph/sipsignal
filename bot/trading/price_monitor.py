"""
Monitor WebSocket de TP/SL en tiempo real.

Conecta al stream WebSocket de Binance (btcusdt@ticker) y monitorea
los trades activos para notificaciones automáticas de TP1 y SL.
"""

import asyncio
import contextlib
import json
from datetime import UTC, datetime
from typing import Any

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.core.config import ADMIN_CHAT_IDS
from bot.core.database import fetch
from bot.utils.logger import logger

# URLs de WebSocket de Binance
# Binance US endpoint para usuarios en Estados Unidos
BINANCE_WS_URL = "wss://stream.binance.us:9443/ws"
BINANCE_TICKER_STREAM = "btcusdt@ticker"

# Configuración de reconexión
RECONNECT_DELAY = 5  # segundos iniciales
MAX_RECONNECT_DELAY = 60  # segundos máximos
MAX_RECONNECT_ATTEMPTS = 10

# Timeout para operaciones
WS_PING_TIMEOUT = 30


class PriceMonitor:
    """Monitor de precios en tiempo real via WebSocket.

    Monitorea trades activos y envía notificaciones cuando se alcanzan
    niveles de TP1 o SL.
    """

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._ws_session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.WebSocketRunner | None = None
        self._reconnect_attempts = 0
        self._reconnect_delay = RECONNECT_DELAY
        self._current_price: float | None = None
        self._last_ticker_update: datetime | None = None
        self._notified_trades: dict[int, set] = {}  # trade_id -> {tp1_notified, sl_notified}

    async def start(self, bot):
        """Inicia el monitor de precios.

        Args:
            bot: Instancia del bot de Telegram para enviar notificaciones.
        """
        if self._running:
            logger.warning("PriceMonitor ya está corriendo")
            return

        self._running = True
        self._bot = bot
        logger.info("🔄 PriceMonitor iniciado")

        self._task = asyncio.create_task(self._run())

    async def _run(self):
        """Loop principal del monitor."""
        while self._running:
            try:
                await self._connect_websocket()
                await self._listen()
            except asyncio.CancelledError:
                logger.info("🛑 PriceMonitor cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en PriceMonitor: {e}")

                if self._running:
                    await self._handle_reconnect()

        await self._cleanup()
        logger.info("🛑 PriceMonitor detenido")

    async def _connect_websocket(self):
        """Conecta al WebSocket de Binance."""
        ws_url = f"{BINANCE_WS_URL}/{BINANCE_TICKER_STREAM}"

        logger.info(f"🔌 Conectando a WebSocket: {ws_url}")

        self._ws_session = aiohttp.ClientSession()

        try:
            # Note: aiohttp 3.10+ removed 'ping' from ClientTimeout
            # Using heartbeat parameter for WebSocket keepalive instead
            timeout = (
                aiohttp.ClientTimeout(total=None)
                if aiohttp.__version__.startswith("3.1")
                else aiohttp.ClientTimeout(total=None, ping=WS_PING_TIMEOUT)
            )
            self._ws = await self._ws_session.ws_connect(
                ws_url,
                timeout=timeout,
                heartbeat=WS_PING_TIMEOUT,
            )
            self._reconnect_attempts = 0
            self._reconnect_delay = RECONNECT_DELAY
            logger.info("✅ Conectado al WebSocket de Binance")

        except Exception as e:
            logger.error(f"❌ Fallo al conectar WebSocket: {e}")
            await self._cleanup()
            raise

    async def _listen(self):
        """Escucha mensajes del WebSocket."""
        if not self._ws:
            return

        try:
            async for msg in self._ws:
                if not self._running:
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._process_ticker(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ JSON decode error: {e}")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"❌ Error WebSocket: {self._ws.exception()}")
                    break

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("⚠️ WebSocket cerrado por el servidor")
                    break

                elif msg.type == aiohttp.WSMsgType.PING:
                    await self._ws.pong()

        except asyncio.CancelledError:
            logger.info("🛑 Escucha de WebSocket cancelada")
            raise

    async def _process_ticker(self, data: dict[str, Any]):
        """Procesa un tick del ticker de Binance.

        Args:
            data: Datos del ticker de Binance
        """
        # Extraer precio actual
        if "c" not in data:  # 'c' es el precio de cierre en el stream ticker
            return

        current_price = float(data["c"])
        self._current_price = current_price
        self._last_ticker_update = datetime.now(UTC)

        logger.debug(f"📊 BTC/USDT: ${current_price:,.2f}")

        # Verificar trades activos
        await self._check_active_trades(current_price)

    async def _check_active_trades(self, current_price: float):
        """Verifica si algún trade activo ha alcanzado TP o SL.

        Args:
            current_price: Precio actual de BTC/USDT
        """
        try:
            # Obtener trades con status ABIERTO
            trades = await fetch(
                "SELECT id, signal_id, direction, entry_price, tp1_level, sl_level, status "
                "FROM active_trades WHERE status = 'ABIERTO'"
            )

            if not trades:
                return

            logger.debug(f"📈 Verificando {len(trades)} trades activos")

            for trade in trades:
                trade_id = trade["id"]
                direction = trade["direction"]
                entry_price = float(trade["entry_price"])
                tp1_level = float(trade["tp1_level"]) if trade["tp1_level"] else None
                sl_level = float(trade["sl_level"]) if trade["sl_level"] else None

                if not tp1_level or not sl_level:
                    continue

                # Inicializar seguimiento de notificaciones
                if trade_id not in self._notified_trades:
                    self._notified_trades[trade_id] = set()

                notified = self._notified_trades[trade_id]

                # Lógica según dirección
                if direction == "LONG":
                    # TP1: precio reached or exceeded
                    if current_price >= tp1_level and "TP1" not in notified:
                        await self._notify_tp1(trade, entry_price, tp1_level, current_price)
                        notified.add("TP1")

                    # SL: precio fell to or below
                    if current_price <= sl_level and "SL" not in notified:
                        await self._notify_sl(trade, entry_price, sl_level, current_price)
                        notified.add("SL")

                elif direction == "SHORT":
                    # TP1: precio fell to or below
                    if current_price <= tp1_level and "TP1" not in notified:
                        await self._notify_tp1(trade, entry_price, tp1_level, current_price)
                        notified.add("TP1")

                    # SL: precio rose to or above
                    if current_price >= sl_level and "SL" not in notified:
                        await self._notify_sl(trade, entry_price, sl_level, current_price)
                        notified.add("SL")

        except Exception as e:
            logger.error(f"❌ Error al verificar trades activos: {e}")

    async def _notify_tp1(
        self, trade: Any, entry_price: float, tp1_level: float, current_price: float
    ):
        """Envía notificación de TP1 alcanzado.

        Args:
            trade: Registro del trade
            entry_price: Precio de entrada
            tp1_level: Nivel de TP1
            current_price: Precio actual
        """
        trade_id = trade["id"]
        direction = trade["direction"]

        message = (
            f"📈 *¡TP1 alcanzado!*\n\n"
            f"BTC llegó a ${tp1_level:,.2f}\n"
            f"Precio actual: ${current_price:,.2f}\n\n"
            f"👉 Cierra el 50% de tu posición y mueve el SL a ${entry_price:,.2f} (breakeven)."
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ TP1 tomado y SL movido", callback_data=f"pm_tp1_done:{trade_id}"
                    ),
                    InlineKeyboardButton("⏳ Aún no", callback_data=f"pm_tp1_wait:{trade_id}"),
                ]
            ]
        )

        await self._send_notification(message, keyboard)
        logger.info(f"🎯 TP1 alcanzado para trade {trade_id} ({direction})")

    async def _notify_sl(
        self, trade: Any, entry_price: float, sl_level: float, current_price: float
    ):
        """Envía notificación de SL alcanzado.

        Args:
            trade: Registro del trade
            entry_price: Precio de entrada
            sl_level: Nivel de SL
            current_price: Precio actual
        """
        trade_id = trade["id"]
        direction = trade["direction"]

        # Calcular pérdida
        if direction == "LONG":
            loss_usdt = entry_price - sl_level
            loss_pct = (loss_usdt / entry_price) * 100
        else:  # SHORT
            loss_usdt = sl_level - entry_price
            loss_pct = (loss_usdt / entry_price) * 100

        message = (
            f"🛑 *Stop-Loss alcanzado*\n\n"
            f"Nivel SL: ${sl_level:,.2f}\n"
            f"Precio actual: ${current_price:,.2f}\n\n"
            f"📉 *Pérdida:* -{loss_usdt:.2f} USDT ({loss_pct:.1f}% del capital)"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Cerré la posición", callback_data=f"pm_sl_closed:{trade_id}"
                    ),
                    InlineKeyboardButton(
                        "📊 Ver resumen", callback_data=f"pm_sl_summary:{trade_id}"
                    ),
                ]
            ]
        )

        await self._send_notification(message, keyboard)
        logger.info(
            f"🛑 SL alcanzado para trade {trade_id} ({direction}) - Pérdida: {loss_usdt:.2f} USDT"
        )

    async def _send_notification(self, message: str, keyboard: InlineKeyboardMarkup):
        """Envía notificación a los administradores.

        Args:
            message: Mensaje a enviar
            keyboard: Keyboard inline con botones
        """
        if not ADMIN_CHAT_IDS:
            logger.warning("No hay ADMIN_CHAT_IDS configurados")
            return

        for admin_id in ADMIN_CHAT_IDS:
            try:
                await self._bot.send_message(chat_id=admin_id, text=message, reply_markup=keyboard)
                await asyncio.sleep(0.1)  # Evitar flood limits
            except Exception as e:
                logger.error(f"❌ Error al enviar notificación a {admin_id}: {e}")

    async def _handle_reconnect(self):
        """Maneja la reconexión con backoff exponencial."""
        self._reconnect_attempts += 1

        if self._reconnect_attempts > MAX_RECONNECT_ATTEMPTS:
            logger.error(
                f"❌ Máximo de intentos de reconexión alcanzado ({MAX_RECONNECT_ATTEMPTS})"
            )
            self._running = False
            return

        logger.warning(
            f"⚠️ Reconectando en {self._reconnect_delay}s (intento {self._reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})"
        )
        await asyncio.sleep(self._reconnect_delay)

        # Backoff exponencial
        self._reconnect_delay = min(self._reconnect_delay * 2, MAX_RECONNECT_DELAY)

    async def _cleanup(self):
        """Limpia recursos del WebSocket."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.warning(f"⚠️ Error al cerrar WebSocket: {e}")
            self._ws = None

        if self._ws_session:
            try:
                await self._ws_session.close()
            except Exception as e:
                logger.warning(f"⚠️ Error al cerrar sesión: {e}")
            self._ws_session = None

    async def stop(self):
        """Detiene el monitor limpiamente."""
        if not self._running:
            return

        logger.info("🛑 Solicitando stop de PriceMonitor...")
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        await self._cleanup()
        logger.info("🛑 PriceMonitor detenido")

    @property
    def is_running(self) -> bool:
        """Retorna si el monitor está corriendo."""
        return self._running

    @property
    def current_price(self) -> float | None:
        """Retorna el último precio conocido."""
        return self._current_price

    @property
    def last_update(self) -> datetime | None:
        """Retorna la última actualización del ticker."""
        return self._last_ticker_update


# Instancia global del monitor
_price_monitor: PriceMonitor | None = None


def get_price_monitor() -> PriceMonitor:
    """Retorna la instancia global del PriceMonitor."""
    global _price_monitor
    if _price_monitor is None:
        _price_monitor = PriceMonitor()
    return _price_monitor


async def start_price_monitor(bot) -> PriceMonitor:
    """Inicia el PriceMonitor y retorna la instancia.

    Args:
        bot: Instancia del bot de Telegram

    Returns:
        Instancia del PriceMonitor iniciado
    """
    monitor = get_price_monitor()
    await monitor.start(bot)
    return monitor


async def stop_price_monitor():
    """Detiene el PriceMonitor."""
    global _price_monitor
    if _price_monitor:
        await _price_monitor.stop()
        _price_monitor = None
