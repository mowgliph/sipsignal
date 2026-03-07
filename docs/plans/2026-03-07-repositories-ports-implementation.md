# Repositories Ports Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear los puertos de salida (interfaces) para repositorios

**Architecture:** Clases abstractas ABC con métodos async

**Tech Stack:** Python stdlib (abc), domain entities

---

### Task 1: Create repositories.py

**Files:**
- Create: `bot/domain/ports/repositories.py`

**Step 1: Create the repositories file**

```python
from abc import ABC, abstractmethod
from bot.domain.signal import Signal
from bot.domain.active_trade import ActiveTrade
from bot.domain.user_config import UserConfig
from bot.domain.drawdown_state import DrawdownState


class SignalRepository(ABC):
    @abstractmethod
    async def save(self, signal: Signal) -> Signal: ...
    
    @abstractmethod
    async def get_by_id(self, signal_id: int) -> Signal | None: ...
    
    @abstractmethod
    async def get_recent(self, limit: int) -> list[Signal]: ...
    
    @abstractmethod
    async def update_status(self, signal_id: int, status: str) -> None: ...


class ActiveTradeRepository(ABC):
    @abstractmethod
    async def save(self, trade: ActiveTrade) -> ActiveTrade: ...
    
    @abstractmethod
    async def get_active(self) -> ActiveTrade | None: ...
    
    @abstractmethod
    async def update(self, trade: ActiveTrade) -> None: ...
    
    @abstractmethod
    async def close(self, trade_id: int, status: str) -> None: ...


class UserConfigRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> UserConfig | None: ...
    
    @abstractmethod
    async def save(self, config: UserConfig) -> UserConfig: ...


class DrawdownRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> DrawdownState | None: ...
    
    @abstractmethod
    async def save(self, state: DrawdownState) -> DrawdownState: ...
    
    @abstractmethod
    async def reset(self, user_id: int) -> DrawdownState: ...
```

**Step 2: Update ports __init__.py**

Modify: `bot/domain/ports/__init__.py`

```python
from bot.domain.ports.repositories import (
    SignalRepository,
    ActiveTradeRepository,
    UserConfigRepository,
    DrawdownRepository,
)

__all__ = [
    "SignalRepository",
    "ActiveTradeRepository", 
    "UserConfigRepository",
    "DrawdownRepository",
]
```

**Step 3: Run linter**

Run: `ruff check bot/domain/ports/repositories.py bot/domain/ports/__init__.py`

**Step 4: Commit**

```bash
git add bot/domain/ports/repositories.py bot/domain/ports/__init__.py
git commit -m "feat: add repository ports to domain layer"
```
