# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### ⚠️ Breaking Changes

- **Eliminar comando `/ver`** - Removido comando de consulta de precios de watchlist
  - Los usuarios pueden usar `/p <símbolo>` para consultar precios individuales
  - Eliminada tabla `user_price_snapshots` de la base de datos
  - Eliminados `PriceSnapshotRepository` y dependencias asociadas

## [1.4.0] - 2026-03-10

### 🔧 Critical Fixes

- **Timezone Comparison Bug** - Fixed `can't compare offset-naive and offset-aware datetimes` error
  - Signal timeout handler now converts UTC datetime to naive before DB comparison
  - Binance adapter candle filter uses naive datetime for timestamp comparison
  - Added regression test `test_signal_timeout.py` to prevent future issues
  - Files changed: `signal_response_handler.py`, `binance_adapter.py`

### 🌐 Infrastructure

- **Binance US WebSocket** - Updated default endpoint to `wss://stream.binance.us:9443/ws`
  - Better connectivity for users in United States
  - Reduced latency for North American traders

### 🧪 Testing

- **194 unit tests passing**
- New test: `test_signal_timeout.py` - Timezone comparison regression test

### Fixed
- **aiohttp 3.10+ Compatibility** - Handle removed `ping` parameter from `ClientTimeout`
  - Added version check for aiohttp 3.10+ compatibility
  - Using `heartbeat` parameter for WebSocket keepalive instead
  - Fixes WebSocket connection errors in price monitor

### Refactored
- **Import Organization** - Follow alphabetical order for telegram.ext imports
  - Moved `filters` import to correct location in `bot/main.py`
  - Consistent import style across the codebase

### Changed
- **Logger Import** - Unified logger import pattern
  - Use `bot_logger as logger` from `bot.utils.logger`
  - Consistent logging across all modules

## [1.3.0] - 2026-03-10

### 🏗️ Architecture

- **Repository Pattern Completion** - Migrated user data from JSON (`file_manager.py`) to PostgreSQL
  - Added `UserRepository` protocol to domain ports
  - Implemented `PostgreSQLUserRepository` with full CRUD operations
  - Migrated `general.py` handlers to use repository pattern
  - Fixes race conditions and data inconsistency issues

- **Dependency Injection Enhancement**
  - All repositories now injected via `Container` class
  - Strategy Engine uses real `ActiveTradeRepository` (not mock)
  - Fixes critical bug: duplicate signal generation when trade is active

- **Code Duplication Elimination**
  - Consolidated `BinanceDataFetcher` methods into `BinanceAdapter`
  - Deleted duplicate `bot/trading/data_fetcher.py`
  - Single source of truth for market data

### 🎨 Handler Modularization

- Extracted admin handlers to separate modules:
  - `admin/ad_manager.py` - Advertisement management
  - `admin/log_viewer.py` - System log viewing
  - `admin/mass_messaging.py` - Bulk messaging to users
  - `admin/user_management.py` - User administration
  - `admin/utils.py` - Shared admin utilities
- Improved maintainability and separation of concerns

### 🔧 Critical Fixes

- **Error Handling Decorator** - Centralized error management with admin alerts
  - New `handle_errors` decorator for consistent exception handling
  - Automatic admin notifications on critical errors
  - Improved logging throughout the system

- **Timezone Fixes** - Replaced 20+ naive datetimes with UTC-aware for PostgreSQL
  - Fixed DTZ005 and DTZ007 warnings
  - All timestamps now properly timezone-aware

- **Async Improvements**
  - Replaced deprecated `asyncio.get_event_loop()` with `get_running_loop()`
  - Fixed race condition in database pool initialization
  - Proper async resource lifecycle management

- **Database Migration**
  - Added `user_price_snapshots` table for price tracking
  - Alembic migration scripts included

### 📚 Documentation

- Added `GEMINI.md` for AI assistant context
- Design docs for issue #68 (error handling)
- Updated GitHub issues documentation
- Comprehensive development workflow guides

### 🧪 Testing

- **211 tests passing**
- New test suites:
  - `test_user_repository.py` - Protocol and implementation tests
  - `test_decorators.py` - Error handling decorator tests
  - Admin handler tests (ad_manager, log_viewer, mass_messaging, user_management)
- Updated strategy engine tests for new DI API

### 📊 Statistics

- **76 files changed**
- **3,971 insertions(+)**
- **7,433 deletions(-)**
- **Net: -3,462 lines** (code cleanup and consolidation)

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
