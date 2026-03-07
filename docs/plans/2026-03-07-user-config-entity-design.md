# UserConfig Entity Design

## Overview
Crear la entidad `UserConfig` en el dominio puro del sistema, sin dependencias externas.

## Location
`bot/domain/user_config.py`

## Structure

```python
from dataclasses import dataclass


@dataclass
class UserConfig:
    user_id: int
    capital_total: float = 1000.0
    risk_percent: float = 1.0
    max_drawdown_percent: float = 5.0
    direction: str = "LONG"
    timeframe_primary: str = "15m"
    setup_completed: bool = False
```

## Methods

### max_drawdown_usdt() -> float
```python
return self.capital_total * (self.max_drawdown_percent / 100)
```

### warning_threshold_usdt() -> float
```python
return self.max_drawdown_usdt() * 0.5
```

## Dependencies
Solo stdlib: `dataclasses`
