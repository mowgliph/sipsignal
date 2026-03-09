"""Ad manager handler for /ad command."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.core.config import ADMIN_CHAT_IDS
from bot.handlers.admin.utils import _
from bot.utils.ads_manager import add_ad, delete_ad, load_ads


async def ad_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gestión de anuncios robusta.
    Si el Markdown del usuario falla, se envía en texto plano.
    """
    chat_id = update.effective_chat.id

    if chat_id not in ADMIN_CHAT_IDS:
        return

    args = context.args

    # --- LISTAR ANUNCIOS ---
    if not args:
        ads = load_ads()
        if not ads:
            await update.message.reply_text(
                _("📭 No hay anuncios activos.\nUsa `/ad add Mi Anuncio` para crear uno.", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        mensaje = _("📢 *Lista de Anuncios Activos:*\n\n", chat_id)
        for i, ad in enumerate(ads):
            mensaje += f"*{i + 1}.* {ad}\n"

        mensaje += _("\nPara borrar: `/ad del N` (ej: `/ad del 1`)", chat_id)

        try:
            await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)
        except BadRequest:
            fallback_msg = _(
                "⚠️ *Error de visualización Markdown*\n"
                "Alguno de tus anuncios tiene caracteres especiales sin cerrar, pero aquí está la lista en texto plano:\n\n",
                chat_id,
            )
            for i, ad in enumerate(ads):
                fallback_msg += f"{i + 1}. {ad}\n"

            fallback_msg += _("\nUsa /ad del N para eliminar.", chat_id)
            await update.message.reply_text(fallback_msg)
        return

    accion = args[0].lower()

    # --- AÑADIR ANUNCIO ---
    if accion == "add":
        if len(args) < 2:
            await update.message.reply_text(
                _("⚠️ Escribe el texto del anuncio.\nEj: `/ad add Visita mi canal @canal`", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        texto_nuevo = " ".join(args[1:])
        add_ad(texto_nuevo)

        try:
            await update.message.reply_text(
                _("✅ Anuncio añadido:\n\n_{ad_text}_", chat_id).format(ad_text=texto_nuevo),
                parse_mode=ParseMode.MARKDOWN,
            )
        except BadRequest:
            await update.message.reply_text(
                _(
                    "✅ Anuncio añadido (Sintaxis MD inválida, mostrado plano):\n\n{ad_text}",
                    chat_id,
                ).format(ad_text=texto_nuevo)
            )

    # --- BORRAR ANUNCIO ---
    elif accion == "del":
        try:
            indice = int(args[1]) - 1
            eliminado = delete_ad(indice)
            if eliminado:
                try:
                    await update.message.reply_text(
                        _("🗑️ Anuncio eliminado:\n\n_{ad_text}_", chat_id).format(ad_text=eliminado),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except BadRequest:
                    await update.message.reply_text(
                        _("🗑️ Anuncio eliminado:\n\n{ad_text}", chat_id).format(ad_text=eliminado)
                    )
            else:
                await update.message.reply_text(
                    _("⚠️ Número de anuncio no válido.", chat_id), parse_mode=ParseMode.MARKDOWN
                )
        except (IndexError, ValueError):
            await update.message.reply_text(
                _("⚠️ Uso: `/ad del N` (N es el número del anuncio).", chat_id),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        await update.message.reply_text(
            _("⚠️ Comandos: `/ad`, `/ad add <txt>`, `/ad del <num>`", chat_id),
            parse_mode=ParseMode.MARKDOWN,
        )
