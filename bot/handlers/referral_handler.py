"""Handler for /ref command."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from bot.utils import role_required
from bot.utils.logger import logger


async def _get_referral_stats(user_id: int) -> dict:
    """Get referral statistics for user."""
    from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

    repo = PostgreSQLReferralRepository()
    count = await repo.get_referral_count(user_id)
    referrals = await repo.get_referrals(user_id)

    last_referred = None
    if referrals:
        last = referrals[0]
        username = last.get("username")
        last_referred = {
            "username": f"@{username}" if username else f"User {last['user_id']}",
            "date": last.get("referred_at"),
        }

    return {
        "count": count,
        "last_referred": last_referred,
    }


@role_required(["approved", "trader", "admin"])
async def ref_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show user's referral code and link.

    Usage: /ref
    """
    user_id = update.effective_chat.id

    try:
        # Get or generate referral code
        from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

        repo = PostgreSQLReferralRepository()
        code = await repo.get_referrer_code(user_id)

        if not code:
            code = await repo.generate_referrer_code(user_id)
            logger.info(f"Generated referral code {code} for user {user_id}")

        # Get stats
        stats = await _get_referral_stats(user_id)

        # Build message
        message = (
            f"🔗 *TU ENLACE DE REFERIDO*\n"
            f"─────────────────────\n\n"
            f"Tu código: `{code}`\n\n"
            f"Enlace directo:\n"
            f"t.me/sipsignal_bot?start={code}\n\n"
            f"Comparte este enlace para invitar amigos a SipSignal.\n\n"
            f"📊 *Estadísticas:*\n"
            f"• Referidos totales: {stats['count']}\n"
        )

        if stats["last_referred"]:
            last = stats["last_referred"]
            message += f"• Último referido: {last['username']}\n"

        if stats["count"] == 0:
            message += "\n¡Comparte tu enlace para comenzar!\n"

        message += "\n─────────────────────\n"
        message += "Usa /ref stats para ver lista completa"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error en /ref: {e}")
        await update.message.reply_text("⚠️ Error al procesar. Intenta de nuevo.")


async def ref_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show detailed list of referrals.

    Usage: /ref stats
    """
    user_id = update.effective_chat.id

    try:
        from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

        repo = PostgreSQLReferralRepository()
        referrals = await repo.get_referrals(user_id)
        count = len(referrals)

        if count == 0:
            await update.message.reply_text(
                "📊 *TUS REFERIDOS*\n"
                "─────────────────────\n\n"
                "Aún no tienes referidos.\n\n"
                "¡Comparte tu enlace para comenzar!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Build list (max 20 for readability)
        message = f"📊 *TUS REFERIDOS* ({count})\n"
        message += "─────────────────────\n\n"

        for i, ref in enumerate(referrals[:20], 1):
            username = ref.get("username")
            user_str = f"@{username}" if username else f"User {ref['user_id']}"
            date_str = (
                ref.get("referred_at", "").strftime("%d/%m/%Y") if ref.get("referred_at") else "N/A"
            )
            message += f"{i}. {user_str} - {date_str}\n"

        if count > 20:
            message += f"\n... y {count - 20} más"

        message += "\n\n─────────────────────\n"
        message += f"Total: {count} referidos"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error en /ref stats: {e}")
        await update.message.reply_text("⚠️ Error al obtener datos. Intenta de nuevo.")


# Handlers for registration in bot
ref_handler = CommandHandler("ref", ref_command)
