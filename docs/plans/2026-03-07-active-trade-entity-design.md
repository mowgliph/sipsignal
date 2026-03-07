# ActiveTrade Entity Design

## Overview
Crear la entidad `ActiveTrade` en el dominio puro del sistema, sin dependencias externas.

## Location
`bot/domain/active_trade.py`

## Structure

```python
from dataclasses import dataclass
from datetime import datetime, UTC

@dataclass
class ActiveTrade:
    id: int | None
    signal_id: int
    direction: str
    entry_price: float
    tp1_level: float
    sl_level: float
    status: str = "ABIERTO"
    created_at: datetime
    updated_at: datetime
```

## Methods

### is_open() -> bool
```python
return self.status == "ABIERTO"
```

### move_sl_to_breakeven() -> None
```python
self.sl_level = self.entry_price
self.updated_at = datetime.now(UTC)
```

## Dependencies
Solo stdlib: `dataclasses`, `datetime`
