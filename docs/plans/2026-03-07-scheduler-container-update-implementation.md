# Scheduler Container Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update bot/scheduler.py to use Container for signal generation instead of direct adapter instantiation.

**Architecture:** Replace direct ChartCapture, GroqClient, run_cycle, and build_signal_message calls with container.run_signal_cycle.execute(). Keep timing responsibility in scheduler.

**Tech Stack:** Python, Telegram Bot API, SQLAlchemy

---

## Pre-requisites

Verify current branch:

```bash
git branch
git status
```

---

### Task 1: Modify scheduler.py Imports

**Files:**
- Modify: `bot/scheduler.py:1-16`

**Step 1: Remove unused imports**

Remove:
```python
from bot.ai.groq_client import GroqClient
from bot.core.config import ADMIN_CHAT_IDS
from bot.core.database import execute
from bot.trading.chart_capture import ChartCapture
from bot.trading.signal_builder import build_signal_message
```

**Step 2: Add container import**

Add:
```python
from bot.container import Container
```

**Step 3: Run linter**

Run: `ruff check bot/scheduler.py --fix`

---

### Task 2: Update _run_loop Method to Use Container

**Files:**
- Modify: `bot/scheduler.py:58-111`

**Step 1: Replace _run_loop implementation**

Replace entire _run_loop method with:

```python
async def _run_loop(self, bot, interval):
    """Internal loop that can be tracked as a task."""
    while self._running:
        try:
            container: Container = bot.bot_data.get("container")
            if container is None:
                logger.error("Container not found in bot_data")
                await asyncio.sleep(interval)
                continue

            signal = await container.run_signal_cycle.execute(self._config)

            if signal:
                logger.info(f"📡 Señal detectada: {signal.direction} en {signal.timeframe}")

                chart_capture = container.run_signal_cycle._chart
                chart_bytes = await chart_capture.capture("BTCUSDT", self._config.timeframe)

                ai_context = ""
                try:
                    ai_client = container.run_signal_cycle._ai
                    ai_context = await ai_client.analyze_signal(signal)
                except Exception as e:
                    logger.warning(f"AI analysis failed: {e}")

                text, keyboard = await self._build_signal_message(signal, ai_context, chart_bytes)

                admin_id = container.run_signal_cycle._admin_chat_ids[0] if container.run_signal_cycle._admin_chat_ids else None
                if not admin_id:
                    logger.warning("No admin configured - señal descartada")
                elif chart_bytes:
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=chart_bytes,
                        caption=text,
                        reply_markup=keyboard,
                    )
                else:
                    await bot.send_message(
                        chat_id=admin_id, text=text, reply_markup=keyboard
                    )
                logger.info(f"✅ Señal enviada al admin {admin_id}")

                signal_id = await self._save_signal(signal)
                if signal_id:
                    signal.id = signal_id

                asyncio.create_task(self._signal_timeout(signal, bot))

            else:
                logger.debug("No se detectó señal en este ciclo")

        except Exception as e:
            logger.error(f"Error en ciclo de scheduler: {e}")

        await asyncio.sleep(interval)

    logger.info("🛑 SignalScheduler detenido")
```

**Step 2: Add _build_signal_message helper**

Add new method after _run_loop:

```python
async def _build_signal_message(self, signal, ai_context: str, chart_bytes: bytes | None):
    """Build signal message text and keyboard."""
    from bot.trading.signal_builder import build_signal_message
    return await build_signal_message(signal, self._config, ai_context, chart_bytes)
```

**Step 3: Run linter**

Run: `ruff check bot/scheduler.py --fix`

---

### Task 3: Run Tests

**Step 1: Run scheduler tests**

Run: `pytest -k "scheduler" -v`

**Step 2: Run all unit tests**

Run: `pytest tests/unit/ -v`

---

### Task 4: Run Full Linting

**Step 1: Run ruff**

Run: `ruff check . --fix`

**Step 2: Run format**

Run: `ruff format --check .`

---

## Summary

| Change | File |
|--------|------|
| Remove unused imports | bot/scheduler.py |
| Add Container import | bot/scheduler.py |
| Replace _run_loop to use container | bot/scheduler.py |
| Add _build_signal_message helper | bot/scheduler.py |
