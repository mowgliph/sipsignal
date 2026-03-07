import os
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.domain.signal import Signal
from bot.infrastructure.database.signal_repository import (
    PostgreSQLSignalRepository,
    _record_to_signal,
)


def create_signal(signal_id: int = 1, status: str = "EMITIDA") -> Signal:
    return Signal(
        id=signal_id,
        direction="LONG",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49000.0,
        rr_ratio=1.5,
        atr_value=500.0,
        supertrend_line=49900.0,
        timeframe="1h",
        detected_at=datetime.now(UTC),
        status=status,
    )


class MockRecord:
    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key: str):
        return self._data[key]


def test_record_to_signal():
    record = MockRecord(
        {
            "id": 1,
            "direction": "LONG",
            "entry_price": 50000.00,
            "tp1_level": 51000.00,
            "sl_level": 49000.00,
            "rr_ratio": 1.5,
            "atr_value": 500.00,
            "timeframe": "1h",
            "detected_at": datetime.now(UTC),
            "status": "EMITIDA",
        }
    )

    signal = _record_to_signal(record)

    assert signal.id == 1
    assert signal.direction == "LONG"
    assert signal.entry_price == 50000.0
    assert signal.tp1_level == 51000.0
    assert signal.sl_level == 49000.0
    assert signal.rr_ratio == 1.5
    assert signal.atr_value == 500.0
    assert signal.supertrend_line == 500.0
    assert signal.timeframe == "1h"
    assert signal.status == "EMITIDA"


@pytest.mark.asyncio
async def test_save_signal():
    repo = PostgreSQLSignalRepository()
    signal = create_signal()

    with patch(
        "bot.infrastructure.database.signal_repository.database.fetchval", new_callable=AsyncMock
    ) as mock_fetchval:
        mock_fetchval.return_value = 42

        result = await repo.save(signal)

        assert result.id == 42
        assert result.direction == "LONG"
        mock_fetchval.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_found():
    repo = PostgreSQLSignalRepository()
    record = MockRecord(
        {
            "id": 1,
            "direction": "LONG",
            "entry_price": 50000.00,
            "tp1_level": 51000.00,
            "sl_level": 49000.00,
            "rr_ratio": 1.5,
            "atr_value": 500.00,
            "timeframe": "1h",
            "detected_at": datetime.now(UTC),
            "status": "EMITIDA",
        }
    )

    with patch(
        "bot.infrastructure.database.signal_repository.database.fetchrow", new_callable=AsyncMock
    ) as mock_fetchrow:
        mock_fetchrow.return_value = record

        result = await repo.get_by_id(1)

        assert result is not None
        assert result.id == 1
        assert result.direction == "LONG"


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    repo = PostgreSQLSignalRepository()

    with patch(
        "bot.infrastructure.database.signal_repository.database.fetchrow", new_callable=AsyncMock
    ) as mock_fetchrow:
        mock_fetchrow.return_value = None

        result = await repo.get_by_id(999)

        assert result is None


@pytest.mark.asyncio
async def test_get_recent():
    repo = PostgreSQLSignalRepository()
    now = datetime.now(UTC)
    records = [
        MockRecord(
            {
                "id": i,
                "direction": "LONG",
                "entry_price": 50000.00,
                "tp1_level": 51000.00,
                "sl_level": 49000.00,
                "rr_ratio": 1.5,
                "atr_value": 500.00,
                "timeframe": "1h",
                "detected_at": now,
                "status": "EMITIDA",
            }
        )
        for i in range(1, 4)
    ]

    with patch(
        "bot.infrastructure.database.signal_repository.database.fetch", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = records

        result = await repo.get_recent(3)

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3


@pytest.mark.asyncio
async def test_update_status():
    repo = PostgreSQLSignalRepository()

    with patch(
        "bot.infrastructure.database.signal_repository.database.execute", new_callable=AsyncMock
    ) as mock_execute:
        await repo.update_status(1, "TOMADA")

        mock_execute.assert_called_once_with(
            "UPDATE signals SET status = $1, updated_at = NOW() WHERE id = $2",
            "TOMADA",
            1,
        )
