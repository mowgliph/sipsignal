from datetime import datetime

import asyncpg

from bot.core import database
from bot.domain.ports.repositories import SignalRepository
from bot.domain.signal import Signal


def _record_to_signal(record: asyncpg.Record) -> Signal:
    def safe_get(key: str, default=None):
        try:
            return record[key]
        except (KeyError, IndexError):
            return default

    return Signal(
        id=record["id"],
        direction=record["direction"],
        entry_price=float(record["entry_price"]),
        tp1_level=float(record["tp1_level"]),
        sl_level=float(record["sl_level"]),
        rr_ratio=float(record["rr_ratio"]),
        atr_value=float(record["atr_value"]),
        supertrend_line=float(record["atr_value"]),
        timeframe=record["timeframe"],
        detected_at=record["detected_at"],
        status=record["status"],
        result=safe_get("result"),
        pnl_usdt=float(safe_get("pnl_usdt")) if safe_get("pnl_usdt") else None,
    )


class PostgreSQLSignalRepository(SignalRepository):
    async def save(self, signal: Signal) -> Signal:
        signal_id: int = await database.fetchval(
            """
            INSERT INTO signals (
                direction, entry_price, tp1_level, sl_level, rr_ratio,
                atr_value, timeframe, detected_at, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            signal.direction,
            signal.entry_price,
            signal.tp1_level,
            signal.sl_level,
            signal.rr_ratio,
            signal.atr_value,
            signal.timeframe,
            signal.detected_at,
            signal.status,
        )
        signal.id = signal_id
        return signal

    async def get_by_id(self, signal_id: int) -> Signal | None:
        record = await database.fetchrow(
            "SELECT * FROM signals WHERE id = $1",
            signal_id,
        )
        if record is None:
            return None
        return _record_to_signal(record)

    async def get_recent(self, limit: int) -> list[Signal]:
        records = await database.fetch(
            "SELECT * FROM signals ORDER BY detected_at DESC LIMIT $1",
            limit,
        )
        return [_record_to_signal(record) for record in records]

    async def get_by_detected_at_and_status(
        self, detected_at: datetime, status: str
    ) -> Signal | None:
        record = await database.fetchrow(
            "SELECT * FROM signals WHERE detected_at = $1 AND status = $2 ORDER BY id DESC LIMIT 1",
            detected_at,
            status,
        )
        if record is None:
            return None
        return _record_to_signal(record)

    async def update_status(self, signal_id: int, status: str) -> None:
        await database.execute(
            "UPDATE signals SET status = $1, updated_at = NOW() WHERE id = $2",
            status,
            signal_id,
        )
