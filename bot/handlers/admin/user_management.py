"""User management handler for /users command."""

import os
import time
from collections import Counter
from datetime import UTC, datetime, timedelta

import psutil
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.core.config import (
    ADMIN_CHAT_IDS,
    ADS_PATH,
    LAST_PRICES_PATH,
    TEMPLATE_PATH,
    VERSION,
)
from bot.handlers.admin.utils import _, _clean_markdown
from bot.utils.telemetry import (
    get_commands_per_user_from_repo,
    get_daily_events_from_repo,
    get_retention_metrics_from_repo,
    get_users_registration_stats_from_repo,
)

# Definición global del objeto PSUTIL (reutilizado para evitar múltiples instancias)
proc_global = psutil.Process(os.getpid())
proc_global.cpu_percent(interval=None)


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dashboard de Administración SUPER PRO.
    Muestra estadísticas de Usuarios, Negocio, Carga, BTC, HBD, Clima y Valerts.
    """
    chat_id = update.effective_chat.id
    chat_id_str = str(chat_id)

    container = context.bot_data["container"]
    user_repo = container.user_repo
    watchlist_repo = container.user_watchlist_repo
    preference_repo = container.user_preference_repo

    usuarios = await user_repo.get_all()
    usuarios_dict = {str(u["user_id"]): u for u in usuarios}

    all_alerts = {}

    if chat_id not in ADMIN_CHAT_IDS:
        user_data = usuarios_dict.get(chat_id_str)
        if not user_data:
            await update.message.reply_text(_("❌ No estás registrado.", chat_id))
            return

        monedas = await watchlist_repo.get_coins(chat_id)
        hbd_enabled = await preference_repo.get_hbd_alerts(chat_id)

        alerts_count = 0
        btc_status = "❌ Eliminado"
        hbd_status = "✅ Activado" if hbd_enabled else "❌ Desactivado"
        subs_txt = "_Sin suscripciones activas_"

        msg = (
            f"👤 *TU PERFIL SIPSIGNAL*\n"
            f"—————————————————\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🗣 Idioma: `{user_data.get('language', 'es')}`\n\n"
            f"📊 *Configuración:*\n"
            f"• Monedas Lista: `{', '.join(monedas)}`\n"
            f"• Alertas Cruce: `{alerts_count}` activas\n\n"
            f"📡 *Servicios Activos:*\n"
            f"• Monitor BTC: {btc_status}\n"
            f"• Monitor HBD: {hbd_status}\n\n"
            f"💎 *Suscripciones:*\n"
            f"{subs_txt}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    msg_loading = await update.message.reply_text(
        _("⏳ *Analizando Big Data...*", chat_id), parse_mode=ParseMode.MARKDOWN
    )

    retention = get_retention_metrics_from_repo(user_repo)
    cmd_stats = get_commands_per_user_from_repo(user_repo, container.user_usage_stats_repo)
    daily_events = get_daily_events_from_repo(user_repo, container.user_usage_stats_repo)
    reg_stats = get_users_registration_stats_from_repo(user_repo)

    total_users = len(usuarios)
    active_24h = 0
    active_7d = 0
    active_30d = 0
    lang_es = 0
    lang_en = 0

    new_today = 0
    new_7d = 0
    new_30d = 0

    total_usage_today = 0
    usage_breakdown = Counter()

    now = datetime.now(UTC)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)

    for _uid, u in usuarios.items():
        last_seen_str = u.get("last_seen") or u.get("last_alert_timestamp")
        if last_seen_str:
            try:
                last_dt = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                delta = now - last_dt
                if delta.total_seconds() < 86400:
                    active_24h += 1
                if delta.total_seconds() < 86400 * 7:
                    active_7d += 1
                if delta.total_seconds() < 86400 * 30:
                    active_30d += 1
            except Exception:
                pass

        reg_str = u.get("registered_at")
        if reg_str:
            try:
                reg_dt = datetime.strptime(reg_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                if reg_dt >= cutoff_24h:
                    new_today += 1
                if reg_dt >= cutoff_7d:
                    new_7d += 1
                if reg_dt >= cutoff_30d:
                    new_30d += 1
            except Exception:
                pass

        if u.get("language") == "en":
            lang_en += 1
        else:
            lang_es += 1

        daily = u.get("daily_usage", {})
        if daily.get("date") == now.strftime("%Y-%m-%d"):
            for cmd, count in daily.items():
                if cmd != "date" and isinstance(count, int):
                    usage_breakdown[cmd] += count
                    total_usage_today += count

    total_alerts_active = 0
    coin_popularity = Counter()

    for _uid, alerts in all_alerts.items():
        for a in alerts:
            if a["status"] == "ACTIVE":
                total_alerts_active += 1
                coin_popularity[a["coin"]] += 1

    mem_usage = proc_global.memory_info().rss / 1024 / 1024
    mem_asignada = proc_global.memory_info().vms / 1024 / 1024
    cpu_percent = proc_global.cpu_percent(interval=None)

    uptime_seconds = time.time() - proc_global.create_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))

    size = {"file_size": 0}
    archivos = [
        ADS_PATH,
        LAST_PRICES_PATH,
        TEMPLATE_PATH,
    ]

    total_kb = 0
    for ruta in archivos:
        try:
            if os.path.exists(ruta):
                total_kb += os.path.getsize(ruta)
        except Exception:
            continue

    size["file_size"] = total_kb / 1024 / 1024

    top_cmds = usage_breakdown.most_common(5)
    top_cmds_lines = []
    cmd_emojis = {
        "ver": "👁",
        "tasa": "💱",
        "ta": "📈",
        "temp_changes": "⏱",
        "reminders": "⏰",
        "btc": "🦁",
    }
    for i, (cmd, cnt) in enumerate(top_cmds, 1):
        emoji = cmd_emojis.get(cmd, "⚙️")
        top_cmds_lines.append(f"  {i}. {emoji} /{cmd}: `{cnt}`")
    top_cmds_str = "\n".join(top_cmds_lines) if top_cmds_lines else "  _Sin datos aún_"

    pct_24h = int(active_24h / total_users * 100) if total_users else 0
    pct_7d = int(active_7d / total_users * 100) if total_users else 0
    pct_30d = int(active_30d / total_users * 100) if total_users else 0

    uptime_str_esc = _clean_markdown(uptime_str)
    mem_usage_esc = _clean_markdown(f"{mem_usage:.2f}")
    mem_asignada_esc = _clean_markdown(f"{mem_asignada:.2f}")
    cpu_percent_esc = _clean_markdown(cpu_percent)
    size_file_esc = _clean_markdown(f"{size['file_size']:.2f}")
    total_usage_today_esc = _clean_markdown(total_usage_today)
    usage_ver_esc = _clean_markdown(usage_breakdown["ver"])
    usage_ta_esc = _clean_markdown(usage_breakdown["ta"])
    top_cmds_str_esc = _clean_markdown(top_cmds_str)
    total_users_esc = _clean_markdown(total_users)
    lang_es_esc = _clean_markdown(lang_es)
    lang_en_esc = _clean_markdown(lang_en)
    active_24h_esc = _clean_markdown(active_24h)
    pct_24h_esc = _clean_markdown(pct_24h)
    active_7d_esc = _clean_markdown(active_7d)
    pct_7d_esc = _clean_markdown(pct_7d)
    active_30d_esc = _clean_markdown(active_30d)
    pct_30d_esc = _clean_markdown(pct_30d)
    new_today_esc = _clean_markdown(new_today)
    new_7d_esc = _clean_markdown(new_7d)
    new_30d_esc = _clean_markdown(new_30d)
    reg_stats_with_esc = _clean_markdown(reg_stats["with_registered_at"])
    reg_stats_quality_esc = _clean_markdown(reg_stats["data_quality_pct"])
    retention_7d_esc = _clean_markdown(retention["retention_7d"])
    churn_rate_esc = _clean_markdown(retention["churn_rate"])
    stickiness_esc = _clean_markdown(retention["stickiness"])
    daily_joins_esc = _clean_markdown(daily_events["joins_today"])
    daily_commands_esc = _clean_markdown(daily_events["commands_today"])
    cmd_avg_esc = _clean_markdown(cmd_stats["avg_per_user"])
    version_esc = _clean_markdown(VERSION)
    now_str_esc = _clean_markdown(now.strftime("%Y-%m-%d %H:%M"))
    top_coins_str_esc = _clean_markdown("")

    dashboard = (
        f"👮‍♂️ *PANEL DE CONTROL* v{version_esc}\n"
        f"📅 {now_str_esc}\n"
        f"———————————————————\n\n"
        f"*🖥️ ESTADO DEL SISTEMA*\n"
        f"├ *Uptime:* `{uptime_str_esc}`\n"
        f"├ *RAM:* `{mem_usage_esc} MB`\n"
        f"├ *VMS:* `{mem_asignada_esc} MB`\n"
        f"├ *CPU:* `{cpu_percent_esc}%`\n"
        f"└ *DATA:* `{size_file_esc} MB`\n\n"
        f"⚙️ *CARGA DEL SISTEMA (Hoy)*\n"
        f"├ Comandos Procesados: `{total_usage_today_esc}`\n"
        f"├ /ver: `{usage_ver_esc}` | /ta: `{usage_ta_esc}`\n"
        f"└ Top Comandos:\n{top_cmds_str_esc}\n\n"
        f"👥 *USUARIOS*\n"
        f"├ Totales: `{total_users_esc}` | 🇪🇸 {lang_es_esc} | 🇺🇸 {lang_en_esc}\n"
        f"├ Activos 24h: `{active_24h_esc}` ({pct_24h_esc}%)\n"
        f"├ Activos 7d:  `{active_7d_esc}` ({pct_7d_esc}%)\n"
        f"├ Activos 30d: `{active_30d_esc}` ({pct_30d_esc}%)\n"
        f"├ Nuevos: hoy `{new_today_esc}` | 7d `{new_7d_esc}` | 30d `{new_30d_esc}`\n"
        f"└ Datos completos: `{reg_stats_with_esc}/{total_users_esc}` ({reg_stats_quality_esc}%)\n\n"
        f"📊 *MÉTRICAS DE RETENCIÓN*\n"
        f"├ Retención 7d: `{retention_7d_esc}%`\n"
        f"├ Churn: `{churn_rate_esc}%`\n"
        f"└ Stickiness: `{stickiness_esc}%` (DAU/MAU)\n\n"
        f"📈 *EVENTOS HOY*\n"
        f"├ Nuevos: `{daily_joins_esc}`\n"
        f"├ Comandos: `{daily_commands_esc}`\n"
        f"└ Promedio/cmd: `{cmd_avg_esc}`\n\n"
        f"🏆 *TENDENCIAS DE MERCADO*\n"
        f"🔥 Top Monedas:\n"
        f"`{top_coins_str_esc}`\n"
    )

    await msg_loading.edit_text(dashboard, parse_mode=ParseMode.MARKDOWN)
