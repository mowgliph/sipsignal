# handlers/chart_handler.py

from datetime import UTC, datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes

from bot.trading.chart_capture import ChartCapture
from bot.utils import admin_only
from bot.utils.logger import logger

VALID_TIMEFRAMES = ["1d", "4h", "1h", "15m", "30m"]
DEFAULT_TIMEFRAME = "4h"
DEFAULT_SYMBOL = "BTCUSDT"


def parse_bool(value: str) -> bool:
    """Parse T/F or True/False string to boolean (case-insensitive)."""
    value = str(value).upper()
    return value == "T" or value == "TRUE"


def build_chart_keyboard(
    symbol: str,
    timeframe: str,
    show_ema: bool = False,
    show_bb: bool = False,
    show_rsi: bool = False,
    show_pivots: bool = False,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for chart interaction."""
    keyboard = []

    # Row 1: Timeframes
    tf_buttons = [
        InlineKeyboardButton(
            f"{'✅ ' if tf == timeframe else ''}{tf.upper()}",
            callback_data=f"chart_tf|{symbol}|{tf}|{show_ema}|{show_bb}|{show_rsi}|{show_pivots}",
        )
        for tf in ["1d", "4h", "1h", "15m", "30m"]
    ]
    keyboard.append(tf_buttons)

    # Row 2: Indicators
    ind_buttons = [
        InlineKeyboardButton(
            f"{'✅ ' if show_ema else ''}📈 EMA",
            callback_data=f"chart_ind|{symbol}|{timeframe}|ema|{not show_ema}",
        ),
        InlineKeyboardButton(
            f"{'✅ ' if show_bb else ''}📊 BB",
            callback_data=f"chart_ind|{symbol}|{timeframe}|bb|{not show_bb}",
        ),
        InlineKeyboardButton(
            f"{'✅ ' if show_rsi else ''}📉 RSI",
            callback_data=f"chart_ind|{symbol}|{timeframe}|rsi|{not show_rsi}",
        ),
        InlineKeyboardButton(
            f"{'✅ ' if show_pivots else ''}🎯 Pivots",
            callback_data=f"chart_ind|{symbol}|{timeframe}|pivots|{not show_pivots}",
        ),
    ]
    keyboard.append(ind_buttons)

    # Row 3: Refresh
    keyboard.append(
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data=f"chart_refresh|{symbol}|{timeframe}|{show_ema}|{show_bb}|{show_rsi}|{show_pivots}",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


@admin_only
async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura y envía el gráfico con botones interactivos."""

    args = context.args
    symbol = DEFAULT_SYMBOL
    timeframe = DEFAULT_TIMEFRAME

    # Parse arguments
    for arg in args:
        arg_lower = arg.lower()
        arg_upper = arg.upper()
        if arg_lower in VALID_TIMEFRAMES:
            timeframe = arg_lower
        elif arg_upper.endswith("USDT") or arg_upper.endswith("BTC"):
            symbol = arg_upper
        else:
            await update.message.reply_text(
                f"⚠️ *Argumento inválido: `{arg}`*\n"
                f"Timeframes válidos: `{', '.join(VALID_TIMEFRAMES)}`\n"
                f"Ejemplo: `/chart ETHUSDT 1h`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

    msg = await update.message.reply_text(
        f"⏳ *Generando gráfico {symbol} {timeframe.upper()}...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture(
            symbol,
            timeframe,
            show_ema=False,  # Default: no indicators
            show_bb=False,
            show_rsi=False,
            show_pivots=False,
        )
        await chart_capture.close()

        now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        if chart_bytes:
            # Build keyboard with default state
            keyboard = build_chart_keyboard(
                symbol,
                timeframe,
                show_ema=False,
                show_bb=False,
                show_rsi=False,
                show_pivots=False,
            )

            await msg.delete()
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 {symbol} {timeframe.upper()} — {now_utc}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
        else:
            await msg.edit_text(
                "⚠️ *Error generando gráfico.*\nIntenta de nuevo en unos segundos.",
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        try:
            await msg.edit_text(f"⚠️ *Error:*\n_{str(e)}_", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await msg.edit_text(f"⚠️ Error: {str(e)}")


async def chart_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from chart buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("|")
    action = parts[0]

    try:
        if action == "chart_tf":
            # Change timeframe: chart_tf|symbol|tf|ema|bb|rsi|pivots
            _, symbol, new_tf, ema, bb, rsi, pivots = parts
            await handle_timeframe_change(
                update,
                context,
                symbol,
                new_tf,
                parse_bool(ema),
                parse_bool(bb),
                parse_bool(rsi),
                parse_bool(pivots),
            )

        elif action == "chart_ind":
            # Toggle indicator: chart_ind|symbol|tf|indicator|new_state
            _, symbol, tf, indicator, new_state = parts
            await handle_indicator_toggle(
                update, context, symbol, tf, indicator, parse_bool(new_state)
            )

        elif action == "chart_refresh":
            # Refresh: chart_refresh|symbol|tf|ema|bb|rsi|pivots
            _, symbol, tf, ema, bb, rsi, pivots = parts
            await handle_refresh(
                update,
                context,
                symbol,
                tf,
                parse_bool(ema),
                parse_bool(bb),
                parse_bool(rsi),
                parse_bool(pivots),
            )

    except Exception as e:
        logger.warning(f"Error en callback de chart: {e}")
        await query.answer("⚠️ Error actualizando gráfico", show_alert=True)


async def handle_timeframe_change(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    new_timeframe: str,
    show_ema: bool,
    show_bb: bool,
    show_rsi: bool,
    show_pivots: bool,
):
    """Handle timeframe change button click."""
    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture(
            symbol,
            new_timeframe,
            show_ema=show_ema,
            show_bb=show_bb,
            show_rsi=show_rsi,
            show_pivots=show_pivots,
        )
        await chart_capture.close()

        if chart_bytes:
            now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

            # Build new keyboard with updated timeframe
            keyboard = build_chart_keyboard(
                symbol,
                new_timeframe,
                show_ema=show_ema,
                show_bb=show_bb,
                show_rsi=show_rsi,
                show_pivots=show_pivots,
            )

            # Edit message with new photo and keyboard
            from telegram import InputMediaPhoto

            media = InputMediaPhoto(
                media=chart_bytes,
                caption=f"📊 {symbol} {new_timeframe.upper()} — {now_utc}",
                parse_mode=ParseMode.MARKDOWN,
            )

            try:
                await update.callback_query.edit_message_media(
                    media=media,
                    reply_markup=keyboard,
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.debug("Message unchanged, skipping")
                    return
                raise

    except Exception as e:
        logger.warning(f"Error cambiando timeframe: {e}")
        raise


async def handle_indicator_toggle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    timeframe: str,
    indicator: str,
    new_state: bool,
):
    """Handle indicator toggle button click."""
    # Build indicator kwargs
    kwargs = {
        "show_ema": False,
        "show_bb": False,
        "show_rsi": False,
        "show_pivots": False,
    }

    # Set the toggled indicator
    if indicator == "ema":
        kwargs["show_ema"] = new_state
    elif indicator == "bb":
        kwargs["show_bb"] = new_state
    elif indicator == "rsi":
        kwargs["show_rsi"] = new_state
    elif indicator == "pivots":
        kwargs["show_pivots"] = new_state

    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture(symbol, timeframe, **kwargs)
        await chart_capture.close()

        if chart_bytes:
            now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

            # Build new keyboard with updated indicator state
            keyboard = build_chart_keyboard(symbol, timeframe, **kwargs)

            from telegram import InputMediaPhoto

            media = InputMediaPhoto(
                media=chart_bytes,
                caption=f"📊 {symbol} {timeframe.upper()} — {now_utc}",
                parse_mode=ParseMode.MARKDOWN,
            )

            try:
                await update.callback_query.edit_message_media(
                    media=media,
                    reply_markup=keyboard,
                )
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.debug("Message unchanged, skipping")
                    return
                raise

    except Exception as e:
        logger.warning(f"Error toggling indicator: {e}")
        raise


async def handle_refresh(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    timeframe: str,
    show_ema: bool,
    show_bb: bool,
    show_rsi: bool,
    show_pivots: bool,
):
    """Handle refresh button click."""
    # This is essentially the same as timeframe change but same TF
    await handle_timeframe_change(
        update,
        context,
        symbol,
        timeframe,
        show_ema,
        show_bb,
        show_rsi,
        show_pivots,
    )


chart_handlers_list = [
    CommandHandler("chart", chart_command),
]
