# Critical Production Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Fix three critical production errors: dual storage (JSON+PostgreSQL), mock database returning None, and BinanceAdapter code duplication.

**Architecture:** Consolidate user data into PostgreSQL via repository pattern, replace mock Database with real ActiveTradeRepository injection, and merge duplicate Binance adapters into single implementation.

**Tech Stack:** Python 3.13+, asyncpg, SQLAlchemy, pytest, dependency injection container.

---

## Task 1: Extend UserRepository Protocol

**Files:**
- Modify: `bot/domain/ports/repositories.py`
- Test: `tests/unit/test_user_repository.py`

**Step 1: Add UserRepository protocol**

Edit `bot/domain/ports/repositories.py` and add:

```python
class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> dict | None:
        """Get user by ID."""
        ...

    @abstractmethod
    async def save(self, user: dict) -> None:
        """Save or update user."""
        ...

    @abstractmethod
    async def get_all(self) -> list[dict]:
        """Get all users."""
        ...

    @abstractmethod
    async def get_by_status(self, status: str) -> list[dict]:
        """Get users by status filter."""
        ...

    @abstractmethod
    async def update_last_seen(self, user_id: int) -> None:
        """Update user last_seen timestamp."""
        ...

    @abstractmethod
    async def get_user_status(self, user_id: int) -> str | None:
        """Get user access status."""
        ...

    @abstractmethod
    async def request_access(self, user_id: int) -> bool:
        """Mark user as pending access request."""
        ...

    @abstractmethod
    async def approve_user(self, user_id: int) -> bool:
        """Approve user access."""
        ...

    @abstractmethod
    async def deny_user(self, user_id: int) -> bool:
        """Deny user access."""
        ...

    @abstractmethod
    async def make_admin(self, user_id: int) -> bool:
        """Make user an admin."""
        ...
```

**Step 2: Run linting**

```bash
ruff check bot/domain/ports/repositories.py
ruff format bot/domain/ports/repositories.py
```

Expected: PASS with no errors

**Step 3: Commit**

```bash
git add bot/domain/ports/repositories.py
git commit -m "feat: add UserRepository protocol to domain ports"
```

---

## Task 2: Implement PostgreSQLUserRepository

**Files:**
- Modify: `bot/infrastructure/database/user_repositories.py`
- Test: `tests/integration/test_user_repository.py`

**Step 1: Add PostgreSQLUserRepository implementation**

Edit `bot/infrastructure/database/user_repositories.py` and add:

```python
from bot.domain.ports.repositories import UserRepository


class PostgreSQLUserRepository(UserRepository):
    async def get(self, user_id: int) -> dict | None:
        record = await database.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id,
        )
        return dict(record) if record else None

    async def save(self, user: dict) -> None:
        now = datetime.now()
        await database.execute(
            """
            INSERT INTO users (user_id, language, registered_at, last_seen, is_active, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                language = EXCLUDED.language,
                last_seen = EXCLUDED.last_seen,
                is_active = EXCLUDED.is_active,
                status = EXCLUDED.status,
                updated_at = NOW()
            """,
            user["user_id"],
            user.get("language", "es"),
            user.get("registered_at", now),
            user.get("last_seen", now),
            user.get("is_active", True),
            user.get("status", "non_permitted"),
        )

    async def get_all(self) -> list[dict]:
        records = await database.fetch("SELECT * FROM users ORDER BY registered_at DESC")
        return [dict(r) for r in records]

    async def get_by_status(self, status: str) -> list[dict]:
        records = await database.fetch(
            "SELECT * FROM users WHERE status = $1 ORDER BY registered_at DESC",
            status,
        )
        return [dict(r) for r in records]

    async def update_last_seen(self, user_id: int) -> None:
        await database.execute(
            "UPDATE users SET last_seen = $1, is_active = TRUE WHERE user_id = $2",
            datetime.now(),
            user_id,
        )

    async def get_user_status(self, user_id: int) -> str | None:
        record = await database.fetchrow("SELECT status FROM users WHERE user_id = $1", user_id)
        return record["status"] if record else None

    async def request_access(self, user_id: int) -> bool:
        now = datetime.now()
        result = await database.execute(
            """
            UPDATE users
            SET status = 'pending', requested_at = $2
            WHERE user_id = $1
            """,
            user_id,
            now,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def approve_user(self, user_id: int) -> bool:
        result = await database.execute(
            "UPDATE users SET status = 'approved' WHERE user_id = $1",
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def deny_user(self, user_id: int) -> bool:
        result = await database.execute(
            """
            UPDATE users
            SET status = 'non_permitted', requested_at = NULL
            WHERE user_id = $1
            """,
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0

    async def make_admin(self, user_id: int) -> bool:
        result = await database.execute(
            "UPDATE users SET status = 'admin' WHERE user_id = $1",
            user_id,
        )
        return result.startswith("UPDATE") and int(result.split()[-1]) > 0
```

**Step 2: Add import at top of file**

```python
from datetime import datetime
from bot.domain.ports.repositories import UserRepository
```

**Step 3: Run linting**

```bash
ruff check bot/infrastructure/database/user_repositories.py
ruff format bot/infrastructure/database/user_repositories.py
```

Expected: PASS

**Step 4: Commit**

```bash
git add bot/infrastructure/database/user_repositories.py
git commit -m "feat: implement PostgreSQLUserRepository with full CRUD"
```

---

## Task 3: Update DI Container with UserRepository

**Files:**
- Modify: `bot/container.py`

**Step 1: Read container.py to understand current structure**

```bash
cat bot/container.py
```

**Step 2: Register UserRepository**

Add to container.py:

```python
from bot.infrastructure.database.user_repositories import PostgreSQLUserRepository

# In the Container class __init__ or setup method:
self.user_repository = PostgreSQLUserRepository()
```

**Step 3: Run linting**

```bash
ruff check bot/container.py
ruff format bot/container.py
```

**Step 4: Commit**

```bash
git add bot/container.py
git commit -m "feat: register UserRepository in DI container"
```

---

## Task 4: Migrate general.py Handlers to PostgreSQL

**Files:**
- Modify: `bot/handlers/general.py`
- Test: `tests/unit/handlers/test_general.py`

**Step 1: Update imports in general.py**

Replace:
```python
from bot.utils.file_manager import (
    check_feature_access,
    load_last_prices_status,
    obtener_datos_usuario,
    obtener_monedas_usuario,
    registrar_uso_comando,
)
```

With:
```python
from bot.utils.file_manager import (
    check_feature_access,
    load_last_prices_status,
    registrar_uso_comando,
)
```

**Step 2: Update obtener_datos_usuario calls**

Replace calls to `obtener_datos_usuario(user_id)` with repository access via context:

```python
# In commands that need user data:
container = context.bot_data["container"]
user_repo = container.user_repository
user_data = await user_repo.get(user_id)
```

**Step 3: Run linting**

```bash
ruff check bot/handlers/general.py
ruff format bot/handlers/general.py
```

**Step 4: Commit**

```bash
git add bot/handlers/general.py
git commit -m "refactor: migrate general.py to use UserRepository"
```

---

## Task 5: Fix Mock Database in strategy_engine.py

**Files:**
- Modify: `bot/trading/strategy_engine.py`
- Test: `tests/unit/trading/test_strategy_engine.py`

**Step 1: Remove Database mock class**

Delete lines 42-51 (the entire `class Database:` block).

**Step 2: Update run_cycle signature**

Replace:
```python
async def run_cycle(config: UserConfig) -> SignalDTO | None:
```

With:
```python
from bot.domain.ports.repositories import ActiveTradeRepository

async def run_cycle(
    config: UserConfig,
    trade_repo: ActiveTradeRepository
) -> SignalDTO | None:
```

**Step 3: Replace Database.fetch_active_trade() call**

Replace:
```python
active = await Database.fetch_active_trade()
```

With:
```python
active_trade = await trade_repo.get_active()
if active_trade:
    logger.info(f"Active trade exists: {active_trade.id}")
    return None
```

**Step 4: Update run_cycle call sites**

Find all calls to `run_cycle()` and inject the repository:

```python
# Example in scheduler or handler:
trade_repo = container.active_trade_repository
signal = await run_cycle(config, trade_repo)
```

**Step 5: Run linting**

```bash
ruff check bot/trading/strategy_engine.py
ruff format bot/trading/strategy_engine.py
```

**Step 6: Commit**

```bash
git add bot/trading/strategy_engine.py
git commit -m "fix: replace mock Database with real ActiveTradeRepository injection"
```

---

## Task 6: Consolidate BinanceAdapter

**Files:**
- Modify: `bot/infrastructure/binance/binance_adapter.py`
- Delete: `bot/trading/data_fetcher.py`
- Modify: All files importing from data_fetcher

**Step 1: Add missing methods to BinanceAdapter**

Edit `bot/infrastructure/binance/binance_adapter.py` and add:

```python
async def get_current_price(self, symbol: str) -> float:
    """Get current price for symbol."""
    url = f"{BINANCE_BASE_URL}/ticker/24hr"
    params = {"symbol": symbol.upper()}

    data = await self._request_with_retry(url, params)

    bid = float(data["bidPrice"])
    ask = float(data["askPrice"])
    return (bid + ask) / 2

async def fetch_multiple_timeframes(
    self, symbol: str, intervals: list[str] | None = None
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV for multiple timeframes."""
    if intervals is None:
        intervals = ["15m", "1h", "4h"]

    tasks = [self.get_ohlcv(symbol, interval) for interval in intervals]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    data = {}
    for interval, result in zip(intervals, results, strict=False):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {interval}: {result}")
            data[interval] = pd.DataFrame()
        else:
            data[interval] = result

    return data
```

**Step 2: Add asyncio import**

Add at top of file:
```python
import asyncio
```

**Step 3: Update all imports**

Find and replace in all files:

```bash
# Find all files importing from data_fetcher
grep -r "from bot.trading.data_fetcher import" bot/
```

Replace each occurrence:
```python
# Before
from bot.trading.data_fetcher import BinanceDataFetcher

# After
from bot.infrastructure.binance.binance_adapter import BinanceAdapter
```

**Files to update:**
- `bot/trading/strategy_engine.py`
- `bot/trading/price_monitor.py`
- `bot/handlers/chart_handler.py`
- Any other file using BinanceDataFetcher

**Step 4: Delete data_fetcher.py**

```bash
rm bot/trading/data_fetcher.py
```

**Step 5: Run linting**

```bash
ruff check bot/infrastructure/binance/binance_adapter.py
ruff format bot/infrastructure/binance/binance_adapter.py
ruff check bot/trading/
ruff format bot/trading/
```

**Step 6: Commit**

```bash
git add bot/infrastructure/binance/binance_adapter.py bot/trading/
git rm bot/trading/data_fetcher.py
git commit -m "refactor: consolidate BinanceAdapter, remove duplicate data_fetcher.py"
```

---

## Task 7: Update DI Container with BinanceAdapter

**Files:**
- Modify: `bot/container.py`

**Step 1: Register BinanceAdapter as MarketDataPort**

Add to container.py:

```python
from bot.infrastructure.binance.binance_adapter import BinanceAdapter
from bot.domain.ports.market_data_port import MarketDataPort

# In Container class:
self.market_data: MarketDataPort = BinanceAdapter()
```

**Step 2: Update strategy_engine to use MarketDataPort**

If strategy_engine uses BinanceAdapter directly, update to use the port:

```python
async def run_cycle(
    config: UserConfig,
    trade_repo: ActiveTradeRepository,
    market_data: MarketDataPort,  # ← Use port instead of concrete class
) -> SignalDTO | None:
    df = await market_data.get_ohlcv("BTCUSDT", config.timeframe, 200)
```

**Step 3: Run linting**

```bash
ruff check bot/container.py
ruff format bot/container.py
```

**Step 4: Commit**

```bash
git add bot/container.py bot/trading/strategy_engine.py
git commit -m "feat: inject MarketDataPort via DI container"
```

---

## Task 8: Write Unit Tests

**Files:**
- Create: `tests/unit/test_user_repository.py`
- Create: `tests/unit/trading/test_strategy_engine.py`
- Create: `tests/unit/infrastructure/test_binance_adapter.py`

**Step 1: Write UserRepository tests**

Create `tests/unit/test_user_repository.py`:

```python
"""Unit tests for UserRepository protocol."""

import pytest
from bot.domain.ports.repositories import UserRepository


def test_user_repository_is_abstract():
    """Verify UserRepository cannot be instantiated directly."""
    with pytest.raises(TypeError):
        UserRepository()


class MockUserRepository(UserRepository):
    """Mock implementation for testing."""

    async def get(self, user_id: int) -> dict | None:
        return {"user_id": user_id, "language": "es"}

    async def save(self, user: dict) -> None:
        pass

    async def get_all(self) -> list[dict]:
        return []

    async def get_by_status(self, status: str) -> list[dict]:
        return []

    async def update_last_seen(self, user_id: int) -> None:
        pass

    async def get_user_status(self, user_id: int) -> str | None:
        return "approved"

    async def request_access(self, user_id: int) -> bool:
        return True

    async def approve_user(self, user_id: int) -> bool:
        return True

    async def deny_user(self, user_id: int) -> bool:
        return True

    async def make_admin(self, user_id: int) -> bool:
        return True


def test_mock_user_repository_implementation():
    """Verify mock implementation satisfies protocol."""
    repo = MockUserRepository()
    assert isinstance(repo, UserRepository)
```

**Step 2: Write strategy_engine tests**

Create `tests/unit/trading/test_strategy_engine.py`:

```python
"""Unit tests for strategy engine with active trade check."""

import pytest
from datetime import datetime
from bot.trading.strategy_engine import run_cycle, UserConfig
from bot.domain.active_trade import ActiveTrade


class MockActiveTradeRepository:
    """Mock trade repository."""

    def __init__(self, active_trade: ActiveTrade | None = None):
        self._active_trade = active_trade

    async def get_active(self) -> ActiveTrade | None:
        return self._active_trade


@pytest.mark.asyncio
async def test_run_cycle_blocks_signal_when_trade_active():
    """Verify no signal generated when active trade exists."""
    config = UserConfig(timeframe="4h")

    # Create mock active trade
    active_trade = ActiveTrade(
        id=1,
        signal_id=100,
        direction="LONG",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49000.0,
        status="ABIERTO",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    trade_repo = MockActiveTradeRepository(active_trade=active_trade)

    # Should return None when trade is active
    result = await run_cycle(config, trade_repo)
    assert result is None


@pytest.mark.asyncio
async def test_run_cycle_allows_signal_when_no_trade():
    """Verify signal can be generated when no active trade."""
    config = UserConfig(timeframe="4h")
    trade_repo = MockActiveTradeRepository(active_trade=None)

    # Note: This will still return None if no signal conditions met
    # Full signal testing requires mocking market data
    result = await run_cycle(config, trade_repo)
    # Result may be None if no signal detected, but function should not crash
    assert result is None or hasattr(result, 'direction')
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_user_repository.py -v
pytest tests/unit/trading/test_strategy_engine.py -v
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/unit/
git commit -m "test: add unit tests for UserRepository and strategy_engine"
```

---

## Task 9: Run Full Test Suite

**Files:**
- All test files

**Step 1: Run full test suite**

```bash
pytest --cov=. --cov-report=term-missing
```

Expected: All tests PASS, coverage > 70%

**Step 2: Run linting on entire codebase**

```bash
ruff check .
ruff format --check .
```

Expected: No errors

**Step 3: Fix any issues**

If linting fails, fix issues:

```bash
ruff check . --fix
ruff format .
```

**Step 4: Commit**

```bash
git add .
git commit -m "chore: ensure all tests pass and linting clean"
```

---

## Task 10: Create GitHub Issue

**Files:**
- GitHub issue (external)

**Step 1: Create GitHub issue with template**

Title: `CRITICAL: Fix dual storage, mock database, and code duplication`

Body:

```markdown
## Critical Production Issues

### Issue 1: Dual Storage (JSON + PostgreSQL)
**Problem:** User data stored in both `file_manager.py` (JSON) and PostgreSQL, creating data inconsistency.

**Impact:**
- Race conditions between storage systems
- Conflicting sources of truth
- Data corruption risk

**Solution:**
- Implement `UserRepository` protocol in `domain/ports/repositories.py`
- Migrate all handlers to use PostgreSQL via repository pattern
- Keep `file_manager.py` read-only for legacy features

### Issue 2: Mock Database in strategy_engine.py
**Problem:** `Database.fetch_active_trade()` always returns `None`.

**Impact:**
- Bot emits duplicate signals to users
- Users receive conflicting trading recommendations
- Loss of trust in bot reliability

**Solution:**
- Remove mock `Database` class
- Inject `ActiveTradeRepository` via DI
- Use real `get_active()` method from PostgreSQL

### Issue 3: BinanceAdapter Duplication
**Problem:** ~80% code duplication between `trading/data_fetcher.py` and `infrastructure/binance/binance_adapter.py`.

**Impact:**
- Maintenance burden
- Bug fixes must be applied twice
- Violates DRY principle

**Solution:**
- Consolidate into `BinanceAdapter` (infrastructure layer)
- Delete `trading/data_fetcher.py`
- Update all imports to use single implementation

## Implementation Plan

See: `docs/plans/2026-03-08-critical-fixes-design.md`

## Acceptance Criteria

- [ ] All user operations go through PostgreSQL
- [ ] No duplicate signals when trade is active
- [ ] Single Binance adapter implementation
- [ ] All tests pass (`pytest`)
- [ ] Linting passes (`ruff check .`)
- [ ] No breaking changes to existing functionality

## Files Modified

- `bot/domain/ports/repositories.py` - Added UserRepository protocol
- `bot/infrastructure/database/user_repositories.py` - Implemented PostgreSQLUserRepository
- `bot/trading/strategy_engine.py` - Removed mock Database, injected repository
- `bot/infrastructure/binance/binance_adapter.py` - Consolidated implementation
- `bot/container.py` - Updated DI registrations
- `bot/handlers/general.py` - Migrated to UserRepository

## Files Deleted

- `bot/trading/data_fetcher.py`
```

**Step 2: Link issue to PR when created**

---

## Task 11: Verification and Documentation

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Update CHANGELOG.md**

Add to `[Unreleased]` section:

```markdown
### Fixed
- CRITICAL: Dual storage architecture - migrated user data to PostgreSQL only (#ISSUE_NUMBER)
- CRITICAL: Mock database in strategy_engine.py causing duplicate signals (#ISSUE_NUMBER)
- CRITICAL: BinanceAdapter code duplication - consolidated into single implementation (#ISSUE_NUMBER)

### Changed
- UserRepository protocol now enforced via dependency injection
- ActiveTradeRepository injected into strategy engine for real trade lookup
- BinanceAdapter is now the single source for market data
```

**Step 2: Run verification commands**

```bash
# Verify no imports of deleted file
grep -r "from bot.trading.data_fetcher" bot/ || echo "✅ No references to deleted file"

# Verify mock Database class removed
grep -r "class Database:" bot/trading/ || echo "✅ Mock Database class removed"

# Verify UserRepository usage
grep -r "UserRepository" bot/ | wc -l
```

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG with critical fixes"
```

---

## Testing Checklist

Run after all tasks complete:

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Linting
ruff check . --fix
ruff format .

# Type checking (if using mypy/pyright)
mypy bot/

# Run bot manually
python bot/main.py
```

Expected: All tests pass, no linting errors, bot starts successfully.

---

## Rollback Instructions

If deployment fails:

```bash
# Rollback to previous commit
git revert HEAD~11..HEAD

# Or reset to specific commit
git reset --hard <commit-hash-before-changes>

# Restore data_fetcher.py from git history
git checkout HEAD~11 -- bot/trading/data_fetcher.py
```

---

## Skills Required

- @python-testing-patterns - For unit test structure
- @python-design-patterns - For repository pattern implementation
- @async-python-patterns - For async/await patterns
- @error-handling-patterns - For proper exception handling
