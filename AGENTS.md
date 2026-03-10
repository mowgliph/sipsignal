# AGENTS.md - Agent Coding Guidelines for sipsignal

## Overview

This is a Telegram bot for crypto trading signals using Python 3.13+. The project uses async/await patterns, SQLAlchemy for database, and pytest for testing.

---

## Complete Workflow Cycle

Every task MUST follow this cycle:

```
Brainstorm → Issue → Rama → Código → Tests → Lint → Merge → Push → Cierre
```

### 1. Brainstorm (Obligatorio)

**Usa la skill `superpowers:brainstorming` ANTES de escribir cualquier código.**

```markdown
# Pasos:
1. Explora el contexto del proyecto (archivos, docs, commits recientes)
2. Haz preguntas para entender propósito, restricciones y criterios de éxito
3. Propón 2-3 enfoques con trade-offs y tu recomendación
4. Presenta el diseño y obtén aprobación del usuario
5. Escribe el diseño en `docs/plans/YYYY-MM-DD-<topic>-design.md`
6. Invoca la skill `writing-plans` para crear el plan de implementación

**NUNCA escribas código antes de completar el brainstorm y obtener aprobación.**
```

### 2. Issue

Crea un issue en GitHub describe:
- Problema a resolver o feature a implementar
- Criterios de aceptación
- Contexto técnico relevante

### 3. Rama

Crea una rama desde `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feat/nombre-descriptivo
# o
git checkout -b fix/nombre-descriptivo
```

### 4. Código

Implementa siguiendo las Code Style Guidelines de este documento.

### 5. Tests

Escribe tests antes o durante la implementación:
```bash
# Crear test
touch tests/unit/test_nueva_funcionalidad.py

# Ejecutar tests
pytest tests/unit/test_nueva_funcionalidad.py -v

# Coverage
pytest --cov=. --cov-report=term-missing
```

### 6. Lint

Ejecuta linting antes de commit:
```bash
ruff check . --fix
ruff format .
```

### 7. Merge

```bash
# Haz push de tu rama
git add .
git commit -m "feat: descripción clara"
git push -u origin feat/nombre-descriptivo

# Crea Pull Request a develop
# Espera revisión y CI
# Merge cuando esté aprobado
```

### 8. Push y Cierre

- Merge a develop activa CI/CD automáticamente
- Cierra el issue con referencia al PR
- Elimina la rama remota si ya no es necesaria
- **NUNCA elimines la rama `dev` del remoto ni del local**

---

## Build, Lint, and Test Commands

> **IMPORTANT:** Always activate the virtual environment before running commands below:
> ```bash
> source venv/bin/activate
> ```

### Installation

```bash
pip install -e ".[dev]"        # Install with dev dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run all tests with coverage
pytest --cov=. --cov-report=term-missing

# Run a single test file
pytest tests/unit/test_commands.py

# Run a single test function
pytest tests/unit/test_commands.py::test_command_status_registered

# Run tests matching a pattern
pytest -k "test_signal"

# Run tests in a specific directory
pytest tests/unit/

# Run async tests
pytest tests/ -k "async"
```

### Linting and Formatting

```bash
# Run ruff linter and auto-fix
ruff check . --fix

# Format code
ruff format .

# Check formatting without modifying
ruff format --check .

# Run pre-commit hooks (includes ruff)
pre-commit run --all-files
```

### Security Checks

```bash
# Run bandit security scanner
bandit -r . -x ./tests

# Check dependencies for vulnerabilities
safety check
```

### Building

```bash
# Build package
python -m build

# Install built wheel
pip install dist/*.whl
```

---

## Code Style Guidelines

### General Principles

- **Python 3.13+** - Use modern syntax (type unions with `|`, dataclasses, etc.)
- **Async/Await** - Use for all I/O operations (Telegram API, HTTP, database)
- **Line length** - Maximum 100 characters (enforced by ruff)
- **No comments** - Avoid unless explaining complex logic or business rules
- **Docstrings** - Use triple quotes for module and class docstrings

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

# Local (absolute imports from bot/, alphabetical)
from bot.core.config import settings
from bot.handlers.signal_handler import signal_command
from bot.trading.data_fetcher import BinanceDataFetcher
```

**Rules:**
- Group imports: stdlib, third-party, local (from bot/)
- Use absolute imports (not relative `..`)
- Separate groups with a blank line
- Alphabetical within groups
- Known first-party: `ai`, `core`, `db`, `handlers`, `utils` (configured in ruff)

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `chat_id`, `signal_active` |
| Functions | snake_case | `async def calculate_all()` |
| Classes | PascalCase | `class Settings:` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_CONFIG`, `LOG_MAX` |
| Files | snake_case | `signal_handler.py`, `config.py` |
| Dataclasses | PascalCase | `@dataclass class Settings:` |
| Test files | test_*.py | `test_signal_builder.py` |
| Test functions | test_* | `test_calculate_signal` |

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
        await update.message.reply_text("⛔ Acceso denegado.")
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

### Configuration

- Store all config in `bot/core/config.py`
- Use environment variables (via `.env`)
- Validate required variables at startup
- Export constants at module level

### Testing Patterns

```python
"""
Tests para signal_builder.
"""

import pytest

from bot.trading.signal_builder import build_signal_message


def test_signal_message_long():
    """Test signal message generation for LONG signals."""
    signal = create_test_signal("LONG")
    config = create_test_config()

    result = build_signal_message(signal, config)
    assert "LONG" in result
    assert "50000.0" in result
```

### Ruff Configuration

The project uses ruff with these rules:
- E, F, W - pycodestyle, pyflakes, warnings
- I - isort (import sorting)
- N - pep8-naming
- UP - pyupgrade
- B - flake8-bugbear
- C4 - flake8-comprehensions
- SIM - flake8-simplify
- DTZ - flake8-datetimez (timezone awareness)

Ignore E501 (line too long) - handled by formatter.

---

## Project Structure

```
sipsignal/
├── bot/                    # Main application code
│   ├── ai/                 # AI clients and prompts
│   ├── core/               # Core functionality (config, database, loops)
│   ├── db/                 # Database models and migrations
│   ├── handlers/           # Telegram command handlers
│   ├── trading/            # Trading logic and analysis
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                # Deployment and utility scripts
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD workflows
└── pyproject.toml         # Project configuration
```

---

## Common Tasks

### Running the bot locally

```bash
# Copy and configure .env
cp env.example .env
# Edit .env with your tokens

# Run the bot
python bot/main.py
# Or use botctl.sh
./bot/botctl.sh run
```

### Creating a database migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### CI/CD Workflow

- **Pre-commit**: Runs ruff, formatting, and custom validation hooks
- **Lint**: Code quality checks with ruff
- **Test**: Runs pytest with coverage
- **Security**: Bandit and safety scans
- **Build**: Package building for releases
