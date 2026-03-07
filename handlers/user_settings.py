# handlers/user_settings.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.file_manager import get_user_language, set_user_language


# Función identidad para reemplazar i18n (textos ya están en español)
def _(message, *args, **kwargs):
    return message


# Soporte de idiomas
SUPPORTED_LANGUAGES = {"es": "🇪🇸 Español", "en": "🇬🇧 English"}


# COMANDO /lang para cambiar el idioma
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú para cambiar el idioma."""
    user_id = update.effective_user.id
    current_lang = get_user_language(user_id)

    text = _(
        "🌐 *Selecciona tu idioma:*\n\nEl idioma actual es: {current_lang_name}", user_id
    ).format(current_lang_name=SUPPORTED_LANGUAGES.get(current_lang, "N/A"))

    keyboard = []
    for code, name in SUPPORTED_LANGUAGES.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    name + (" ✅" if code == current_lang else ""), callback_data=f"set_lang_{code}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


# CALLBACK para cambiar el idioma
async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang_code = query.data.split("set_lang_")[1]

    if lang_code in SUPPORTED_LANGUAGES:
        set_user_language(user_id, lang_code)

        new_text = _(
            "✅ ¡Idioma cambiado a *{new_lang_name}*!\n"
            "Usa el comando /lang si deseas cambiarlo de nuevo.",
            user_id,
        ).format(new_lang_name=SUPPORTED_LANGUAGES[lang_code])

        await query.edit_message_text(new_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await query.edit_message_text(
            _("⚠️ Idioma no soportado.", user_id), parse_mode=ParseMode.MARKDOWN
        )
