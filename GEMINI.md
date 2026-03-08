# SipSignal Trading Bot - GEMINI Context

## Project Overview
SipSignal is a specialized Telegram bot for automated Bitcoin (BTC) technical analysis and trading signals. It operates 24/7 on a VPS, providing high-precision entry, take-profit (TP), and stop-loss (SL) levels.

- **Main Goal:** Automate BTC trading signals with real-time monitoring and AI-enhanced market context.
- **Key Features:**
    - Technical Analysis (RSI, MACD, Bollinger Bands, EMA, Supertrend, ASH).
    - Real-time TP/SL monitoring via WebSockets (PriceMonitor).
    - AI Market Context using Groq (Llama 3).
    - Capital Management and Drawdown control.
    - Multi-language support (ES/EN).
    - Interactive Telegram UI with callback buttons and charts.

### Tech Stack
- **Language:** Python 3.13+
- **Framework:** `python-telegram-bot` (Asynchronous)
- **Database:** PostgreSQL with SQLAlchemy ORM and Alembic migrations.
- **Data Science:** `pandas`, `pandas-ta`, `numba` (for performance).
- **AI Integration:** `groq` API.
- **Infrastructure:** Hexagonal Architecture (Domain/Infrastructure/Application/Handlers).
- **Dependency Injection:** Centralized `Container` in `bot/container.py`.

## Building and Running

### Prerequisites
- Python 3.13+
- PostgreSQL database
- Environment variables configured (see `.env`)

### Key Commands
- **Environment Setup:**
    ```bash
    python3.13 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
- **Database Migrations:**
    ```bash
    alembic upgrade head
    ```
- **Run the Bot (Development):**
    ```bash
    python bot/main.py
    ```
- **Run Tests:**
    ```bash
    pytest tests/
    ```
- **Management Script (`botctl.sh`):**
    The project includes a comprehensive management script:
    - `./botctl.sh start`: Start the bot service.
    - `./botctl.sh stop`: Stop the bot service.
    - `./botctl.sh status`: Show service status and PID.
    - `./botctl.sh logs`: View real-time logs.
    - `./botctl.sh health`: Run a full system health check.

## Development Conventions

### Architecture
The project follows a **Hexagonal / Clean Architecture** pattern:
- `bot/domain/`: Core business logic and entities (e.g., `Signal`, `UserConfig`).
- `bot/domain/ports/`: Interfaces for repositories and external services.
- `bot/infrastructure/`: Concrete implementations (Adapters) of ports (e.g., `BinanceAdapter`, `PostgreSQLSignalRepository`).
- `bot/application/`: Use cases that orchestrate domain logic (e.g., `RunSignalCycle`).
- `bot/handlers/`: Telegram command and callback handlers.
- `bot/core/`: Central configuration and shared utilities.

### Coding Style
- **Type Hinting:** Strictly required for all new code.
- **Asynchronous:** Most operations are `async/await`.
- **Dependency Injection:** Use the `Container` provided in `bot_data` for accessing services and repositories.
- **Linting:** `Ruff` is used for linting and formatting. Rules are defined in `pyproject.toml`.
- **Logging:** Use `loguru` for logging. Avoid `print()` statements.

### Testing
- **Unit Tests:** Located in `tests/unit/`. Focus on isolated logic.
- **Integration Tests:** Located in `tests/integration/`. Focus on database and API interactions.
- **E2E Tests:** Located in `tests/e2e/`.

### Database
- Models are defined using SQLAlchemy in `bot/db/models.py`.
- Pydantic models in the same file are used for data validation and DTOs.
- Always use Alembic for schema changes.

## Important Files
- `bot/main.py`: Main entry point.
- `bot/container.py`: DI Container wiring.
- `bot/core/config.py`: Configuration loading from `.env`.
- `botctl.sh`: VPS management script.
- `bot/application/run_signal_cycle.py`: The heart of the signal detection logic.
