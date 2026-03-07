"""
Manejador de respuestas de callbacks para decisiones del trader sobre señales.
"""

import asyncio
import re
from datetime import UTC, datetime, timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes

from core.database import execute, fetch, fetchrow
from utils.logger import logger

# Pattern para extraer signal_id de los callbacks (formato: LONG_1234567890 o SHORT_1234567890)
CALLBACK_PATTERNS = {
    "taken": re.compile(r"^taken:(LONG|SHORT)_(\d+)$"),
    "skipped": re.compile(r"^skipped:(LONG|SHORT)_(\d+)$"),
    "detail": re.compile(r"^detail:(LONG|SHORT)_(\d+)$"),
}

# Bandera global para evitar múltiples instancias del timeout
_timeout_running = False

SIGNAL_TIMEOUT = 60 * 60  # 60 minutos en segundos


async def signal_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja los callbacks de decisiones del trader:
    - taken:{signal_id}: Registrar operación tomada
    - skipped:{signal_id}: Registrar señal como no tomada
    - detail:{signal_id}: Enviar análisis completo
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"🔔 Callback recibido: {data}")

    # Parsear el callback
    taken_match = CALLBACK_PATTERNS["taken"].match(data)
    skipped_match = CALLBACK_PATTERNS["skipped"].match(data)
    detail_match = CALLBACK_PATTERNS["detail"].match(data)

    if taken_match:
        # group(1)=direction, group(2)=timestamp
        timestamp = int(taken_match.group(2))
        await _handle_taken(update, timestamp)
    elif skipped_match:
        timestamp = int(skipped_match.group(2))
        await _handle_skipped(update, timestamp)
    elif detail_match:
        timestamp = int(detail_match.group(2))
        await _handle_detail(update, timestamp)
    else:
        logger.warning(f"⚠️ Callback desconocido: {data}")
        await query.edit_message_text("⚠️ Acción desconocida.")


async def _handle_taken(update: Update, timestamp: int):
    """Maneja el callback de 'tomar señal'."""
    query = update.callback_query

    try:
        # 1. Obtener la señal de la DB por detected_at timestamp
        from datetime import datetime

        detected_dt = datetime.fromtimestamp(timestamp)

        signal = await fetchrow(
            "SELECT * FROM signals WHERE detected_at = $1 AND status = 'EMITIDA' ORDER BY id DESC LIMIT 1",
            detected_dt,
        )

        if not signal:
            await query.edit_message_text("⚠️ Señal no encontrada o ya procesada.")
            return

        signal_id = signal["id"]

        if signal["status"] != "EMITIDA":
            await query.edit_message_text(
                f"⚠️ Esta señal ya fue procesada (status: {signal['status']})"
            )
            return

        # 2. UPDATE signals SET status='TOMADA', taken_at=now() WHERE id={signal_id}
        await execute(
            "UPDATE signals SET status = 'TOMADA', taken_at = NOW(), updated_at = NOW() WHERE id = $1",
            signal_id,
        )

        # 3. INSERT INTO active_trades (signal_id, direction, entry_price, tp1_level, sl_level, status, created_at)
        await execute(
            """
            INSERT INTO active_trades 
            (signal_id, direction, entry_price, tp1_level, sl_level, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, 'ABIERTO', NOW(), NOW())
            """,
            signal_id,
            signal["direction"],
            signal["entry_price"],
            signal["tp1_level"],
            signal["sl_level"],
        )

        # 4. Responder con mensaje de confirmación
        direction = signal["direction"]
        entry = float(signal["entry_price"])
        tp1 = float(signal["tp1_level"])
        sl = float(signal["sl_level"])

        confirmation_text = (
            f"✅ *Operación registrada* \\#{signal_id}\n\n"
            f"🟢 *Dirección:* {direction}\n"
            f"💵 *Entrada:* ${entry:,.2f}\n"
            f"🎯 *TP1:* ${tp1:,.2f}\n"
            f"🛑 *SL:* ${sl:,.2f}\n\n"
            f"📡 *Monitoreando TP1 y Stop\\-Loss en tiempo real...*"
        )

        # 5. Editar mensaje original para eliminar botones
        try:
            await query.edit_message_text(confirmation_text, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.warning(f"No se pudo editar mensaje: {e}")
            await query.message.reply_text(confirmation_text, parse_mode=ParseMode.MARKDOWN_V2)

        logger.info(f"✅ Señal {signal_id} marcada como TOMADA - trade creado")

    except Exception as e:
        logger.error(f"Error en _handle_taken para señal {signal_id}: {e}")
        await query.edit_message_text(f"⚠️ Error al procesar la señal: {str(e)[:100]}")


async def _handle_skipped(update: Update, timestamp: int):
    """Maneja el callback de 'no tomar señal'."""
    query = update.callback_query

    try:
        # 1. Buscar la señal por timestamp
        from datetime import datetime

        detected_dt = datetime.fromtimestamp(timestamp)

        signal = await fetchrow(
            "SELECT * FROM signals WHERE detected_at = $1 AND status = 'EMITIDA' ORDER BY id DESC LIMIT 1",
            detected_dt,
        )

        if not signal:
            await query.edit_message_text("⚠️ Señal no encontrada o ya procesada.")
            return

        signal_id = signal["id"]

        if signal["status"] != "EMITIDA":
            await query.edit_message_text(
                f"⚠️ Esta señal ya fue procesada (status: {signal['status']})"
            )
            return

        # 2. UPDATE signals SET status='NO_TOMADA' WHERE id={signal_id}
        await execute(
            "UPDATE signals SET status = 'NO_TOMADA', updated_at = NOW() WHERE id = $1", signal_id
        )

        # 3. Responder con mensaje de confirmación
        skipped_text = (
            f"❌ *Señal registrada como no tomada* \\#{signal_id}\n\n"
            f"📊 *Dirección:* {signal['direction']}\n"
            f"💵 *Entrada:* ${float(signal['entry_price']):,.2f}\n\n"
            f"⏭️ *Siguiente ciclo en curso...*"
        )

        # 4. Eliminar botones del mensaje original
        try:
            await query.edit_message_text(skipped_text, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.warning(f"No se pudo editar mensaje: {e}")
            await query.message.reply_text(skipped_text, parse_mode=ParseMode.MARKDOWN_V2)

        logger.info(f"❌ Señal {signal_id} marcada como NO_TOMADA")

    except Exception as e:
        logger.error(f"Error en _handle_skipped para señal {signal_id}: {e}")
        await query.edit_message_text(f"⚠️ Error al procesar: {str(e)[:100]}")


async def _handle_detail(update: Update, timestamp: int):
    """Maneja el callback de 'ver detalle de señal'."""
    query = update.callback_query

    try:
        # 1. Recuperar señal de la DB por timestamp
        from datetime import datetime

        detected_dt = datetime.fromtimestamp(timestamp)

        signal = await fetchrow(
            "SELECT * FROM signals WHERE detected_at = $1 ORDER BY id DESC LIMIT 1", detected_dt
        )

        if not signal:
            await query.answer("⚠️ Señal no encontrada", show_alert=True)
            return

        signal_id = signal["id"]

        # 2. Construir mensaje de análisis completo
        direction = signal["direction"]
        entry = float(signal["entry_price"]) if signal["entry_price"] else 0
        tp1 = float(signal["tp1_level"]) if signal["tp1_level"] else 0
        sl = float(signal["sl_level"]) if signal["sl_level"] else 0
        rr = float(signal["rr_ratio"]) if signal["rr_ratio"] else 0
        atr = float(signal["atr_value"]) if signal["atr_value"] else 0
        timeframe = signal["timeframe"]
        ai_context = signal["ai_context"] or "Sin análisis IA disponible."

        detected = (
            signal["detected_at"].strftime("%Y-%m-%d %H:%M:%S") if signal["detected_at"] else "N/A"
        )

        detail_text = (
            f"📊 *Análisis Completo de Señal* \\#{signal_id}\n\n"
            f"*Información General:*\n"
            f"├ 📅 *Detectada:* {detected}\n"
            f"├ ⏱️ *Timeframe:* {timeframe.upper()}\n"
            f"├ 🏷️ *Status:* {signal['status']}\n"
            f"└ 📈 *Dirección:* {direction}\n\n"
            f"*Niveles de Trading:*\n"
            f"├ 💵 *Entrada:* ${entry:,.2f}\n"
            f"├ 🎯 *TP1:* ${tp1:,.2f}\n"
            f"├ 🛑 *SL:* ${sl:,.2f}\n"
            f"├ 📊 *R:R:* 1:{rr:.2f}\n"
            f"└ 📉 *ATR:* ${atr:,.2f}\n\n"
            f"*Contexto IA:*\n"
            f"{ai_context}"
        )

        # 3. Enviar análisis completo (mantener botones originales)
        try:
            await query.edit_message_text(
                detail_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=query.message.reply_markup,  # Mantener botones originales
            )
        except Exception as e:
            logger.warning(f"No se pudo editar mensaje: {e}")
            await query.message.reply_text(
                detail_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=query.message.reply_markup,
            )

        logger.info(f"📊 Detalle enviado para señal {signal_id}")

    except Exception as e:
        logger.error(f"Error en _handle_detail para señal {signal_id}: {e}")
        await query.answer(f"⚠️ Error: {str(e)[:50]}", show_alert=True)


async def process_signal_timeout():
    """
    Tarea asíncrona que actualiza a 'SIN_RESPUESTA' las señales EMITIDAS
    con detected_at < now() - 60 minutos.
    """
    global _timeout_running

    if _timeout_running:
        logger.info("⏰ Signal timeout ya está corriendo, ignorando duplicado")
        return

    _timeout_running = True
    logger.info("⏰ Signal timeout process iniciado")

    while True:
        try:
            # Buscar señales EMITIDAS con más de 60 minutos sin respuesta
            timeout_threshold = datetime.now(UTC) - timedelta(seconds=SIGNAL_TIMEOUT)

            # Obtener señales que necesitan timeout
            expired_signals = await fetch(
                """
                SELECT id, direction, detected_at 
                FROM signals 
                WHERE status = 'EMITIDA' 
                AND detected_at < $1
                """,
                timeout_threshold,
            )

            if expired_signals:
                for signal in expired_signals:
                    await execute(
                        "UPDATE signals SET status = 'SIN_RESPUESTA', updated_at = NOW() WHERE id = $1",
                        signal["id"],
                    )
                    logger.warning(
                        f"⏰ Señal {signal['id']} marcada como SIN_RESPUESTA por timeout"
                    )

            if expired_signals:
                logger.info(
                    f"⏰ Timeout procesado: {len(expired_signals)} señales actualizadas a SIN_RESPUESTA"
                )

        except Exception as e:
            logger.error(f"Error en process_signal_timeout: {e}")

        # Ejecutar cada 5 minutos
        await asyncio.sleep(300)


# Handler para registrar en el bot
signal_response_handler = CallbackQueryHandler(
    signal_response_callback, pattern=r"^(taken:|skipped:|detail:)(LONG|SHORT)_\d+$"
)
