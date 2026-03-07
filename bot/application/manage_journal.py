from bot.domain.ports.repositories import SignalRepository
from bot.domain.signal import Signal


class ManageJournal:
    def __init__(self, signal_repo: SignalRepository):
        self._signal_repo = signal_repo

    async def get_recent(self, limit: int = 10) -> list[Signal]:
        return await self._signal_repo.get_recent(limit)

    async def get_by_id(self, signal_id: int) -> Signal | None:
        return await self._signal_repo.get_by_id(signal_id)

    async def mark_taken(self, signal_id: int) -> None:
        await self._signal_repo.update_status(signal_id, "TOMADA")

    async def mark_skipped(self, signal_id: int) -> None:
        await self._signal_repo.update_status(signal_id, "CANCELADA")

    async def mark_closed(self, signal_id: int) -> None:
        await self._signal_repo.update_status(signal_id, "CERRADA")
