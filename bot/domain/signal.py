from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    id: int | None
    direction: str
    entry_price: float
    tp1_level: float
    sl_level: float
    rr_ratio: float
    atr_value: float
    supertrend_line: float
    timeframe: str
    detected_at: datetime
    status: str = "EMITIDA"
    result: str | None = None
    pnl_usdt: float | None = None

    def is_valid(self) -> bool:
        if self.direction not in ("LONG", "SHORT"):
            return False
        if self.rr_ratio < 1.0:
            return False
        return self.entry_price > 0

    def risk_amount(self, capital: float, risk_percent: float) -> float:
        return capital * (risk_percent / 100)

    def position_size(self, capital: float, risk_percent: float) -> float:
        risk = self.risk_amount(capital, risk_percent)
        stop_distance = abs(self.entry_price - self.sl_level)
        if stop_distance == 0:
            return 0.0
        return risk / stop_distance
