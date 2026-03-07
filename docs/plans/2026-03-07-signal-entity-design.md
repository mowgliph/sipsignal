# Signal Entity Design

## Overview
Crear la entidad `Signal` en el dominio puro del sistema, sin dependencias externas.

## Location
`bot/domain/signal.py`

## Structure

```python
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
```

## Methods

### is_valid() -> bool
Retorna `True` si:
- `direction` es "LONG" o "SHORT"
- `rr_ratio >= 1.0`
- `entry_price > 0`

### risk_amount(capital: float, risk_percent: float) -> float
```python
return capital * (risk_percent / 100)
```

### position_size(capital: float, risk_percent: float) -> float
```python
return risk_amount(capital, risk_percent) / abs(entry_price - sl_level)
```

## Dependencies
Solo stdlib: `dataclasses`, `datetime`
