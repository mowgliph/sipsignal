#!/usr/bin/env python3
"""
Script de migración de datos JSON → PostgreSQL

Migra los datos de usuarios desde bot/data/users.json hacia las tablas de PostgreSQL:
- users (ya existe - solo verifica timestamps)
- user_watchlists (monedas)
- user_preferences (hbd_alerts, intervalo_alerta_h)
- user_usage_stats (daily_usage)

Uso:
    python scripts/migrate_json_to_postgres.py
"""

import asyncio
import json
import os
import sys
from datetime import UTC, datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.core.config import USUARIOS_PATH
from bot.infrastructure.database.user_repositories import (
    PostgreSQLUserPreferenceRepository,
    PostgreSQLUserWatchlistRepository,
)
from bot.utils.logger import logger


async def migrate_user_data():
    """Migra todos los usuarios desde JSON a PostgreSQL."""

    if not os.path.exists(USUARIOS_PATH):
        logger.info("📄 No se encontró users.json - omitiendo migración")
        return {"migrated": 0, "skipped": 0, "errors": 0}

    # Cargar datos JSON
    try:
        with open(USUARIOS_PATH, encoding="utf-8") as f:
            users_json = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"❌ Error al leer users.json: {e}")
        return {"migrated": 0, "skipped": 0, "errors": 1}

    if not users_json:
        logger.info("📄 users.json está vacío - omitiendo migración")
        return {"migrated": 0, "skipped": 0, "errors": 0}

    logger.info(f"📊 Migrando {len(users_json)} usuarios desde JSON...")

    # Inicializar repositorios
    watchlist_repo = PostgreSQLUserWatchlistRepository()
    preference_repo = PostgreSQLUserPreferenceRepository()

    migrated = 0
    skipped = 0
    errors = 0

    for chat_id_str, user_data in users_json.items():
        try:
            user_id = int(chat_id_str)

            # 1. Migrar watchlist (monedas)
            monedas = user_data.get("monedas", [])
            if monedas:
                await watchlist_repo.set_coins(user_id, monedas)
                logger.debug(f"✅ User {user_id}: migradas {len(monedas)} monedas")

            # 2. Migrar preferencias
            hbd_alerts = user_data.get("hbd_alerts", False)
            intervalo_alerta = user_data.get("intervalo_alerta_h", 1.0)

            await preference_repo.set_hbd_alerts(user_id, hbd_alerts)
            await preference_repo.set_alert_interval(user_id, float(intervalo_alerta))
            logger.debug(
                f"✅ User {user_id}: preferencias migradas (hbd={hbd_alerts}, intervalo={intervalo_alerta})"
            )

            # 3. Migrar daily_usage a user_usage_stats
            daily_usage = user_data.get("daily_usage", {})
            if daily_usage:
                # Extraer fecha del daily_usage
                date_str = daily_usage.get("date")
                if date_str:
                    try:
                        usage_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        today = datetime.now(UTC).date()

                        # Solo migrar si es del día actual o reciente (últimos 90 días)
                        if (today - usage_date).days <= 90:
                            # Mapear campos
                            field_mapping = {
                                "ver": "ver_count",
                                "ta": "ta_count",
                                "temp_changes": "temp_changes_count",
                                "btc": "btc_count",
                                "graf": "graf_count",
                            }

                            # Insertar estadísticas
                            values = [user_id, usage_date]
                            columns = ["user_id", "usage_date"]
                            update_cols = []

                            for json_field, db_column in field_mapping.items():
                                value = daily_usage.get(json_field, 0)
                                if isinstance(value, int) and value > 0:
                                    columns.append(db_column)
                                    values.append(value)
                                    update_cols.append(f"{db_column} = EXCLUDED.{db_column}")

                            if len(columns) > 2:  # Más que solo user_id y date
                                from bot.core import database

                                columns_str = ", ".join(columns)
                                placeholders = ", ".join(
                                    ["$" + str(i) for i in range(1, len(values) + 1)]
                                )
                                update_str = ", ".join(update_cols)

                                await database.execute(
                                    f"""
                                    INSERT INTO user_usage_stats ({columns_str})
                                    VALUES ({placeholders})
                                    ON CONFLICT (user_id, usage_date) DO UPDATE SET
                                        {update_str},
                                        updated_at = NOW()
                                    """,
                                    *values,
                                )
                                logger.debug(f"✅ User {user_id}: daily_usage migrado ({date_str})")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ User {user_id}: error al migrar daily_usage: {e}")

            migrated += 1

        except Exception as e:
            logger.error(f"❌ Error migrando user {chat_id_str}: {e}")
            errors += 1

    logger.info(
        f"🎉 Migración completada: {migrated} migrados, {skipped} omitidos, {errors} errores"
    )

    # Opcional: Renombrar archivo JSON como backup
    if migrated > 0 and errors == 0:
        backup_path = f"{USUARIOS_PATH}.migrated"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(USUARIOS_PATH, backup_path)
        logger.info(f"💾 users.json renombrado a {backup_path} (backup)")

    return {"migrated": migrated, "skipped": skipped, "errors": errors}


async def verify_migration():
    """Verifica que la migración se haya completado correctamente."""
    from bot.core import database

    logger.info("🔍 Verificando migración...")

    # Contar usuarios en cada tabla
    users_count = await database.fetchval("SELECT COUNT(*) FROM users")
    watchlists_count = await database.fetchval("SELECT COUNT(*) FROM user_watchlists")
    preferences_count = await database.fetchval("SELECT COUNT(*) FROM user_preferences")
    usage_stats_count = await database.fetchval("SELECT COUNT(*) FROM user_usage_stats")

    logger.info("📊 Resultados:")
    logger.info(f"   - users: {users_count}")
    logger.info(f"   - user_watchlists: {watchlists_count}")
    logger.info(f"   - user_preferences: {preferences_count}")
    logger.info(f"   - user_usage_stats: {usage_stats_count}")

    # Verificar consistencia
    if users_count > 0 and watchlists_count == 0:
        logger.warning("⚠️ Advertencia: hay usuarios pero no watchlists migradas")

    return {
        "users": users_count,
        "watchlists": watchlists_count,
        "preferences": preferences_count,
        "usage_stats": usage_stats_count,
    }


async def main():
    """Función principal."""
    logger.info("=" * 60)
    logger.info("🚀 Iniciando migración JSON → PostgreSQL")
    logger.info("=" * 60)

    # Ejecutar migración
    result = await migrate_user_data()

    # Verificar migración
    await verify_migration()

    logger.info("=" * 60)
    logger.info("✅ Migración finalizada")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(main())
