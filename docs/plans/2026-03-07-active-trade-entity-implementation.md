# ActiveTrade Entity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear la entidad `ActiveTrade` en el dominio puro del sistema

**Architecture:** Dataclass simple en `bot/domain/active_trade.py` sin dependencias externas

**Tech Stack:** Python stdlib (dataclasses, datetime)

---

### Task 1: Create ActiveTrade entity

**Files:**
- Create: `bot/domain/active_trade.py`

**Step 1: Create the entity file**

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

    def is_open(self) -> bool:
        return self.status == "ABIERTO"

    def move_sl_to_breakeven(self) -> None:
        self.sl_level = self.entry_price
        self.updated_at = datetime.now(UTC)
```

**Step 2: Update domain __init__.py**

Modify: `bot/domain/__init__.py`

```python
from bot.domain.signal import Signal
from bot.domain.active_trade import ActiveTrade

__all__ = ["Signal", "ActiveTrade"]
```

**Step 3: Run linter**

Run: `ruff check bot/domain/active_trade.py bot/domain/__init__.py`

Expected: No errors

**Step 4: Commit**

```bash
git add bot/domain/active_trade.py bot/domain/__init__.py
git commit -m "feat: add ActiveTrade entity to domain layer"
```
