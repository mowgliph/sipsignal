#!/usr/bin/env python3
"""bot_main.py - Punto de entrada mínimo funcional de SipSignal.

Entry point básico del bot de Telegram con solo comandos esenciales:
- /start: Mensaje de bienvenida
- /status: Información del sistema

Autor: SipSignal Team
Versión: 1.0.0-dev
"""

import asyncio
import platform
import sys
from datetime import datetime, timezone
from typing import NoReturn

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

from core.config import settings, VERSION, PID

# --- Metadata ---
START_TIME = datetime.now(timezone.utc)
BOT_VERSION = "1.0.0-dev"


async def check_admin(update: Update) -> bool:
    """Verifica si el chat_id está en la lista de administradores."""
    chat_id = update.effective_chat.id
    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text(
            "⛔ Acceso denegado. No tienes permisos para usar este bot."
        )
        return False
    return True


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /start - Mensaje de bienvenida."""
    if not await check_admin(update):
        return

    message = (
        "✅ *SipSignal activo*\n\n"
        "Sistema de trading BTC iniciando...\n"
        f"🤖 Bot v{BOT_VERSION}\n"
        "📊 Listo para recibir señales"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para /status - Información del sistema."""
    if not await check_admin(update):
        return

    now = datetime.now(timezone.utc)
    uptime = now - START_TIME
    uptime_str = str(uptime).split(".")[0]  # Quitar microsegundos

    message = (
        "📊 *Estado del Sistema*\n\n"
        f"🕐 *Fecha UTC:* `{now.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"🏷️ *Versión:* `{BOT_VERSION}`\n"
        f"⏱️ *Uptime:* `{uptime_str}`\n"
        f"🐍 *Python:* `{platform.python_version()}`\n"
        f"🖥️ *PID:* `{PID}`\n"
        f"🔧 *Entorno:* `{settings.environment}`"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


async def post_init(app: Application) -> None:
    """Se ejecuta después de inicializar el bot."""
    print(f"✅ SipSignal Bot v{BOT_VERSION} iniciado correctamente")
    print(f"📊 Admin IDs configurados: {settings.admin_chat_ids}")
    print(f"🔧 Entorno: {settings.environment}")
    print(f"📝 Log Level: {settings.log_level}")


def main() -> NoReturn:
    """Inicia el bot con configuración mínima."""
    print(f"🚀 Iniciando SipSignal Bot v{BOT_VERSION}...")

    try:
        builder = ApplicationBuilder().token(settings.token_telegram)
        app = builder.build()

        # Registro de handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("status", status_command))

        # Post-init callback
        app.post_init = post_init

        print("✅ Handlers registrados. Iniciando polling...")
        print("   Presiona Ctrl+C para detener")

        app.run_polling()

    except KeyboardInterrupt:
        print("\n👋 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
