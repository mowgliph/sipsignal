import os
import sys
from datetime import UTC, datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.application.manage_journal import ManageJournal
from bot.domain.signal import Signal


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


class MockSignalRepository:
    def __init__(self):
        self._signals = [create_signal(i) for i in range(1, 6)]
        self._update_calls = []

    async def get_recent(self, limit: int) -> list[Signal]:
        return self._signals[:limit]

    async def get_by_id(self, signal_id: int) -> Signal | None:
        for s in self._signals:
            if s.id == signal_id:
                return s
        return None

    async def update_status(self, signal_id: int, status: str) -> None:
        self._update_calls.append((signal_id, status))

    async def save(self, signal: Signal) -> Signal:
        self._signals.append(signal)
        return signal


@pytest.mark.asyncio
async def test_get_recent_returns_signals():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    result = await use_case.get_recent(limit=3)

    assert len(result) == 3
    assert result[0].id == 1
    assert result[1].id == 2
    assert result[2].id == 3


@pytest.mark.asyncio
async def test_get_by_id_returns_signal():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    result = await use_case.get_by_id(3)

    assert result is not None
    assert result.id == 3


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    result = await use_case.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_mark_taken_updates_status():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    await use_case.mark_taken(1)

    assert repo._update_calls == [(1, "TOMADA")]


@pytest.mark.asyncio
async def test_mark_skipped_updates_status():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    await use_case.mark_skipped(2)

    assert repo._update_calls == [(2, "CANCELADA")]


@pytest.mark.asyncio
async def test_mark_closed_updates_status():
    repo = MockSignalRepository()
    use_case = ManageJournal(repo)

    await use_case.mark_closed(3)

    assert repo._update_calls == [(3, "CERRADA")]
