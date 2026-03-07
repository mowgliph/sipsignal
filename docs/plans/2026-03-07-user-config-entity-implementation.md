# UserConfig Entity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear la entidad `UserConfig` en el dominio puro del sistema

**Architecture:** Dataclass simple en `bot/domain/user_config.py` sin dependencias externas

**Tech Stack:** Python stdlib (dataclasses)

---

### Task 1: Create UserConfig entity

**Files:**
- Create: `bot/domain/user_config.py`

**Step 1: Create the entity file**

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

    def max_drawdown_usdt(self) -> float:
        return self.capital_total * (self.max_drawdown_percent / 100)

    def warning_threshold_usdt(self) -> float:
        return self.max_drawdown_usdt() * 0.5
```

**Step 2: Update domain __init__.py**

Modify: `bot/domain/__init__.py`

```python
from bot.domain.signal import Signal
from bot.domain.active_trade import ActiveTrade
from bot.domain.user_config import UserConfig

__all__ = ["Signal", "ActiveTrade", "UserConfig"]
```

**Step 3: Run linter**

Run: `ruff check bot/domain/user_config.py bot/domain/__init__.py`

Expected: No errors

**Step 4: Commit**

```bash
git add bot/domain/user_config.py bot/domain/__init__.py
git commit -m "feat: add UserConfig entity to domain layer"
```
