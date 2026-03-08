# Update bot/scheduler.py to Use Container

**Goal:** Replace direct instantiation of adapters (BinanceDataFetcher, ChartCapture, GroqClient, signal_builder) with Container-based approach in SignalScheduler

**Architecture:** Get container from bot.bot_data["container"] and use container.run_signal_cycle.execute() for signal generation. Keep the timing responsibility in scheduler.

**Tech Stack:** Python, Telegram Bot API, SQLAlchemy/asyncpg

---

## Current State

The scheduler directly instantiates:
- `ChartCapture()` for chart capture
- `GroqClient()` for AI analysis
- Uses `run_cycle()` from strategy_engine
- Manual signal building and notification

This creates tight coupling and makes testing difficult.

---

## Target State

1. Get container from `bot.bot_data["container"]`
2. Call `await container.run_signal_cycle.execute(self._config)`
3. Maintain current flow: send chart, save signal, notify admin
4. Remove all direct adapter instantiations

---

## Changes Required

### File: bot/scheduler.py

1. **Remove imports:**
   - `from bot.ai.groq_client import GroqClient`
   - `from bot.trading.chart_capture import ChartCapture`
   - `from bot.trading.signal_builder import build_signal_message`
   - Keep `from bot.trading.strategy_engine import UserConfig, run_cycle` for UserConfig

2. **Modify _run_loop method:**
   - Get container from `bot.bot_data["container"]`
   - Replace internal logic with `signal = await container.run_signal_cycle.execute(self._config)`
   - Keep timing and exception handling

3. **Keep current flow after signal is returned:**
   - Chart capture (redundant but requested)
   - AI analysis (redundant but requested)
   - Signal message building
   - Send to admin
   - Save to DB
   - Timeout task

---

## Testing

- Run existing tests
- Verify scheduler still works with container
