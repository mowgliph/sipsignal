# utils/file_manager.py

import contextlib
import json
import os
import shutil
from datetime import datetime, timedelta

from bot.core.config import ADMIN_CHAT_IDS, LAST_PRICES_PATH, LOG_LINES, LOG_MAX, USUARIOS_PATH
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


# --- FASE 1: NUEVAS FUNCIONES DE SUSCRIPCIÓN Y LÍMITES ---


def check_feature_access(chat_id, feature_type, current_count=None):
    """
    Verifica si el usuario tiene permiso o si alcanzó su límite.
    Retorna: (Bool, Mensaje) -> (True, "OK") o (False, "Razón")
    """
    # 1. Los Admins siempre tienen pase VIP (Ilimitado)
    if chat_id in ADMIN_CHAT_IDS:
        if feature_type == "temp_min_val":
            return 0.25, "Admin Mode"  # Mínimo flexible
        return True, "Admin Mode"

    # Inline: obtener_datos_usuario_seguro logic
    usuarios = cargar_usuarios()
    chat_id_str = str(chat_id)
    if chat_id_str not in usuarios:
        return False, "Usuario no registrado. Usa /start."
    user_data = usuarios[chat_id_str]
    guardar = False
    today_str = datetime.now().strftime("%Y-%m-%d")
    if "daily_usage" not in user_data or user_data["daily_usage"].get("date") != today_str:
        user_data["daily_usage"] = {
            "date": today_str,
            "ver": 0,
            "ta": 0,
            "temp_changes": 0,
            "btc": 0,
        }
        guardar = True
    else:
        keys_necesarias = ["ver", "ta", "temp_changes", "btc"]
        for key in keys_necesarias:
            if key not in user_data["daily_usage"]:
                user_data["daily_usage"][key] = 0
                guardar = True
    if "subscriptions" not in user_data:
        user_data["subscriptions"] = {
            "alerts_extra": {"qty": 0, "expires": None},
            "coins_extra": {"qty": 0, "expires": None},
            "watchlist_bundle": {"active": False, "expires": None},
            "ta_vip": {"active": False, "expires": None},
        }
        guardar = True
    if "last_seen" not in user_data:
        user_data["last_seen"] = None
        guardar = True
    if "registered_at" not in user_data:
        user_data["registered_at"] = None
        guardar = True
    if guardar:
        guardar_usuarios(usuarios)

    if not user_data:
        return False, "Usuario no registrado. Usa /start."

    subs = user_data["subscriptions"]
    daily = user_data["daily_usage"]
    now = datetime.now()

    # Helper para verificar si una subscripción está activa y vigente
    def is_active(sub_key):
        if not subs.get(sub_key):
            return False
        if not subs[sub_key]["active"]:
            return False
        if not subs[sub_key]["expires"]:
            return False
        try:
            exp_date = datetime.strptime(subs[sub_key]["expires"], "%Y-%m-%d %H:%M:%S")
            return exp_date > now
        except ValueError:
            return False

    # --- REGLA 1: Comando /ver ---
    if feature_type == "ver_limit":
        limit = 8  # Gratis
        if is_active("watchlist_bundle"):
            limit = 48  # Pago (Pack Control Total)

        if daily["ver"] >= limit:
            return False, (
                f"🔒 *Límite Diario Alcanzado ({limit}/{limit})*\n—————————————————\n\n"
                f"Has usado tus {limit} consultas gratuitas de /ver por hoy.\n"
                f"El límite se reinicia mañana."
            )
        return True, "OK"

    # --- REGLA 2: Comando /ta ---
    if feature_type == "ta_limit":
        limit = 21  # Gratis
        if is_active("ta_vip"):
            limit = 999999  # Pago (Ilimitado)

        if daily["ta"] >= limit:
            return False, (
                f"🔒 *Límite Diario Alcanzado ({limit}/{limit})*\n—————————————————\n\n"
                f"Has realizado {limit} análisis técnicos hoy.\n"
                f"El límite se reinicia mañana."
            )
        return True, "OK"

    # --- REGLA 4: Cambios de Temporalidad ---
    if feature_type == "temp_min_val":
        min_val = 8.0
        if is_active("watchlist_bundle"):
            min_val = 0.25
        return min_val, "Valor Mínimo"

    # --- REGLA 5: Cambios de Temporalidad ---
    if feature_type == "temp_change_limit":
        if is_active("watchlist_bundle"):
            return True, "OK"  # Ilimitado con el pack

        # Plan Gratis: Solo 1 cambio al día
        if daily.get("temp_changes", 0) >= 1:
            return False, (
                "🔒 *Límite Diario Alcanzado*\n—————————————————\n\n"
                "Solo puedes cambiar la temporalidad 1 vez al día en el plan gratuito.\n"
                "Adquiere el 'Pack Control Total' para cambios ilimitados durante 30 días, entre otras finciones."
            )
        return True, "OK"

    # --- REGLA 6: Capacidad de Lista de Monedas (/monedas) ---
    if feature_type == "coins_capacity":
        # current_count es la cantidad de monedas que el usuario INTENTA guardar
        base_capacity = 5

        # Verificamos extras comprados
        extra_capacity = 0
        if is_active("coins_extra"):
            extra_capacity = subs["coins_extra"]["qty"]

        total_capacity = base_capacity + extra_capacity

        if current_count > total_capacity:
            return False, (
                f"🔒 *Capacidad Excedida ({current_count}/{total_capacity})*\n—————————————————\n\n"
                f"Tu límite actual es de {total_capacity} monedas.\n"
                f"Has intentado guardar {current_count}.\n\n"
                f"Elimina alguna moneda antes de agregar nuevas."
            )
        return True, "OK"

    # --- REGLA 7: Capacidad de Alertas de Cruce (/alerta) ---
    if feature_type == "alerts_capacity":
        # current_count aquí será el total de alertas ACTIVAS en la BD
        # Recordar: 1 alerta de usuario = 2 registros en BD (Arriba + Abajo)

        base_pairs = 10  # 10 alertas del usuario (20 registros)
        extra_pairs = 0

        if is_active("alerts_extra"):
            extra_pairs = subs["alerts_extra"]["qty"]

        total_pairs = base_pairs + extra_pairs
        total_slots_db = total_pairs * 2  # Capacidad real en base de datos

        # Al crear una alerta nueva, se suman 2 slots. Verificamos si caben.
        if (current_count + 2) > total_slots_db:
            return False, (
                f"🔒 *Capacidad de Alertas Llena*\n—————————————————\n\n"
                f"Tienes ocupados tus {total_pairs} espacios para alertas.\n"
                f"Elimina alguna con /misalertas antes de crear nuevas."
            )
        return True, "OK"

    return True, "OK"


def registrar_uso_comando(chat_id, comando):
    """Incrementa el contador de uso para un comando específico y actualiza last_seen."""
    # Los admins no registran uso (son ilimitados)
    if chat_id in ADMIN_CHAT_IDS:
        return

    # Inline: obtener_datos_usuario_seguro logic (ensure structure exists)
    usuarios = cargar_usuarios()
    chat_id_str = str(chat_id)
    if chat_id_str in usuarios:
        usuario = usuarios[chat_id_str]
        guardar = False
        today_str = datetime.now().strftime("%Y-%m-%d")
        if "daily_usage" not in usuario or usuario["daily_usage"].get("date") != today_str:
            usuario["daily_usage"] = {
                "date": today_str,
                "ver": 0,
                "ta": 0,
                "temp_changes": 0,
                "btc": 0,
            }
            guardar = True
        else:
            keys_necesarias = ["ver", "ta", "temp_changes", "btc"]
            for key in keys_necesarias:
                if key not in usuario["daily_usage"]:
                    usuario["daily_usage"][key] = 0
                    guardar = True
        if "subscriptions" not in usuario:
            usuario["subscriptions"] = {
                "alerts_extra": {"qty": 0, "expires": None},
                "coins_extra": {"qty": 0, "expires": None},
                "watchlist_bundle": {"active": False, "expires": None},
                "ta_vip": {"active": False, "expires": None},
            }
            guardar = True
        if "last_seen" not in usuario:
            usuario["last_seen"] = None
            guardar = True
        if "registered_at" not in usuario:
            usuario["registered_at"] = None
            guardar = True
        if guardar:
            guardar_usuarios(usuarios)

    usuarios = cargar_usuarios()
    chat_id_str = str(chat_id)

    if chat_id_str in usuarios:
        daily = usuarios[chat_id_str].get("daily_usage", {})

        # Incrementamos de forma segura (creando la clave si por alguna razón no está)
        actual = daily.get(comando, 0)
        daily[comando] = actual + 1

        usuarios[chat_id_str]["daily_usage"] = daily  # Asegurar asignación

        # MEJORA: Actualizar last_seen con cada uso de comando (actividad real del usuario)
        usuarios[chat_id_str]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        guardar_usuarios(usuarios)

        # LOG DE DEBUG (Opcional: te ayudará a ver en consola si cuenta)
        print(f"DEBUG: Usuario {chat_id} usó {comando}. Nuevo total: {daily[comando]}")


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
