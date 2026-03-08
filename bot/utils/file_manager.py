# utils/file_manager.py

import contextlib
import json
import os
import shutil
from datetime import datetime, timedelta

from bot.core.config import LAST_PRICES_PATH, LOG_LINES, LOG_MAX, USUARIOS_PATH
from bot.utils.logger import logger

_USUARIOS_CACHE = None
_MIGRATION_TIMESTAMPS_DONE = False


def migrate_user_timestamps():
    """
    Migrate legacy user data to include registered_at timestamps.
    For users without registered_at, attempts to estimate from available data.
    Returns counts of migrated users.
    """
    global _MIGRATION_TIMESTAMPS_DONE

    # Only run once per process
    if _MIGRATION_TIMESTAMPS_DONE:
        return {"migrated": 0, "already_had": 0, "failed": 0}

    usuarios = cargar_usuarios()
    migrated = 0
    already_had = 0
    failed = 0
    now = datetime.now()

    for _uid, u in usuarios.items():
        # Skip if already has registered_at
        if u.get("registered_at"):
            already_had += 1
            continue

        # Try to estimate registration date from available data
        estimated_date = None

        # 1. Use last_alert_timestamp as oldest available activity
        if u.get("last_alert_timestamp"):
            with contextlib.suppress(Exception):
                estimated_date = u["last_alert_timestamp"]

        # 2. Use last_seen as fallback
        if not estimated_date and u.get("last_seen"):
            with contextlib.suppress(Exception):
                estimated_date = u["last_seen"]

        # 3. Use a default far-past date if no data available
        if not estimated_date:
            # Default to 90 days ago as conservative estimate
            estimated_date = (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
            failed += 1  # Mark as failed (estimated) since we had no real data
        else:
            migrated += 1

        # Set the estimated registration date
        u["registered_at"] = estimated_date

    # Save if any changes were made
    if migrated > 0 or failed > 0:
        guardar_usuarios(usuarios)
        logger.info(
            f"Migration complete: {migrated} migrated, {failed} estimated, {already_had} already had timestamps"
        )

    _MIGRATION_TIMESTAMPS_DONE = True
    return {"migrated": migrated, "already_had": already_had, "failed": failed}


def add_log_line(linea):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_LINES.append(f"[{timestamp}] | {linea}")
    if len(LOG_LINES) > LOG_MAX:
        del LOG_LINES[0]
    print(LOG_LINES[-1])
    logger.info(linea)


def load_last_prices_status():
    if not os.path.exists(LAST_PRICES_PATH):
        return {}
    try:
        with open(LAST_PRICES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


# === GESTIÓN DE USUARIOS ===


def cargar_usuarios():
    global _USUARIOS_CACHE

    # Si ya está en memoria, usar memoria (rápido y seguro)
    if _USUARIOS_CACHE is not None:
        return _USUARIOS_CACHE

    if not os.path.exists(USUARIOS_PATH):
        _USUARIOS_CACHE = {}
        return _USUARIOS_CACHE

    try:
        with open(USUARIOS_PATH, encoding="utf-8") as f:
            _USUARIOS_CACHE = json.load(f)
            # Ejecutar migracion automaticamente despues de cargar
            migrate_user_timestamps()
            return _USUARIOS_CACHE
    except json.JSONDecodeError:
        # Si el archivo está roto, intentamos recuperar backup o iniciar vacío
        if os.path.exists(USUARIOS_PATH):
            shutil.copy(USUARIOS_PATH, f"{USUARIOS_PATH}.corrupto")
        _USUARIOS_CACHE = {}
        return _USUARIOS_CACHE
    except Exception:
        return {}


def guardar_usuarios(usuarios_data=None):
    global _USUARIOS_CACHE

    if usuarios_data is not None:
        _USUARIOS_CACHE = usuarios_data

    if _USUARIOS_CACHE is None:
        return

    try:
        # Guardado atómico: escribe en .tmp y renombra (evita corrupción)
        temp_path = f"{USUARIOS_PATH}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(_USUARIOS_CACHE, f, indent=4)
        os.replace(temp_path, USUARIOS_PATH)
    except Exception as e:
        logger.error(f"❌ Error al guardar usuarios: {e}")


def check_feature_access(chat_id, feature_type, current_count=None):
    """
    Verifica acceso - ahora siempre permitido para usuarios registrados.
    El control de acceso se maneja via @permitted_only decorator en los handlers.
    """
    # Acceso siempre permitido - el control se hace en los handlers via @permitted_only
    if feature_type == "temp_min_val":
        return 0.25, "Valor Mínimo"
    return True, "OK"


def registrar_uso_comando(chat_id, comando):
    """
    Registra uso de comando - función simplificada.
    El control de acceso se maneja via @permitted_only decorator.
    """
    # Ya no se necesita registro de uso diario - acceso ilimitado para usuarios aprobados
    # La función se mantiene para compatibilidad pero no hace nada
    pass


# ------------------------------------------------------------------


def set_user_language(chat_id: int, lang_code: str):
    usuarios = cargar_usuarios()
    chat_id_str = str(chat_id)
    if chat_id_str in usuarios:
        usuarios[chat_id_str]["language"] = lang_code
        guardar_usuarios(usuarios)


def get_user_language(chat_id: int) -> str:
    usuarios = cargar_usuarios()
    return usuarios.get(str(chat_id), {}).get("language", "es")


def obtener_monedas_usuario(chat_id):
    usuarios = cargar_usuarios()
    return usuarios.get(str(chat_id), {}).get("monedas", [])


def obtener_datos_usuario(chat_id):
    usuarios = cargar_usuarios()
    return usuarios.get(str(chat_id), {})
