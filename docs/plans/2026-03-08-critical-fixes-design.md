# Critical Production Fixes Design

**Date:** 2026-03-08
**Status:** Approved
**Author:** Qwen Code

---

## Executive Summary

This document describes the solution architecture for three critical production errors in SipSignal that cause data inconsistency, duplicate signals, and code maintenance issues.

### Critical Issues

1. **Dual Storage Active (JSON + PostgreSQL)** - User data stored in both `file_manager.py` (JSON) and PostgreSQL, creating data inconsistency
2. **Mock Database in strategy_engine.py** - `Database.fetch_active_trade()` always returns `None`, causing duplicate signal generation
3. **BinanceAdapter Duplication** - ~80% code duplication between `trading/data_fetcher.py` and `infrastructure/binance/binance_adapter.py`

---

## Issue 1: Dual Storage Architecture

### Current State

```
┌─────────────────────────────────────────────────────────────┐
│  Current Fragmented Architecture                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │ general.py   │────▶│ file_manager │────▶│ JSON files   │ │
│  │ ta.py        │     │ .py          │     │ (users.json) │ │
│  │ admin.py     │     │              │     │              │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │ capital_     │────▶│ db/          │────▶│ PostgreSQL   │ │
│  │ handler.py   │     │ users.py     │     │ (users)      │ │
│  │ journal_     │     │              │     │              │ │
│  │ handler.py   │     │              │     │              │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                                                              │
│  ⚠️ Result: Data inconsistency, race conditions,             │
│  conflicting sources of truth                                │
└─────────────────────────────────────────────────────────────┘
```

**Files involved:**
- `bot/utils/file_manager.py` - JSON file manager (users, alerts, subscriptions)
- `bot/db/users.py` - PostgreSQL user operations (underutilized)
- `bot/infrastructure/database/user_repositories.py` - Repository pattern (partial)
- `bot/handlers/general.py` - Uses JSON for user data
- `bot/handlers/capital_handler.py` - Uses PostgreSQL

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Unified PostgreSQL Architecture                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Handlers Layer                                       │   │
│  │  general.py, capital_handler.py, journal_handler.py   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Domain Layer (Ports)                                 │   │
│  │  bot/domain/ports/repositories.py                     │   │
│  │  - UserRepository (Protocol)                          │   │
│  │  - ActiveTradeRepository                              │   │
│  │  - SignalRepository                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Infrastructure Layer                                 │   │
│  │  bot/infrastructure/database/user_repositories.py     │   │
│  │  - PostgreSQLUserRepository                           │   │
│  │  - PostgreSQLActiveTradeRepository                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                                  │   │
│  │  - users table                                        │   │
│  │  - active_trades table                                │   │
│  │  - signals table                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ✅ Single source of truth, ACID compliance,                │
│  no data inconsistency                                       │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Strategy

**Phase 1A: Extend Repository Pattern**

Add `UserRepository` protocol to `bot/domain/ports/repositories.py`:

```python
class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> dict | None: ...

    @abstractmethod
    async def save(self, user: dict) -> None: ...

    @abstractmethod
    async def get_all(self) -> list[dict]: ...

    @abstractmethod
    async def get_by_status(self, status: str) -> list[dict]: ...
```

**Phase 1B: Consolidate User Operations**

Extend `bot/infrastructure/database/user_repositories.py` to include all operations from `bot/db/users.py`:

- `register_or_update_user()`
- `update_last_seen()`
- `get_user_status()`
- `request_access()`
- `approve_user()`
- `deny_user()`
- `make_admin()`

**Phase 1C: Migrate Handlers**

Update all handlers to use repository pattern:

```python
# Before (general.py)
from bot.utils.file_manager import obtener_datos_usuario, cargar_usuarios

user_data = obtener_datos_usuario(user_id)

# After
from bot.domain.ports.repositories import UserRepository

async def get_user_data(user_id: int, user_repo: UserRepository):
    user = await user_repo.get(user_id)
    return user
```

**Phase 1D: Legacy Compatibility**

`file_manager.py` will maintain read-only support for:
- `monedas` (coin watchlist)
- `alerts` (price alerts)
- `subscriptions` (feature subscriptions)
- `daily_usage` (usage tracking)

Until these features are migrated to PostgreSQL in a future iteration.

---

## Issue 2: Mock Database in Strategy Engine

### Current State

```python
# bot/trading/strategy_engine.py:42-51
class Database:
    """Mock database para operaciones de trade."""

    @staticmethod
    async def fetch_active_trade() -> dict | None:
        """
        Retorna el trade activo actual o None si no hay operación abierta.
        Implementación placeholder - debe integrarse con PostgreSQL.
        """
        return None  # ← ALWAYS RETURNS NONE
```

**Consequence:** The signal generation cycle never detects active trades, allowing duplicate signals to be sent to users.

### Solution

**Phase 2A: Remove Mock Class**

Delete the `Database` class from `strategy_engine.py`.

**Phase 2B: Inject Repository Dependency**

```python
# bot/trading/strategy_engine.py
from bot.domain.ports.repositories import ActiveTradeRepository

async def run_cycle(
    config: UserConfig,
    trade_repo: ActiveTradeRepository  # ← Injected dependency
) -> SignalDTO | None:
    """
    Executes a strategy analysis cycle.

    Args:
        config: User configuration for analysis
        trade_repo: Repository for active trade lookup

    Returns:
        SignalDTO if signal detected, None otherwise
    """
    fetcher = BinanceDataFetcher()
    try:
        df = await fetcher.get_ohlcv("BTCUSDT", config.timeframe, 200)
        # ... technical analysis ...

        # REAL database check
        active_trade = await trade_repo.get_active()
        if active_trade:
            logger.info(f"Active trade exists: {active_trade.id}")
            return None  # ← Block duplicate signal

        # ... signal generation logic ...

    finally:
        await fetcher.close()
```

**Phase 2C: Update DI Container**

Update `bot/container.py` to inject `ActiveTradeRepository` into the signal analysis use case.

---

## Issue 3: BinanceAdapter Duplication

### Current State

Two nearly identical classes (~80% code overlap):

| File | Class | Lines | Purpose |
|------|-------|-------|---------|
| `bot/trading/data_fetcher.py` | `BinanceDataFetcher` | ~180 | OHLCV data fetching |
| `bot/infrastructure/binance/binance_adapter.py` | `BinanceAdapter` | ~120 | OHLCV data fetching |

**Identical functionality:**
- `_request_with_retry()` - Same retry logic with delays [2, 4, 8]
- `get_ohlcv()` - Same Binance API call, same DataFrame transformation
- `_exclude_open_candle()` - Same candle exclusion logic
- `close()` - Same session cleanup

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Consolidated Binance Adapter                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Domain Port                                          │   │
│  │  bot/domain/ports/market_data_port.py                 │   │
│  │  class MarketDataPort(ABC):                           │   │
│  │      async def get_ohlcv(...) -> pd.DataFrame         │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ implements                        │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Single Implementation                                │   │
│  │  bot/infrastructure/binance/binance_adapter.py        │   │
│  │  class BinanceAdapter(MarketDataPort):                │   │
│  │      - get_ohlcv()                                    │   │
│  │      - get_current_price()                            │   │
│  │      - fetch_multiple_timeframes()                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          │ used by                           │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Consumers                                            │   │
│  │  - strategy_engine.py                                 │   │
│  │  - price_monitor.py                                   │   │
│  │  - chart_handler.py                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ✅ Single implementation, DRY principle,                   │
│  easier maintenance                                          │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Strategy

**Phase 3A: Consolidate into BinanceAdapter**

Move missing methods from `BinanceDataFetcher` to `BinanceAdapter`:
- `get_current_price()` - Already exists in data_fetcher
- `fetch_multiple_timeframes()` - Already exists in data_fetcher

**Phase 3B: Delete data_fetcher.py**

Remove `bot/trading/data_fetcher.py` entirely.

**Phase 3C: Update Imports**

Update all consumers:

```python
# Before
from bot.trading.data_fetcher import BinanceDataFetcher

fetcher = BinanceDataFetcher()
df = await fetcher.get_ohlcv("BTCUSDT", "4h")

# After
from bot.infrastructure.binance.binance_adapter import BinanceAdapter

adapter = BinanceAdapter()
df = await adapter.get_ohlcv("BTCUSDT", "4h")
```

**Phase 3D: Update DI Container**

Register `BinanceAdapter` as the singleton implementation of `MarketDataPort` in `bot/container.py`.

---

## Testing Strategy

### Unit Tests

1. **UserRepository Tests**
   - `test_user_repository_get_existing_user()`
   - `test_user_repository_get_nonexistent_user()`
   - `test_user_repository_save_new_user()`
   - `test_user_repository_update_existing_user()`

2. **Strategy Engine Tests**
   - `test_run_cycle_blocks_signal_when_trade_active()`
   - `test_run_cycle_allows_signal_when_no_trade()`

3. **BinanceAdapter Tests**
   - `test_binance_adapter_get_ohlcv()`
   - `test_binance_adapter_retry_logic()`
   - `test_binance_adapter_exclude_open_candle()`

### Integration Tests

1. **User Flow Integration**
   - `/start` command creates user in PostgreSQL
   - `/capital` reads user config from PostgreSQL
   - `/journal` reads signals from PostgreSQL

2. **Signal Cycle Integration**
   - Full signal cycle with active trade check
   - Verify no duplicate signals when trade exists

### Migration Tests

1. **Data Integrity**
   - Verify all JSON users exist in PostgreSQL after migration
   - Verify user counts match between JSON and PostgreSQL

---

## Rollback Plan

If issues arise during deployment:

1. **Issue 1 Rollback**: Revert handler changes, keep `file_manager.py` as primary
2. **Issue 2 Rollback**: Restore mock `Database` class temporarily
3. **Issue 3 Rollback**: Restore `data_fetcher.py`, revert imports

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| No data inconsistency | All user reads/writes go through PostgreSQL |
| No duplicate signals | `get_active()` returns real trade data |
| No code duplication | Single Binance adapter implementation |
| All tests pass | `pytest` returns 0 failures |
| No linting errors | `ruff check .` passes |

---

## Related Files

### Modified Files
- `bot/domain/ports/repositories.py`
- `bot/infrastructure/database/user_repositories.py`
- `bot/trading/strategy_engine.py`
- `bot/infrastructure/binance/binance_adapter.py`
- `bot/container.py`
- `bot/handlers/general.py`
- `bot/handlers/ta.py`
- `bot/handlers/user_settings.py`

### Deleted Files
- `bot/trading/data_fetcher.py`

### Unchanged (Future Migration)
- `bot/utils/file_manager.py` (legacy read support)
- `bot/db/users.py` (will be consolidated)

---

## References

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)
- [DRY Principle](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
