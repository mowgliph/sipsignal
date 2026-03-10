from datetime import UTC, datetime

import asyncpg

from bot.core import database
from bot.domain.drawdown_state import DrawdownState
from bot.domain.ports.repositories import DrawdownRepository, UserConfigRepository, UserRepository
from bot.domain.user_config import UserConfig


def _record_to_user_config(record: asyncpg.Record) -> UserConfig:
    return UserConfig(
        user_id=record["user_id"],
        chat_id=record["user_id"],
        capital_total=float(record["capital_total"]),
        risk_percent=float(record["risk_percent"]),
        max_drawdown_percent=float(record["max_drawdown_percent"]),
        direction=record["direction"],
        timeframe_primary=record["timeframe_primary"],
        timeframe=record["timeframe_primary"],
        setup_completed=record["setup_completed"],
    )


def _record_to_drawdown_state(record: asyncpg.Record) -> DrawdownState:
    return DrawdownState(
        user_id=record["user_id"],
        current_drawdown_usdt=float(record["current_drawdown_usdt"]),
        current_drawdown_percent=float(record["current_drawdown_percent"]),
        losses_count=record["losses_count"],
        is_paused=record["is_paused"],
        last_reset_at=record["last_reset_at"],
    )


class PostgreSQLUserConfigRepository(UserConfigRepository):
    async def get(self, user_id: int) -> UserConfig | None:
        record = await database.fetchrow(
            "SELECT * FROM user_config WHERE user_id = $1",
            user_id,
        )
        if record is None:
            return None
        return _record_to_user_config(record)

    async def save(self, config: UserConfig) -> UserConfig:
        now = datetime.now(UTC)
        await database.execute(
            """
            INSERT INTO user_config
            (user_id, capital_total, risk_percent, max_drawdown_percent, direction, timeframe_primary, setup_completed, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id) DO UPDATE SET
                capital_total = EXCLUDED.capital_total,
                risk_percent = EXCLUDED.risk_percent,
                max_drawdown_percent = EXCLUDED.max_drawdown_percent,
                direction = EXCLUDED.direction,
                timeframe_primary = EXCLUDED.timeframe_primary,
                setup_completed = EXCLUDED.setup_completed,
                updated_at = EXCLUDED.updated_at
            """,
            config.user_id,
            config.capital_total,
            config.risk_percent,
            config.max_drawdown_percent,
            config.direction,
            config.timeframe_primary,
            config.setup_completed,
            now,
        )
        result = await self.get(config.user_id)
        if result is None:
            raise RuntimeError("Failed to save user config")
        return result


class PostgreSQLDrawdownRepository(DrawdownRepository):
    async def get(self, user_id: int) -> DrawdownState | None:
        record = await database.fetchrow(
            """
            SELECT dt.*, uc.capital_total, uc.max_drawdown_percent
            FROM drawdown_tracker dt
            LEFT JOIN user_config uc ON dt.user_id = uc.user_id
            WHERE dt.user_id = $1
            """,
            user_id,
        )
        if record is None:
            return None
        return _record_to_drawdown_state(record)

    async def save(self, state: DrawdownState) -> DrawdownState:
        existing = await database.fetchrow(
            "SELECT user_id FROM drawdown_tracker WHERE user_id = $1",
            state.user_id,
        )
        if existing is None:
            await database.execute(
                """
                INSERT INTO drawdown_tracker
                (user_id, current_drawdown_usdt, current_drawdown_percent, losses_count, is_paused, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                """,
                state.user_id,
                state.current_drawdown_usdt,
                state.current_drawdown_percent,
                state.losses_count,
                state.is_paused,
            )
        else:
            await database.execute(
                """
                UPDATE drawdown_tracker
                SET current_drawdown_usdt = $1,
                    current_drawdown_percent = $2,
                    losses_count = $3,
                    is_paused = $4,
                    updated_at = NOW()
                WHERE user_id = $5
                """,
                state.current_drawdown_usdt,
                state.current_drawdown_percent,
                state.losses_count,
                state.is_paused,
                state.user_id,
            )
        result = await self.get(state.user_id)
        if result is None:
            raise RuntimeError("Failed to save drawdown state")
        return result

    async def reset(self, user_id: int) -> DrawdownState:
        await database.execute(
            """
            UPDATE drawdown_tracker
            SET current_drawdown_usdt = 0,
                current_drawdown_percent = 0,
                losses_count = 0,
                is_paused = false,
                last_reset_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $1
            """,
            user_id,
        )
        result = await self.get(user_id)
        if result is None:
            raise RuntimeError("Failed to reset drawdown state")
        return result


class PostgreSQLUserRepository(UserRepository):
    async def get(self, user_id: int) -> dict | None:
        record = await database.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id,
        )
        return dict(record) if record else None

    async def save(self, user: dict) -> None:
        now = datetime.now(UTC)
        await database.execute(
            """
            INSERT INTO users (user_id, language, registered_at, last_seen, is_active, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                language = EXCLUDED.language,
                last_seen = EXCLUDED.last_seen,
                is_active = EXCLUDED.is_active,
                status = EXCLUDED.status,
                updated_at = NOW()
            """,
            user["user_id"],
            user.get("language", "es"),
            user.get("registered_at", now),
            user.get("last_seen", now),
            user.get("is_active", True),
            user.get("status", "non_permitted"),
        )

    async def get_all(self) -> list[dict]:
        records = await database.fetch("SELECT * FROM users ORDER BY registered_at DESC")
        return [dict(r) for r in records]

    async def get_by_status(self, status: str) -> list[dict]:
        records = await database.fetch(
            "SELECT * FROM users WHERE status = $1 ORDER BY registered_at DESC",
            status,
        )
        return [dict(r) for r in records]

    async def update_last_seen(self, user_id: int) -> None:
        await database.execute(
            "UPDATE users SET last_seen = $1, is_active = TRUE WHERE user_id = $2",
            datetime.now(UTC),
            user_id,
        )

    async def get_user_status(self, user_id: int) -> str | None:
        record = await database.fetchrow("SELECT status FROM users WHERE user_id = $1", user_id)
        return record["status"] if record else None

    async def request_access(self, user_id: int) -> bool:
        now = datetime.now(UTC)
        result = await database.execute(
            """
            UPDATE users
            SET status = 'pending', requested_at = $2
            WHERE user_id = $1
            """,
            user_id,
            now,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def approve_user(self, user_id: int) -> bool:
        result = await database.execute(
            "UPDATE users SET status = 'approved' WHERE user_id = $1",
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def deny_user(self, user_id: int) -> bool:
        result = await database.execute(
            """
            UPDATE users
            SET status = 'non_permitted', requested_at = NULL
            WHERE user_id = $1
            """,
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def make_admin(self, user_id: int) -> bool:
        result = await database.execute(
            "UPDATE users SET status = 'admin' WHERE user_id = $1",
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0


class PostgreSQLUserWatchlistRepository:
    """Repository for user watchlists (crypto coins)."""

    async def get_coins(self, user_id: int) -> list[str]:
        """Get user's watchlist coins."""
        record = await database.fetchrow(
            "SELECT coins FROM user_watchlists WHERE user_id = $1",
            user_id,
        )
        return record["coins"] if record and record["coins"] else []

    async def set_coins(self, user_id: int, coins: list[str]) -> None:
        """Set user's watchlist coins."""
        await database.execute(
            """
            INSERT INTO user_watchlists (user_id, coins, updated_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                coins = EXCLUDED.coins,
                updated_at = EXCLUDED.updated_at
            """,
            user_id,
            coins,
            datetime.now(UTC),
        )

    async def add_coin(self, user_id: int, coin: str) -> None:
        """Add a coin to user's watchlist."""
        current = await self.get_coins(user_id)
        if coin not in current:
            current.append(coin)
            await self.set_coins(user_id, current)

    async def remove_coin(self, user_id: int, coin: str) -> None:
        """Remove a coin from user's watchlist."""
        current = await self.get_coins(user_id)
        if coin in current:
            current.remove(coin)
            await self.set_coins(user_id, current)


class PostgreSQLUserPreferenceRepository:
    """Repository for user preferences."""

    async def get_hbd_alerts(self, user_id: int) -> bool:
        """Get user's HBD alerts preference."""
        record = await database.fetchrow(
            "SELECT hbd_alerts FROM user_preferences WHERE user_id = $1",
            user_id,
        )
        return record["hbd_alerts"] if record else False

    async def set_hbd_alerts(self, user_id: int, enabled: bool) -> None:
        """Set user's HBD alerts preference."""
        await database.execute(
            """
            INSERT INTO user_preferences (user_id, hbd_alerts, updated_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                hbd_alerts = EXCLUDED.hbd_alerts,
                updated_at = EXCLUDED.updated_at
            """,
            user_id,
            enabled,
            datetime.now(UTC),
        )

    async def get_alert_interval(self, user_id: int) -> float:
        """Get user's alert interval in hours."""
        record = await database.fetchrow(
            "SELECT alerta_interval_hours FROM user_preferences WHERE user_id = $1",
            user_id,
        )
        return float(record["alerta_interval_hours"]) if record else 1.0

    async def set_alert_interval(self, user_id: int, hours: float) -> None:
        """Set user's alert interval in hours."""
        await database.execute(
            """
            INSERT INTO user_preferences (user_id, alerta_interval_hours, updated_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                alerta_interval_hours = EXCLUDED.alerta_interval_hours,
                updated_at = EXCLUDED.updated_at
            """,
            user_id,
            hours,
            datetime.now(UTC),
        )


class PostgreSQLUserUsageStatsRepository:
    """Repository for daily user usage statistics."""

    async def get_today_stats(self, user_id: int) -> dict:
        """Get today's usage statistics."""
        today = datetime.now(UTC).date()
        record = await database.fetchrow(
            """
            SELECT ver_count, ta_count, temp_changes_count, btc_count, graf_count
            FROM user_usage_stats
            WHERE user_id = $1 AND usage_date = $2
            """,
            user_id,
            today,
        )
        if not record:
            return {
                "ver": 0,
                "ta": 0,
                "temp_changes": 0,
                "btc": 0,
                "graf": 0,
            }
        return {
            "ver": record["ver_count"] or 0,
            "ta": record["ta_count"] or 0,
            "temp_changes": record["temp_changes_count"] or 0,
            "btc": record["btc_count"] or 0,
            "graf": record["graf_count"] or 0,
        }

    async def increment_stat(self, user_id: int, stat_type: str) -> None:
        """Increment a specific stat counter for today."""
        today = datetime.now(UTC).date()
        column_map = {
            "ver": "ver_count",
            "ta": "ta_count",
            "temp_changes": "temp_changes_count",
            "btc": "btc_count",
            "graf": "graf_count",
        }
        column = column_map.get(stat_type)
        if not column:
            return

        await database.execute(
            f"""
            INSERT INTO user_usage_stats (user_id, usage_date, {column})
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id, usage_date) DO UPDATE SET
                {column} = user_usage_stats.{column} + 1,
                updated_at = NOW()
            """,
            user_id,
            today,
        )

    async def get_historical_stats(self, user_id: int, days: int = 30) -> list[dict]:
        """Get historical usage statistics for the last N days."""
        records = await database.fetch(
            """
            SELECT usage_date, ver_count, ta_count, temp_changes_count, btc_count, graf_count
            FROM user_usage_stats
            WHERE user_id = $1 AND usage_date >= $2
            ORDER BY usage_date DESC
            """,
            user_id,
            datetime.now(UTC).date() - __import__("datetime").timedelta(days=days),
        )
        return [
            {
                "date": r["usage_date"],
                "ver": r["ver_count"] or 0,
                "ta": r["ta_count"] or 0,
                "temp_changes": r["temp_changes_count"] or 0,
                "btc": r["btc_count"] or 0,
                "graf": r["graf_count"] or 0,
            }
            for r in records
        ]
