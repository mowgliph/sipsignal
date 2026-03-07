from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal


@dataclass
class ActiveTrade:
    id: int | None
    signal_id: int
    direction: str
    entry_price: float
    tp1_level: float
    sl_level: float
    created_at: datetime
    updated_at: datetime
    status: Literal["ABIERTO"] = "ABIERTO"

    def is_open(self) -> bool:
        return self.status == "ABIERTO"

    def move_sl_to_breakeven(self) -> None:
        self.sl_level = self.entry_price
        self.updated_at = datetime.now(UTC)
