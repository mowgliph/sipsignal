from dataclasses import dataclass


@dataclass(frozen=True)
class UserConfig:
    user_id: int
    capital_total: float = 1000.0
    risk_percent: float = 1.0
    max_drawdown_percent: float = 5.0
    direction: str = "LONG"
    timeframe_primary: str = "15m"
    setup_completed: bool = False

    def max_drawdown_usdt(self) -> float:
        return self.capital_total * (self.max_drawdown_percent / 100)

    def warning_threshold_usdt(self) -> float:
        return self.max_drawdown_usdt() * 0.5
