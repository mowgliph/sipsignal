# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🔴 Critical Fixes

- **Dual Storage Architecture** - Migrated user data from JSON (`file_manager.py`) to PostgreSQL only
  - Added `UserRepository` protocol to domain ports
  - Implemented `PostgreSQLUserRepository` with full CRUD operations
  - Migrated `general.py` handlers to use repository pattern
  - Fixes race conditions and data inconsistency issues

- **Mock Database in Strategy Engine** - Replaced mock `Database` class with real `ActiveTradeRepository` injection
  - Removed `Database.fetch_active_trade()` that always returned `None`
  - Injected `ActiveTradeRepository` via dependency injection
  - Prevents duplicate signal generation when trade is active
  - Fixes critical bug causing conflicting trading recommendations

- **BinanceAdapter Code Duplication** - Consolidated duplicate adapters into single implementation
  - Merged `BinanceDataFetcher` methods into `BinanceAdapter`
  - Deleted `bot/trading/data_fetcher.py` (duplicate file)
  - Updated all imports to use single `BinanceAdapter` implementation
  - Added `get_current_price()` and `fetch_multiple_timeframes()` methods

### Changed

- **Dependency Injection** - All repositories now injected via `Container` class
  - `user_repo` - User data access
  - `market_data` - Market data port (BinanceAdapter)
  - `trade_repo` - Active trade repository
- **Strategy Engine API** - `run_cycle()` now requires dependency injection:
  ```python
  await run_cycle(config, trade_repo, market_data)
  ```
- **Circular Import Resolution** - Used `TYPE_CHECKING` for deferred imports in `notifier_port.py`

### Added

- **Unit Tests**:
  - `test_user_repository.py` - Protocol and implementation tests (13 tests)
  - `test_strategy_engine.py` - Strategy engine with mock repositories (8 tests)
  - Updated legacy `test_strategy_engine.py` for new DI API (7 tests)

---

## [1.2.0] - 2026-03-08

### 🏗️ Architecture
- **Dependency Injection Container**: Centralized service management with `bot/container.py`
- **Repository Pattern**: PostgreSQL repositories for signals, active trades, user config, and drawdown
- **Port/Adapter Architecture**: Clean separation between domain logic and infrastructure

### 🚀 Added
- **Use Cases**:
  - `RunSignalCycle` - Complete signal cycle orchestration
  - `HandleDrawdown` - Drawdown management with auto-pause
  - `ManageJournal` - Journal entry management
  - `GetSignalAnalysis` - Signal technical analysis
  - `GetScenarioAnalysis` - Scenario-based analysis
- **Infrastructure Adapters**:
  - `BinanceAdapter` - Market data port implementation
  - `GroqAdapter` - AI analysis with async httpx client
  - `ScreenshotAdapter` - Chart image generation for Telegram
  - `TelegramNotifier` - Enhanced notification system
- **PostgreSQL Repositories**:
  - `PostgreSQLSignalRepository` - Signal persistence
  - `PostgreSQLActiveTradeRepository` - Active trade management
  - `PostgreSQLUserConfigRepository` - User configuration
  - `PostgreSQLDrawdownRepository` - Drawdown tracking
- **Commands**:
  - `/scenario` - Scenario-based signal analysis command
- **Security Features**:
  - `RateLimiter` - API abuse prevention
  - `AccessManager` - User access control with admin permissions
- **Pre-commit Hooks**: Automated code quality and test validation with `validate_tests.py`
- **Utilities**:
  - `decorators.py` - Reusable decorators (rate_limit, async_lock, etc.)
  - `rate_limiter.py` - Token bucket rate limiting

### 🧪 Testing
- **Unit Tests**: 20+ new test files covering domain entities, use cases, and adapters
- **Integration Tests**: Bot startup and core workflow validation
- **Test Coverage**: Comprehensive coverage for all new components

### 🔒 Security
- **Security Audit Fixes**: Rate limiting and httpx migration (closes #55)
- **AsyncIO Lock**: Replaced `threading.Lock` with `asyncio.Lock` in telemetry
- **Access Control**: User access management with admin role enforcement

### 🧹 Chore
- **Legacy Code Cleanup**: Removed unused JSON functions from `file_manager.py`
- **File Manager Refactor**: Simplified file operations with reduced complexity

### 📚 Documentation
- **QWEN.md**: Comprehensive project documentation and development workflow
- **GEMINI.md**: AI assistant documentation
- **AGENTS.md**: Agent-specific guidelines
- **Design Plans**: Security audit, pre-commit hooks, access control documentation
- **Workflow Cycle**: Formal development workflow documentation (`WORKFLOW_CYCLE.md`)

### 📊 Statistics
- **107 files changed**
- **7,216 insertions(+)**
- **1,789 deletions(-)**
- **Net: +5,427 lines**

---

## [1.1.0] - 2026-03-06

### 🚀 Added
- **CI/CD Pipeline**: Complete GitHub Actions pipeline with lint, test, build, and security stages
- **Project Configuration**: pyproject.toml with pytest, coverage, and ruff configurations
- **Linter Configuration**: .ruff.toml with comprehensive linting rules
- **Test Structure**: Basic test directory with example tests

### 🛠 Fixed
- Python version updated to 3.13

---

## [1.0.0] - 2026-03-06

### 🚀 Added
- **Signal Scheduler**: Autonomous signal scheduler integrated in bot main loop
- **Journal System**: `/journal` command with paginated history, stats, and `/active` command
- **Drawdown Manager**: Auto-pause trading when drawdown threshold is reached, `/capital` command
- **WebSocket Price Monitor**: Real-time WebSocket price monitor for TP and SL tracking
- **Setup Handler**: `/setup` capital onboarding conversation handler
- **Signal Response Handler**: Signal status tracking and migration

### 🛠 Fixed
- Cleaned dead code from removed features (BTC alerts, valerts, price alerts)
- Fixed import errors in handlers/admin.py

### ⚠️ Breaking Changes
- **Removed Alert System**: The alert system has been removed, keeping only trading signals
- **Removed /graf Command**: The chart command was removed from the system

### ✅ Tests
- All 67 tests passing
- Bot starts without critical errors

### 📦 Dependencies
- Updated various dependencies for stability

---

## [0.0.0] - 2026-01-XX (Pre-release)

### 🚀 Initial Pre-release
- Initial Telegram bot setup
- Basic trading signal generation
- Technical analysis (RSI, MACD, Bollinger Bands, EMA)
- User management and language support
- Price alerts system

---

*For older releases, please refer to the git history.*
