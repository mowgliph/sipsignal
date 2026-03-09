"""Mass messaging handlers for /ms command."""

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

from bot.core.config import ADMIN_CHAT_IDS
from bot.handlers.admin.utils import _

# Definimos los estados para nuestra conversación de mensaje masivo
AWAITING_CONTENT, AWAITING_CONFIRMATION, AWAITING_ADDITIONAL_TEXT, AWAITING_ADDITIONAL_PHOTO = (
    range(4)
)


async def ms_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la conversación para el mensaje masivo."""
    chat_id = update.effective_chat.id

    if chat_id not in ADMIN_CHAT_IDS:
        await update.message.reply_text(
            _("🚫 Comando no autorizado.", chat_id), parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END

    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    mensaje_instrucciones = _(
        "✍️ *Creación de Mensaje Masivo*\n\n"
        "Por favor, envía el contenido principal del mensaje.\n"
        "Puedes enviar una imagen, un texto, o una imagen con texto.",
        chat_id,
    )

    await update.message.reply_text(mensaje_instrucciones, parse_mode=ParseMode.MARKDOWN)
    return AWAITING_CONTENT


async def handle_initial_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Captura el primer contenido enviado (texto o foto)."""
    message = update.message
    chat_id = update.effective_chat.id

    btn_add_photo = _("🖼️ Añadir Imagen", chat_id)
    btn_send_only_text = _("➡️ Enviar Solo Texto", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)
    btn_add_edit_text = _("✍️ Añadir/Editar Texto", chat_id)
    btn_send_only_photo = _("➡️ Enviar Solo Imagen", chat_id)

    if message.text:
        context.user_data["ms_text"] = message.text
        keyboard = [
            [InlineKeyboardButton(btn_add_photo, callback_data="ms_add_photo")],
            [InlineKeyboardButton(btn_send_only_text, callback_data="ms_send_final")],
            [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
        ]
        mensaje_texto_recibido = _(
            "✅ Texto recibido. ¿Deseas añadir una imagen o enviar el mensaje?", chat_id
        )
        await message.reply_text(
            mensaje_texto_recibido, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif message.photo:
        context.user_data["ms_photo_id"] = message.photo[-1].file_id
        if message.caption:
            context.user_data["ms_text"] = message.caption

        keyboard = [
            [InlineKeyboardButton(btn_add_edit_text, callback_data="ms_add_text")],
            [InlineKeyboardButton(btn_send_only_photo, callback_data="ms_send_final")],
            [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
        ]
        mensaje_foto_recibida = _(
            "✅ Imagen recibida. ¿Deseas añadir o editar el texto del pie de foto?", chat_id
        )
        await message.reply_text(mensaje_foto_recibida, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        mensaje_error_contenido = _("⚠️ Por favor, envía un texto o una imagen.", chat_id)
        await message.reply_text(mensaje_error_contenido)
        return AWAITING_CONTENT

    return AWAITING_CONFIRMATION


async def handle_confirmation_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja los botones de confirmación."""
    query = update.callback_query
    await query.answer()
    choice = query.data
    user_id = query.from_user.id

    if choice == "ms_add_text":
        mensaje_add_text = _(
            "✍️ De acuerdo, por favor envía el texto que quieres usar como pie de foto.", user_id
        )
        await query.edit_message_text(mensaje_add_text)
        return AWAITING_ADDITIONAL_TEXT
    elif choice == "ms_add_photo":
        mensaje_add_photo = _(
            "🖼️ Entendido, por favor envía la imagen que quieres adjuntar.", user_id
        )
        await query.edit_message_text(mensaje_add_photo)
        return AWAITING_ADDITIONAL_PHOTO
    elif choice == "ms_send_final":
        return await send_broadcast(query, context)
    elif choice == "ms_cancel":
        mensaje_cancelar = _("🚫 Operación cancelada.", user_id)
        await query.edit_message_text(mensaje_cancelar)
        return ConversationHandler.END


async def receive_additional_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el texto adicional para una imagen."""
    chat_id = update.effective_chat.id
    context.user_data["ms_text"] = update.message.text

    btn_send = _("🚀 Enviar a todos los usuarios", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)

    keyboard = [
        [InlineKeyboardButton(btn_send, callback_data="ms_send_final")],
        [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
    ]

    mensaje_confirmacion = _("✅ Texto añadido. El mensaje está listo para ser enviado.", chat_id)

    await update.message.reply_text(
        mensaje_confirmacion, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_CONFIRMATION


async def receive_additional_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la imagen adicional para un texto."""
    chat_id = update.effective_chat.id
    context.user_data["ms_photo_id"] = update.message.photo[-1].file_id

    btn_send = _("🚀 Enviar a todos los usuarios", chat_id)
    btn_cancel = _("❌ Cancelar", chat_id)

    keyboard = [
        [InlineKeyboardButton(btn_send, callback_data="ms_send_final")],
        [InlineKeyboardButton(btn_cancel, callback_data="ms_cancel")],
    ]

    mensaje_confirmacion = _("✅ Imagen añadida. El mensaje está listo para ser enviado.", chat_id)

    await update.message.reply_text(
        mensaje_confirmacion, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_CONFIRMATION


async def send_broadcast(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función final que envía el mensaje a todos los usuarios."""
    chat_id = query.from_user.id

    mensaje_iniciando = _(
        "⏳ *Enviando mensaje a todos los usuarios...*\nEsto puede tardar un momento.", chat_id
    )
    await query.edit_message_text(mensaje_iniciando, parse_mode=ParseMode.MARKDOWN)

    from bot.handlers.admin.utils import _enviar_mensaje_telegram_async_ref

    if not _enviar_mensaje_telegram_async_ref:
        mensaje_error_interno = _(
            "❌ Error interno: La función de envío masivo no ha sido inicializada.", chat_id
        )
        await query.message.reply_text(mensaje_error_interno)
        return ConversationHandler.END

    text_to_send = context.user_data.get("ms_text", "")
    photo_id_to_send = context.user_data.get("ms_photo_id")

    container = context.bot_data["container"]
    user_repo = container.user_repo

    usuarios = await user_repo.get_all()
    chat_ids = [str(u["user_id"]) for u in usuarios]

    fallidos = await _enviar_mensaje_telegram_async_ref(
        text_to_send, chat_ids, photo=photo_id_to_send
    )

    total_enviados = len(chat_ids) - len(fallidos)
    if fallidos:
        fallidos_reporte = [f"  - `{chat_id}`: _{error}_" for chat_id, error in fallidos.items()]
        fallidos_str = "\n".join(fallidos_reporte)

        mensaje_admin_base = _(
            "✅ Envío completado.\n\n"
            "Enviado a *{total_enviados}* de {total_usuarios} usuarios.\n\n"
            "❌ Fallos ({num_fallos}):\n{fallidos_str}",
            chat_id,
        )
        mensaje_admin = mensaje_admin_base.format(
            total_enviados=total_enviados,
            total_usuarios=len(chat_ids),
            num_fallos=len(fallidos),
            fallidos_str=fallidos_str,
        )
    else:
        mensaje_admin_base = _(
            "✅ ¡Éxito! Mensaje enviado a todos los *{total_usuarios}* usuarios.", chat_id
        )
        mensaje_admin = mensaje_admin_base.format(total_usuarios=len(chat_ids))

    await query.message.reply_text(mensaje_admin, parse_mode=ParseMode.MARKDOWN)

    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    return ConversationHandler.END


async def cancel_ms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función para cancelar la conversación."""
    chat_id = update.effective_chat.id

    mensaje_cancelado = _("🚫 Operación cancelada.", chat_id)

    await update.message.reply_text(mensaje_cancelado)

    context.user_data.pop("ms_text", None)
    context.user_data.pop("ms_photo_id", None)

    return ConversationHandler.END


# Definición del ConversationHandler para el comando /ms
ms_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("ms", ms_start)],
    states={
        AWAITING_CONTENT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_content),
            MessageHandler(filters.PHOTO, handle_initial_content),
        ],
        AWAITING_CONFIRMATION: [CallbackQueryHandler(handle_confirmation_choice)],
        AWAITING_ADDITIONAL_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_additional_text)
        ],
        AWAITING_ADDITIONAL_PHOTO: [MessageHandler(filters.PHOTO, receive_additional_photo)],
    },
    fallbacks=[CommandHandler("cancelar", cancel_ms)],
    conversation_timeout=600,
)
