# DrawdownState Entity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear la entidad `DrawdownState` en el dominio puro del sistema

**Architecture:** Dataclass simple en `bot/domain/drawdown_state.py` sin dependencias externas

**Tech Stack:** Python stdlib (dataclasses, datetime)

---

### Task 1: Create DrawdownState entity

**Files:**
- Create: `bot/domain/drawdown_state.py`

**Step 1: Create the entity file**

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

    def apply_pnl(self, pnl_usdt: float, capital_total: float) -> None:
        self.current_drawdown_usdt += pnl_usdt
        self.current_drawdown_percent = (self.current_drawdown_usdt / capital_total) * 100
        if pnl_usdt < 0:
            self.losses_count += 1

    def should_warn(self, max_drawdown_percent: float) -> bool:
        return abs(self.current_drawdown_percent) >= max_drawdown_percent * 0.5

    def should_pause(self, max_drawdown_percent: float) -> bool:
        return abs(self.current_drawdown_percent) >= max_drawdown_percent
```

**Step 2: Update domain __init__.py**

Modify: `bot/domain/__init__.py`

```python
from bot.domain.signal import Signal
from bot.domain.active_trade import ActiveTrade
from bot.domain.user_config import UserConfig
from bot.domain.drawdown_state import DrawdownState

__all__ = ["Signal", "ActiveTrade", "UserConfig", "DrawdownState"]
```

**Step 3: Run linter**

Run: `ruff check bot/domain/drawdown_state.py bot/domain/__init__.py`

Expected: No errors

**Step 4: Commit**

```bash
git add bot/domain/drawdown_state.py bot/domain/__init__.py
git commit -m "feat: add DrawdownState entity to domain layer"
```
