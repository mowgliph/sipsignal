from dataclasses import dataclass
from datetime import datetime


@dataclass
class DrawdownState:
    user_id: int
    current_drawdown_usdt: float = 0.0
    current_drawdown_percent: float = 0.0
    losses_count: int = 0
    is_paused: bool = False
    last_reset_at: datetime | None = None

    def apply_pnl(self, pnl_usdt: float, capital_total: float) -> None:
        if capital_total <= 0:
            return
        self.current_drawdown_usdt += pnl_usdt
        self.current_drawdown_percent = (self.current_drawdown_usdt / capital_total) * 100
        if pnl_usdt < 0:
            self.losses_count += 1

    def should_warn(self, max_drawdown_percent: float) -> bool:
        return abs(self.current_drawdown_percent) >= max_drawdown_percent * 0.5

    def should_pause(self, max_drawdown_percent: float) -> bool:
        return abs(self.current_drawdown_percent) >= max_drawdown_percent
