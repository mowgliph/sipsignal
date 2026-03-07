# DrawdownState Entity Design

## Overview
Crear la entidad `DrawdownState` en el dominio puro del sistema, sin dependencias externas.

## Location
`bot/domain/drawdown_state.py`

## Structure

```python
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
```

## Methods

### apply_pnl(pnl_usdt: float, capital_total: float) -> None
- Suma `pnl_usdt` a `current_drawdown_usdt`
- Recalcula `current_drawdown_percent = (current_drawdown_usdt / capital_total) * 100`
- Si `pnl_usdt < 0`, incrementa `losses_count`

### should_warn(max_drawdown_percent: float) -> bool
```python
return abs(self.current_drawdown_percent) >= max_drawdown_percent * 0.5
```

### should_pause(max_drawdown_percent: float) -> bool
```python
return abs(self.current_drawdown_percent) >= max_drawdown_percent
```

## Dependencies
Solo stdlib: `dataclasses`, `datetime`
