# SipSignal Trading Bot - Instructional Context

This document serves as the primary instructional context for Gemini CLI when working on the `sipsignal` project. It outlines the project's architecture, technology stack, development standards, and key workflows.

## Project Overview
SipSignal is a specialized Telegram bot designed for automated Bitcoin (BTC/USDT) technical analysis and trading signal generation. It follows a **Hexagonal (Clean) Architecture** to ensure modularity, testability, and maintainability.

- **Core Purpose:** 24/7 market monitoring, technical analysis (TA), and real-time signal notification via Telegram.
- **Key Features:**
    - **Automated TA:** RSI, MACD, Bollinger Bands, EMA, Supertrend, ATR.
    - **AI Analysis:** Contextual market analysis using Groq AI (Llama 3).
    - **Signal Generation:** Entry opportunities with dynamic TP/SL and Risk:Reward ratios.
    - **Real-time Monitoring:** WebSocket-based monitoring for Take Profit (TP) and Stop Loss (SL) events.
    - **Drawdown Management:** Capital protection and performance tracking.

## Technology Stack
- **Language:** Python 3.13+
- **Database:** PostgreSQL (SQLAlchemy ORM, Alembic for migrations)
- **APIs:**
    - **Telegram:** `python-telegram-bot` (v20+)
    - **Market Data:** Binance API (via `python-binance` and `httpx`)
    - **AI:** Groq Cloud API (Llama 3)
- **Data Analysis:** `pandas`, `pandas_ta`
- **Testing:** `pytest`, `pytest-asyncio`, `pytest-cov`
- **Quality Assurance:** `ruff` (linting/formatting), `pre-commit` hooks

## Project Structure & Architecture
The project strictly adheres to Hexagonal Architecture:
- `bot/domain/`: Business entities (`signal.py`, `user_config.py`) and Ports (interfaces in `ports/`).
- `bot/application/`: Use cases that orchestrate business logic (`run_signal_cycle.py`, `get_signal_analysis.py`).
- `bot/infrastructure/`: Concrete implementations of ports (adapters for Binance, Groq, Telegram, and Database).
- `bot/handlers/`: Telegram command and callback handlers.
- `bot/trading/`: Core trading logic (Technical Analysis, Strategy Engine, Price Monitor).
- `bot/container.py`: Centralized Dependency Injection (DI) container.
- `bot/main.py`: Entry point for the Telegram application.

## Development Standards & Mandates
### 1. Architectural Integrity
- **Ports & Adapters:** Always define an interface (Port) in `bot/domain/ports/` before implementing a new external service (Adapter) in `bot/infrastructure/`.
- **Dependency Injection:** Use the `Container` in `bot/container.py` for injecting dependencies. Avoid direct instantiation of infrastructure classes in application or handler layers.
- **Use Cases:** Business logic must reside in the `application` layer. Handlers should only delegate to use cases.

### 2. Coding Style
- **Linter/Formatter:** `ruff` is the source of truth. Run `ruff check .` and `ruff format .` before finishing tasks.
- **Type Safety:** Use Python type hints throughout the codebase. Use Pydantic models (in `bot/db/models.py`) for data validation.
- **Async/Await:** The project is fully asynchronous. Use `async/await` and non-blocking libraries (e.g., `httpx`, `aiohttp`, `asyncpg`).

### 3. Testing Protocol
- **Location:** All tests reside in the `tests/` directory, categorized into `unit/`, `integration/`, and `e2e/`.
- **Mandate:** Every new feature or bug fix **must** include corresponding tests.
- **Execution:** Run `pytest tests/` to verify changes.

### 4. Database Migrations
- Use Alembic for any schema changes.
- **Commands:**
    - `alembic revision --autogenerate -m "description"` to create a migration.
    - `alembic upgrade head` to apply migrations.

## Key Workflows
### Autonomous Signal Cycle
Triggered by `bot/scheduler.py` or `bot/main.py`'s `post_init`:
1. `MarketDataPort` fetches OHLCV data.
2. `TechnicalAnalysis` calculates indicators.
3. `StrategyEngine` evaluates entry/exit conditions.
4. `GroqAdapter` provides AI context.
5. `TelegramNotifier` sends the alert with a chart.

### Interactive Commands
- `/signal`: Instant technical analysis.
- `/ta <symbol>`: Full technical analysis for any coin.
- `/chart [tf]`: Fetch TradingView chart for BTC.
- `/capital`: Manage drawdown and capital settings.
- `/journal`: Review signal history.

## Common Development Commands
- **Install Dependencies:** `pip install -e ".[dev]"`
- **Run Bot:** `python bot/main.py`
- **Run Tests:** `pytest tests/`
- **Lint/Format:** `ruff check . --fix` and `ruff format .`
- **Database Status:** `alembic current`

## Contextual Precedence
The instructions in this `GEMINI.md` take absolute precedence over general defaults. Always refer to the hexagonal architecture boundaries when proposing or implementing changes.
