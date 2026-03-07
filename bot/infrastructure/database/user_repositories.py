from datetime import datetime

import asyncpg

from bot.core import database
from bot.domain.drawdown_state import DrawdownState
from bot.domain.ports.repositories import DrawdownRepository, UserConfigRepository
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
        now = datetime.now()
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
