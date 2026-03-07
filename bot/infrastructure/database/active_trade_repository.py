import asyncpg

from bot.core import database
from bot.domain.active_trade import ActiveTrade
from bot.domain.ports.repositories import ActiveTradeRepository


def _record_to_trade(record: asyncpg.Record) -> ActiveTrade:
    return ActiveTrade(
        id=record["id"],
        signal_id=record["signal_id"],
        direction=record["direction"],
        entry_price=float(record["entry_price"]),
        tp1_level=float(record["tp1_level"]),
        sl_level=float(record["sl_level"]),
        status=record["status"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


class PostgreSQLActiveTradeRepository(ActiveTradeRepository):
    async def save(self, trade: ActiveTrade) -> ActiveTrade:
        trade_id: int = await database.fetchval(
            """
            INSERT INTO active_trades (
                signal_id, direction, entry_price, tp1_level, sl_level, status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            trade.signal_id,
            trade.direction,
            trade.entry_price,
            trade.tp1_level,
            trade.sl_level,
            trade.status,
            trade.created_at,
            trade.updated_at,
        )
        trade.id = trade_id
        return trade

    async def get_active(self) -> ActiveTrade | None:
        record = await database.fetchrow(
            "SELECT * FROM active_trades WHERE status = 'ABIERTO' LIMIT 1",
        )
        if record is None:
            return None
        return _record_to_trade(record)

    async def update(self, trade: ActiveTrade) -> None:
        await database.execute(
            "UPDATE active_trades SET sl_level=$1, status=$2, updated_at=NOW() WHERE id=$3",
            trade.sl_level,
            trade.status,
            trade.id,
        )

    async def close(self, trade_id: int, status: str) -> None:
        await database.execute(
            "UPDATE active_trades SET status=$1, updated_at=NOW() WHERE id=$2",
            status,
            trade_id,
        )
