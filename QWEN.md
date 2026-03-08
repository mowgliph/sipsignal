# SipSignal Trading Bot - Project Context

## Project Overview

**SipSignal** is an intelligent Telegram bot for automated BTC trading signals and technical analysis. Built with Python 3.13+, it provides 24/7 market monitoring, real-time TP/SL tracking via WebSocket, and AI-powered market context using Groq.

### Key Features
- 📊 **Automated Technical Analysis** - RSI, MACD, Bollinger Bands, EMA, Supertrend
- 🎯 **Trading Signals** - Entry opportunities with risk:reward ratios
- 📡 **WebSocket Price Monitor** - Real-time take profit and stop loss tracking
- 🧠 **AI Integration** - Market context analysis via Groq API
- 🌐 **Multi-language** - Spanish and English support
- 💰 **Capital Management** - Drawdown control and performance tracking

### Architecture
- **Entry Point**: `bot/main.py` - Telegram bot initialization and command routing
- **Core**: `bot/core/` - Configuration, database, API clients, analysis logic
- **Handlers**: `bot/handlers/` - Telegram command handlers
- **Trading**: `bot/trading/` - Trading logic, signal generation, price monitoring
- **Application Layer**: `bot/application/` - Use cases (signal cycle, drawdown, journal)
- **Infrastructure**: `bot/infrastructure/` - External adapters (Binance, Groq, Telegram, DB)
- **Domain**: `bot/domain/` - Business entities and repositories
- **DI Container**: `bot/container.py` - Dependency injection wiring

---

## Building and Running

### Prerequisites
- Python 3.13+
- pip
- PostgreSQL database
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/mowgliph/sipsignal.git
cd sipsignal

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials:
# - TELEGRAM_BOT_TOKEN (from @BotFather)
# - ADMIN_CHAT_IDS (comma-separated Telegram IDs)
# - DATABASE_URL (PostgreSQL connection string)
# - GROQ_API_KEY (optional, for AI analysis)
```

### Running the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python bot/main.py

# Or use the botctl script
./bot/botctl.sh run
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_commands.py -v

# Run tests matching pattern
pytest -k "test_signal"

# Run tests in directory
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

---

## Linting and Code Quality

```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check . --fix

# Check formatting
ruff format --check .

# Format code
ruff format .

# Security scan
bandit -r . -x ./tests

# Check dependencies
safety check
```

---

## Development Workflow

Every task MUST follow this cycle:

```
Brainstorm → Issue → Branch → Code → Tests → Lint → Merge → Push → Close
```

### 1. Brainstorm (Required)

**Use the `brainstorming` skill BEFORE writing any code.**

1. Explore project context (files, docs, recent commits)
2. Ask questions to understand purpose, constraints, success criteria
3. Propose 2-3 approaches with trade-offs and recommendation
4. Present design and get user approval
5. Write design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
6. Invoke `writing-plans` skill to create implementation plan

**NEVER write code before completing brainstorm and getting approval.**

### 2. Create Issue

Create a GitHub issue describing:
- Problem to solve or feature to implement
- Acceptance criteria
- Relevant technical context

### 3. Branch

Create branch from `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feat/name-description
# or
git checkout -b fix/name-description
```

### 4. Code

Implement following the Code Style Guidelines below.

### 5. Tests

Write tests before or during implementation.

### 6. Lint

Run linting before commit:
```bash
ruff check . --fix
ruff format .
```

### 7. Merge

```bash
git add .
git commit -m "feat: clear description"
git push -u origin feat/name-description

# Create Pull Request to develop
# Wait for review and CI
# Merge when approved
```

### 8. Push and Close

- Merge to develop triggers CI/CD automatically
- Close issue with PR reference
- Delete remote branch when no longer needed
- **NEVER delete the `develop` branch**

---

## Code Style Guidelines

### General Principles

- **Python 3.13+** - Use modern syntax (type unions with `|`, dataclasses)
- **Async/Await** - Use for all I/O operations (Telegram API, HTTP, database)
- **Line Length** - Maximum 100 characters
- **No Comments** - Avoid unless explaining complex logic or business rules

### Imports

```python
# Standard library
import os
import sys
from dataclasses import dataclass

# Third-party (alphabetical)
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler

# Local (absolute imports, alphabetical by module)
from bot.core.config import settings
from bot.handlers.signal_handler import signal_handlers_list
from bot.trading.data_fetcher import BinanceDataFetcher
```

**Rules:**
- Group imports: stdlib, third-party, local
- Use absolute imports (not relative `..`)
- Separate groups with a blank line
- Alphabetical within groups

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `chat_id`, `signal_active` |
| Functions | snake_case | `async def calculate_all()` |
| Classes | PascalCase | `class Settings:` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_CONFIG`, `LOG_MAX` |
| Files | snake_case | `signal_handler.py`, `config.py` |
| Dataclasses | PascalCase | `@dataclass class Settings:` |

### Type Annotations

Use Python 3.13+ union syntax:

```python
# Good
def process_signal(signal: SignalDTO) -> str | None:
    result: bool | None = None

# Avoid
from typing import Optional
def process_signal(signal: SignalDTO) -> Optional[str]:
```

### Dataclasses

Use frozen dataclasses for configuration:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    token_telegram: str
    admin_chat_ids: list[int]
    log_level: str = "INFO"
```

### Error Handling

```python
# Use specific exceptions with context
try:
    result = await fetcher.get_ohlcv("BTCUSDT", "4h")
except ValueError as e:
    raise ValueError(f"Invalid symbol format: {e}") from e

# Handle gracefully in handlers
try:
    # risky operation
except Exception as e:
    logger.warning(f"Operation failed: {e}")
    await update.message.reply_text(f"⚠️ Error: {str(e)}")
```

### Telegram Handlers

```python
async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Access check first
    if chat_id not in settings.admin_chat_ids:
        await update.message.reply_text("⛔ Access denied.")
        return

    # Show loading state
    msg = await update.message.reply_text("⏳ Processing...")

    try:
        # main logic
        await update.message.reply_text(result)
        await msg.delete()  # cleanup loading message
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {str(e)}")
```

### Async Patterns

```python
# Always close resources
fetcher = BinanceDataFetcher()
try:
    df = await fetcher.get_ohlcv("BTCUSDT", "4h")
finally:
    await fetcher.close()

# Or use context managers if available
async with BinanceDataFetcher() as fetcher:
    df = await fetcher.get_ohlcv("BTCUSDT", "4h")
```

### Database Models

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
```

### Testing Patterns

```python
"""Module docstring."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_function_name():
    """Test description in Spanish."""
    # Test implementation
    assert expected == actual
```

### Ruff Configuration

The project uses ruff with these rules:
- **E, F, W** - pycodestyle, pyflakes, warnings
- **I** - isort (import sorting)
- **N** - pep8-naming
- **UP** - pyupgrade
- **B** - flake8-bugbear
- **C4** - flake8-comprehensions
- **SIM** - flake8-simplify

Ignore E501 (line too long) - handled by formatter.

---

## Project Structure

```
sipsignal/
├── bot/
│   ├── main.py                 # Entry point
│   ├── container.py            # Dependency injection
│   ├── scheduler.py            # Signal scheduler
│   ├── ai/                     # AI clients and prompts
│   ├── application/            # Use cases / application services
│   ├── core/                   # Core functionality (config, database)
│   ├── data/                   # Static data files
│   ├── db/                     # Database models and migrations
│   ├── domain/                 # Business entities
│   ├── handlers/               # Telegram command handlers
│   ├── infrastructure/         # External adapters (Binance, Groq, etc.)
│   ├── trading/                # Trading logic and analysis
│   └── utils/                  # Utility functions
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── pyproject.toml              # Project configuration
├── requirements.txt            # Pip dependencies
├── alembic.ini                 # Database migration config
├── env.example                 # Environment variables template
└── .ruff.toml                  # Linter configuration
```

---

## Key Commands Reference

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Start bot and register |
| `/help` | Show help menu |
| `/status` | Bot status and last analysis |
| `/signal` | Instant BTC technical analysis |
| `/journal` | Signal history |
| `/capital` | Capital management and drawdown |
| `/lang` | Change language |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/users` | Admin dashboard |
| `/logs` | System logs |
| `/ms` | Mass message to users |
| `/ad` | Ad management |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TOKEN_TELEGRAM` | Telegram bot token | ✅ |
| `ADMIN_CHAT_IDS` | Admin chat IDs (comma-separated) | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `GROQ_API_KEY` | Groq API key for AI analysis | ❌ |
| `BINANCE_API_KEY` | Binance API key (future use) | ❌ |
| `SCREENSHOT_API_KEY` | Screenshot API key for charts | ❌ |

---

## CI/CD Pipeline

GitHub Actions runs on push/PR with these stages:

1. **Lint** - ruff check and format validation
2. **Test** - pytest with coverage reporting
3. **Build** - Package build and validation
4. **Security** - bandit and safety scans

---

## Version

**Current:** 1.1.0 (Production)
**Last Updated:** March 2026
**Status:** ✅ Active Development
