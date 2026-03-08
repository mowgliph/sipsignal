# Container de Dependencias - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create `bot/container.py` with the `Container` class that wires all adapters, repositories, and use cases together.

**Architecture:** Simple dependency injection container that instantiates all components and exposes them as attributes. The container receives `Settings` and a Telegram `bot` instance, then composes all infrastructure adapters with application use cases.

**Tech Stack:** Python 3.13+, asyncio, Telegram Bot API, SQLAlchemy/asyncpg

---

### Task 1: Create container.py with Container class

**Files:**
- Create: `bot/container.py`

**Step 1: Write the file**

```python
"""Dependency injection container for the bot."""

from bot.core.config import Settings
from bot.infrastructure.binance.binance_adapter import BinanceAdapter
from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
from bot.infrastructure.groq.groq_adapter import GroqAdapter
from bot.infrastructure.telegram.telegram_notifier import TelegramNotifier
from bot.infrastructure.database.signal_repository import PostgreSQLSignalRepository
from bot.infrastructure.database.active_trade_repository import PostgreSQLActiveTradeRepository
from bot.infrastructure.database.user_repositories import (
    PostgreSQLUserConfigRepository,
    PostgreSQLDrawdownRepository,
)
from bot.application.run_signal_cycle import RunSignalCycle
from bot.application.handle_drawdown import HandleDrawdown
from bot.application.get_signal_analysis import GetSignalAnalysis
from bot.application.get_scenario_analysis import GetScenarioAnalysis
from bot.application.manage_journal import ManageJournal


class Container:
    """Dependency injection container that wires all components."""

    def __init__(self, settings: Settings, bot):
        """
        Initialize the container with settings and bot instance.

        Args:
            settings: Application settings from bot.core.config
            bot: Telegram bot instance
        """
        # Adaptadores de infraestructura
        self.market_data = BinanceAdapter()
        self.chart = ScreenshotAdapter(api_key=settings.screenshot_api_key)
        self.ai = GroqAdapter(api_key=settings.groq_api_key)
        self.notifier = TelegramNotifier()

        # Repositorios
        self.signal_repo = PostgreSQLSignalRepository()
        self.trade_repo = PostgreSQLActiveTradeRepository()
        self.user_config_repo = PostgreSQLUserConfigRepository()
        self.drawdown_repo = PostgreSQLDrawdownRepository()

        # Casos de uso
        self.run_signal_cycle = RunSignalCycle(
            market_data=self.market_data,
            signal_repo=self.signal_repo,
            trade_repo=self.trade_repo,
            chart=self.chart,
            ai=self.ai,
            notifier=self.notifier,
            admin_chat_ids=settings.admin_chat_ids,
        )
        self.handle_drawdown = HandleDrawdown(
            drawdown_repo=self.drawdown_repo,
            user_config_repo=self.user_config_repo,
            notifier=self.notifier,
        )
        self.get_signal_analysis = GetSignalAnalysis(
            market_data=self.market_data,
            chart=self.chart,
            ai=self.ai,
        )
        self.get_scenario_analysis = GetScenarioAnalysis(
            market_data=self.market_data,
            ai=self.ai,
        )
        self.manage_journal = ManageJournal(signal_repo=self.signal_repo)
```

**Step 2: Run ruff to check for issues**

Run: `ruff check bot/container.py`
Expected: No errors (or fix if any)

**Step 3: Run ruff format**

Run: `ruff format bot/container.py`
Expected: File formatted

---

### Task 2: Verify the container can be imported

**Files:**
- Test: `bot/container.py`

**Step 1: Run Python import test**

Run: `source venv/bin/activate && python -c "from bot.container import Container; print('Import OK')"`
Expected: Import OK

**Step 2: Verify Container class exists**

Run: `source venv/bin/activate && python -c "from bot.container import Container; print(hasattr(Container, '__init__'))"`
Expected: True

---

### Task 3: Commit changes

**Step 1: Check git status**

Run: `git status`

**Step 2: Add and commit**

Run: `git add bot/container.py && git commit -m "feat: add dependency container for wiring components"`
