## 🔴 Critical Production Issues

**Priority:** P0 - Immediate attention required
**Impact:** Data inconsistency, duplicate signals, maintenance burden

---

## Issue 1: Dual Storage Active (JSON + PostgreSQL)

### Problem
User data is stored in both `file_manager.py` (JSON files) and PostgreSQL, with handlers mixing both sources.

**Files affected:**
- `bot/utils/file_manager.py` - JSON storage
- `bot/db/users.py` - PostgreSQL operations (underutilized)
- `bot/handlers/general.py` - Uses JSON (`cargar_usuarios()`)
- `bot/handlers/capital_handler.py` - Uses PostgreSQL

**Impact:**
- Race conditions between storage systems
- Conflicting sources of truth
- Data corruption risk in production
- User settings may be inconsistent across commands

### Solution
1. Implement `UserRepository` protocol in `bot/domain/ports/repositories.py`
2. Implement `PostgreSQLUserRepository` in `bot/infrastructure/database/user_repositories.py`
3. Migrate all handlers to use repository pattern via dependency injection
4. Keep `file_manager.py` read-only for legacy features (alerts, monedas) until future migration

---

## Issue 2: Mock Database in strategy_engine.py

### Problem
The `Database` class in `strategy_engine.py` returns `None` for `fetch_active_trade()`:

```python
class Database:
    @staticmethod
    async def fetch_active_trade() -> dict | None:
        return None  # ← ALWAYS RETURNS NONE
```

**Impact:**
- Bot emits duplicate signals to users when a trade is already active
- Users receive conflicting trading recommendations
- Loss of trust in bot reliability
- Potential financial losses from duplicate trades

### Solution
1. Remove mock `Database` class entirely
2. Inject `ActiveTradeRepository` via dependency injection
3. Use real `get_active()` method from PostgreSQL repository
4. Block signal generation when active trade exists

---

## Issue 3: BinanceAdapter Code Duplication

### Problem
~80% code duplication between two files:

| File | Class | Lines |
|------|-------|-------|
| `bot/trading/data_fetcher.py` | `BinanceDataFetcher` | ~180 |
| `bot/infrastructure/binance/binance_adapter.py` | `BinanceAdapter` | ~120 |

**Identical functionality:**
- `_request_with_retry()` - Same retry logic with delays [2, 4, 8]
- `get_ohlcv()` - Same Binance API call, same DataFrame transformation
- `_exclude_open_candle()` - Same candle exclusion logic
- `close()` - Same session cleanup

**Impact:**
- Maintenance burden (bug fixes must be applied twice)
- Violates DRY principle
- Increased risk of inconsistencies

### Solution
1. Consolidate all methods into `BinanceAdapter` (infrastructure layer)
2. Delete `bot/trading/data_fetcher.py`
3. Update all imports to use single implementation
4. Register `BinanceAdapter` as `MarketDataPort` in DI container

---

## Implementation Plan

**Design document:** `docs/plans/2026-03-08-critical-fixes-design.md`
**Implementation plan:** `docs/plans/2026-03-08-critical-fixes-plan.md`

### Tasks

1. [ ] Extend `UserRepository` protocol in `domain/ports/repositories.py`
2. [ ] Implement `PostgreSQLUserRepository` in `infrastructure/database/user_repositories.py`
3. [ ] Register `UserRepository` in DI container (`container.py`)
4. [ ] Migrate `general.py` handlers to PostgreSQL
5. [ ] Remove mock `Database` class from `strategy_engine.py`
6. [ ] Inject `ActiveTradeRepository` into `run_cycle()` function
7. [ ] Consolidate `BinanceAdapter` methods
8. [ ] Delete `data_fetcher.py` and update imports
9. [ ] Write unit tests for all changes
10. [ ] Run full test suite and linting
11. [ ] Update CHANGELOG.md

---

## Acceptance Criteria

- [ ] All user operations go through PostgreSQL repository
- [ ] No duplicate signals when trade is active (verified by test)
- [ ] Single Binance adapter implementation (no `data_fetcher.py`)
- [ ] All tests pass (`pytest` returns 0 failures)
- [ ] Linting passes (`ruff check .` returns 0 errors)
- [ ] No breaking changes to existing functionality
- [ ] Bot starts and runs without errors

---

## Files to Modify

### Created
- `bot/domain/ports/repositories.py` - Added `UserRepository` protocol

### Modified
- `bot/infrastructure/database/user_repositories.py` - Implemented `PostgreSQLUserRepository`
- `bot/trading/strategy_engine.py` - Removed mock Database, injected repository
- `bot/container.py` - Updated DI registrations
- `bot/handlers/general.py` - Migrated to `UserRepository`
- `bot/infrastructure/binance/binance_adapter.py` - Consolidated implementation

### Deleted
- `bot/trading/data_fetcher.py`

---

## Testing Strategy

### Unit Tests
- `test_user_repository_is_abstract()` - Verify protocol cannot be instantiated
- `test_run_cycle_blocks_signal_when_trade_active()` - Verify duplicate signal prevention
- `test_run_cycle_allows_signal_when_no_trade()` - Verify normal operation

### Integration Tests
- `/start` command creates user in PostgreSQL
- `/capital` reads user config from PostgreSQL
- Signal cycle checks for active trades before emitting

### Verification Commands
```bash
# Verify no imports of deleted file
grep -r "from bot.trading.data_fetcher" bot/ || echo "✅ No references"

# Verify mock Database class removed
grep -r "class Database:" bot/trading/ || echo "✅ Mock removed"

# Run tests
pytest --cov=. --cov-report=term-missing

# Run linting
ruff check . --fix
ruff format .
```

---

## Rollback Plan

If issues arise during deployment:

```bash
# Rollback to previous commit
git revert HEAD~11..HEAD

# Or reset to specific commit
git reset --hard <commit-hash-before-changes>

# Restore data_fetcher.py from git history
git checkout HEAD~11 -- bot/trading/data_fetcher.py
```

---

## Related Issues

- Blocks: Any issues related to signal reliability
- Related: Any issues related to user data consistency

---

**Assigned to:** @mowgliph
**Estimated effort:** 4-6 hours
**Risk level:** High (critical production fix)
