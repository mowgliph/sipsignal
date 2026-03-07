# Signal Entity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear la entidad `Signal` en el dominio puro del sistema

**Architecture:** Dataclass simple en `bot/domain/signal.py` sin dependencias externas

**Tech Stack:** Python stdlib (dataclasses, datetime)

---

### Task 1: Create Signal entity

**Files:**
- Create: `bot/domain/signal.py`

**Step 1: Create the entity file**

```python
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

    def is_valid(self) -> bool:
        if self.direction not in ("LONG", "SHORT"):
            return False
        if self.rr_ratio < 1.0:
            return False
        if self.entry_price <= 0:
            return False
        return True

    def risk_amount(self, capital: float, risk_percent: float) -> float:
        return capital * (risk_percent / 100)

    def position_size(self, capital: float, risk_percent: float) -> float:
        return self.risk_amount(capital, risk_percent) / abs(self.entry_price - self.sl_level)
```

**Step 2: Update domain __init__.py**

Modify: `bot/domain/__init__.py`

```python
from bot.domain.signal import Signal

__all__ = ["Signal"]
```

**Step 3: Run linter**

Run: `ruff check bot/domain/signal.py bot/domain/__init__.py`

Expected: No errors

**Step 4: Commit**

```bash
git add bot/domain/signal.py bot/domain/__init__.py
git commit -m "feat: add Signal entity to domain layer"
```
