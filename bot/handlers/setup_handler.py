# handlers/setup_handler.py

from decimal import Decimal, InvalidOperation

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.db.user_config import create_or_update_user_config, get_user_config
from bot.db.users import register_or_update_user

# Estados de la conversación
(
    STEP_1_CAPITAL,
    STEP_2_RISK,
    STEP_3_DRAWDOWN,
    STEP_4_DIRECTION,
    STEP_5_TIMEFRAME,
    CONFIRM_SETUP,
) = range(6)


async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el proceso de setup / configuración de capital."""
    user_id = update.effective_user.id

    # Registrar usuario si no existe
    await register_or_update_user(user_id)

    # Verificar si ya tiene configuración
    existing_config = await get_user_config(user_id)

    if existing_config and existing_config.get("setup_completed"):
        # Mostrar config actual y preguntar si quiere actualizar
        capital = existing_config.get("capital_total", 0)
        risk = existing_config.get("risk_percent", 0)
        drawdown = existing_config.get("max_drawdown_percent", 0)
        direction = existing_config.get("direction", "LONG")
        timeframe = existing_config.get("timeframe_primary", "15m")

        msg = (
            f"⚙️ *CONFIGURACIÓN ACTUAL*\\n"
            f"—————————————————\\n\\n"
            f"• *Capital:* `${capital:,.2f}` USDT\\n"
            f"• *Riesgo por operación:* `{risk}%`\\n"
            f"• *Drawdown máximo:* `{drawdown}%`\\n"
            f"• *Dirección:* `{direction}`\\n"
            f"• *Timeframe:* `{timeframe.upper()}`\\n\\n"
            f"—————————————————\\n"
            f"¿Deseas actualizar tu configuración?"
        )

        keyboard = [
            [InlineKeyboardButton("✅ Sí, configurar de nuevo", callback_data="setup_restart")],
            [InlineKeyboardButton("❌ No, mantener actual", callback_data="setup_cancel")],
        ]

        await update.message.reply_text(
            msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
        )
        return CONFIRM_SETUP

    # Si no tiene config, iniciar desde cero
    return await start_setup_flow(update, context)


async def start_setup_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el flujo de setup desde el paso 1."""

    msg = (
        "⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
        "—————————————————\\n\\n"
        "Vamos a configurar tu estrategia de trading. "
        "Responde a cada pregunta para personalizar el sistema a tu perfil de riesgo.\\n\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "📊 *PASO 1 de 5*\\n\\n"
        "¿Cuál es tu *capital total* en USDT?\\n"
        "_Ejemplo: 1000_ (solo el número)"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    return STEP_1_CAPITAL


async def step_1_capital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 1: Pedir el capital total."""
    text = update.message.text.strip().replace(",", ".")

    try:
        capital = Decimal(text)
        if capital <= 0:
            raise ValueError("Capital debe ser positivo")
    except (InvalidOperation, ValueError):
        await update.message.reply_text(
            "⚠️ *Formato inválido.*\\n\\n"
            "Por favor, ingresa solo el número de USDT sin comas ni símbolos.\\n"
            "_Ejemplo: 1000_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return STEP_1_CAPITAL

    # Guardar en context.user_data
    context.user_data["capital_total"] = capital

    # Paso 2: Pedir riesgo por operación
    msg = (
        "⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "📊 *PASO 2 de 5*\\n\\n"
        "¿Qué *% del capital* quieres arriesgar por operación? [1-5]\\n"
        "_Recomendado: 2%_ (default)\\n\\n"
        "Ejemplo: Si tienes $1000 y usas 2%, arriesgas $20 por operación."
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    return STEP_2_RISK


async def step_2_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 2: Pedir el porcentaje de riesgo."""
    text = update.message.text.strip()

    # Si está vacío, usar default
    if not text:
        risk = Decimal("2.00")
    else:
        try:
            risk = Decimal(text)
            if risk < Decimal("0.5") or risk > Decimal("10"):
                await update.message.reply_text(
                    "⚠️ *Valor fuera de rango.*\\n\\n"
                    "El riesgo debe estar entre 0.5% y 10%.\\n"
                    "_Usa un valor como: 2_",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return STEP_2_RISK
        except (InvalidOperation, ValueError):
            await update.message.reply_text(
                "⚠️ *Formato inválido.*\\n\\nIngresa un número entre 0.5 y 10.\\n_Ejemplo: 2_",
                parse_mode=ParseMode.MARKDOWN,
            )
            return STEP_2_RISK

    context.user_data["risk_percent"] = risk

    # Paso 3: Pedir drawdown máximo
    msg = (
        "⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "📊 *PASO 3 de 5*\\n\\n"
        "Drawdown máximo configurado: *8%*\\n"
        "¿Deseas ajustar este valor? [5-15]\\n"
        "_Este es el límite de pérdidas acumulado antes de pausar el trading._\\n\\n"
        "Envía un número (5-15) o presiona el botón para mantener 8%."
    )

    keyboard = [[InlineKeyboardButton("✅ Mantener 8%", callback_data="dd_keep_8")]]

    await update.message.reply_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )
    return STEP_3_DRAWDOWN


async def step_3_drawdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 3: Pedir el drawdown máximo (maneja texto o callback)."""
    # Determinar si viene de callback o mensaje
    if update.callback_query:
        await update.callback_query.answer()
        # El usuario eligió mantener 8% (botón)
        if update.callback_query.data == "dd_keep_8":
            drawdown = Decimal("8.00")
        else:
            # Callback con valor numérico
            try:
                drawdown = Decimal(update.callback_query.data.replace("dd_", ""))
            except (ValueError, IndexError):
                drawdown = Decimal("8.00")
    else:
        # El usuario envió un número
        text = update.message.text.strip()
        if not text:
            drawdown = Decimal("8.00")
        else:
            try:
                drawdown = Decimal(text)
                if drawdown < Decimal("5") or drawdown > Decimal("15"):
                    await update.message.reply_text(
                        "⚠️ *Valor fuera de rango.*\\n\\nEl drawdown debe estar entre 5% y 15%.",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return STEP_3_DRAWDOWN
            except (InvalidOperation, ValueError):
                await update.message.reply_text(
                    "⚠️ *Formato inválido.*\\n\\nIngresa un número entre 5 y 15.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return STEP_3_DRAWDOWN

    context.user_data["max_drawdown_percent"] = drawdown

    # Paso 4: Dirección de trading
    msg = (
        "⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "📊 *PASO 4 de 5*\\n\\n"
        "¿Qué *dirección* de trading prefieres?"
    )

    keyboard = [
        [
            InlineKeyboardButton("🟢 Solo LONG ✅ (Recomendado)", callback_data="dir_LONG"),
            InlineKeyboardButton("🔴 LONG y SHORT", callback_data="dir_AMBOS"),
        ]
    ]

    await update.message.reply_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )
    return STEP_4_DIRECTION


async def step_4_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 4: Seleccionar dirección de trading."""
    query = update.callback_query
    await query.answer()

    # Extraer dirección del callback_data
    direction = query.data.replace("dir_", "")

    if direction == "LONG":
        context.user_data["direction"] = "LONG"
    else:
        context.user_data["direction"] = "AMBOS"

    # Paso 5: Timeframe
    msg = (
        "⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "📊 *PASO 5 de 5*\\n\\n"
        "¿Qué *timeframe* principal prefieres?"
    )

    keyboard = [
        [
            InlineKeyboardButton("📅 Diario (1D)", callback_data="tf_1d"),
            InlineKeyboardButton("⏱️ 4 Horas (4H)", callback_data="tf_4h"),
        ]
    ]

    await query.edit_message_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )
    return STEP_5_TIMEFRAME


async def step_5_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Paso 5: Seleccionar timeframe y mostrar resumen."""
    query = update.callback_query
    await query.answer()

    # Extraer timeframe del callback_data Y GUARDARLO
    timeframe = query.data.replace("tf_", "")
    context.user_data["timeframe"] = timeframe

    # Obtener todos los valores
    capital = context.user_data.get("capital_total", Decimal("1000"))
    risk = context.user_data.get("risk_percent", Decimal("2"))
    drawdown = context.user_data.get("max_drawdown_percent", Decimal("8"))
    direction = context.user_data.get("direction", "LONG")

    # Calcular valores derivados
    risk_amount = (capital * risk) / Decimal("100")
    max_loss = (capital * drawdown) / Decimal("100")

    # Mapeo de timeframe para mostrar
    tf_display = "1D (Diario)" if timeframe == "1d" else "4H (4 Horas)"

    # Construir mensaje de confirmación
    direction_icon = "🟢" if direction == "LONG" else "🔴"
    direction_text = "Solo LONG" if direction == "LONG" else "LONG y SHORT"

    msg = (
        "✅ *RESUMEN DE CONFIGURACIÓN*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        f"💰 *Capital Total:* `${capital:,.2f}` USDT\\n\\n"
        f"⚠️ *Riesgo por operación:* `{risk}%`\\n"
        f"   → *Monto en riesgo:* `${risk_amount:,.2f}` USDT\\n\\n"
        f"📉 *Drawdown máximo:* `{drawdown}%`\\n"
        f"   → *Pérdida máxima:* `${max_loss:,.2f}` USDT\\n\\n"
        f"{direction_icon} *Dirección:* {direction_text}\\n\\n"
        f"⏱️ *Timeframe:* {tf_display}\\n\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n"
        "¿Confirmas esta configuración y activas el sistema?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar y activar", callback_data="setup_confirm"),
            InlineKeyboardButton("🔄 Repetir configuración", callback_data="setup_repeat"),
        ]
    ]

    await query.edit_message_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )
    return CONFIRM_SETUP


async def confirm_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirmar y guardar la configuración."""
    query = update.callback_query
    await query.answer()

    if query.data == "setup_repeat":
        # Reiniciar configuración
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 *Reiniciando configuración...*\\n\\n", parse_mode=ParseMode.MARKDOWN
        )
        return await start_setup_flow(update, context)

    # Obtener valores
    user_id = query.from_user.id
    capital = context.user_data.get("capital_total", Decimal("1000"))
    risk = context.user_data.get("risk_percent", Decimal("2"))
    drawdown = context.user_data.get("max_drawdown_percent", Decimal("8"))
    direction = context.user_data.get("direction", "LONG")
    timeframe = "1d"  # Default, se actualiza en el paso 5
    if context.user_data.get("timeframe"):
        timeframe = context.user_data["timeframe"]

    # Guardar en base de datos
    await create_or_update_user_config(
        user_id=user_id,
        capital_total=capital,
        risk_percent=risk,
        max_drawdown_percent=drawdown,
        direction=direction,
        timeframe_primary=timeframe,
        setup_completed=True,
    )

    # Mensaje de éxito
    success_msg = (
        "🎉 *¡CONFIGURACIÓN COMPLETADA!*\\n"
        "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        "Tu capital y estrategia han sido guardados. "
        "El sistema de señales está ahora *activo* para ti.\\n\\n"
        "📊 *Próximos pasos:*\\n"
        "• Usa `/signal` para ver análisis de BTC\\n"
        "• Usa `/status` para ver el estado del sistema\\n"
        "• Usa `/setup` para cambiar tu configuración\\n\\n"
        "¡Mucho éxito en tus operaciones! 🚀"
    )

    await query.edit_message_text(success_msg, parse_mode=ParseMode.MARKDOWN)

    # Limpiar datos de la conversación
    context.user_data.clear()
    return ConversationHandler.END


async def confirm_setup_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la confirmación cuando viene de un mensaje de texto."""
    # Este caso no debería ocurrir normalmente, pero por seguridad
    return await confirm_setup(update, context)


async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el proceso de setup."""
    if update.message:
        await update.message.reply_text(
            "❌ *Configuración cancelada.*\\n\\n"
            "Tu configuración anterior se mantiene.\\n"
            "Usa `/setup` para configurar cuando quieras.",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif update.callback_query:
        await update.callback_query.answer("Cancelado")
        await update.callback_query.edit_message_text(
            "❌ *Configuración cancelada.*\\n\\nTu configuración anterior se mantiene.",
            parse_mode=ParseMode.MARKDOWN,
        )

    context.user_data.clear()
    return ConversationHandler.END


# Handler de callback para manejo del drawdown (texto libre)
async def drawdown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja los callbacks de drawdown."""
    query = update.callback_query
    await query.answer()

    if query.data == "dd_keep_8":
        # Usuario eligió mantener 8%, avanzar al paso 4
        context.user_data["max_drawdown_percent"] = Decimal("8.00")
        return await step_4_direction(update, context)

    return STEP_3_DRAWDOWN


# Callback para manejar restart desde el estado CONFIRM_SETUP
async def setup_restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el botón de reiniciar configuración."""
    query = update.callback_query
    await query.answer()

    if query.data == "setup_restart":
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 *Reiniciando configuración...*\\n\\n", parse_mode=ParseMode.MARKDOWN
        )
        # Enviar mensaje nuevo para iniciar el flow
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚡ *CONFIGURACIÓN DE CAPITAL*\\n"
            "—————————————————\\n\\n"
            "Vamos a configurar tu estrategia de trading.\\n\\n"
            "━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
            "📊 *PASO 1 de 5*\\n\\n"
            "¿Cuál es tu *capital total* en USDT?\\n"
            "_Ejemplo: 1000_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return STEP_1_CAPITAL
    else:
        # setup_cancel
        await query.edit_message_text(
            "✅ *Ok, configuración mantenida.*\\n\\nUsa `/setup` cuando quieras cambiarla.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END


# Definir el ConversationHandler
setup_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("setup", setup_command)],
    states={
        STEP_1_CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_1_capital)],
        STEP_2_RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_2_risk)],
        STEP_3_DRAWDOWN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, step_3_drawdown),
            CallbackQueryHandler(drawdown_callback, pattern="^dd_"),
        ],
        STEP_4_DIRECTION: [CallbackQueryHandler(step_4_direction, pattern="^dir_")],
        STEP_5_TIMEFRAME: [CallbackQueryHandler(step_5_timeframe, pattern="^tf_")],
        CONFIRM_SETUP: [
            CallbackQueryHandler(confirm_setup, pattern="^setup_(confirm|repeat)$"),
            CallbackQueryHandler(setup_restart_callback, pattern="^setup_(restart|cancel)$"),
        ],
    },
    fallbacks=[CommandHandler("cancelar", cancel_setup)],
    conversation_timeout=300,  # 5 minutos de timeout
)
