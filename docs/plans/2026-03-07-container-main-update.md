# Update bot/main.py to Use Container

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace SignalScheduler direct instantiation with Container-based RunSignalCycle use case in bot/main.py

**Architecture:** Add Container instantiation after bot build, store in bot_data, and replace SignalScheduler with container.run_signal_cycle.execute() call in post_init using UserConfig from repository

**Tech Stack:** Python, Telegram Bot API, SQLAlchemy/asyncpg

---

### Task 1: Add Container Instantiation in main()

**Files:**
- Modify: `bot/main.py:243-244`

**Step 1: Add Container import and instantiation**

After line 243 (`app = builder.build()`), add:

```python
from bot.container import Container

container = Container(settings=settings, bot=app.bot)
app.bot_data["container"] = container
```

**Step 2: Run linter to verify**

Run: `ruff check bot/main.py --fix`
Expected: No errors for the new import and lines

---

### Task 2: Replace SignalScheduler with Container Use Case

**Files:**
- Modify: `bot/main.py:216-222`

**Step 1: Replace SignalScheduler instantiation**

Replace the current code:
```python
# Iniciar SignalScheduler
try:
    scheduler = SignalScheduler()
    asyncio.create_task(scheduler.start(app.bot))
    logger.info("✅ SignalScheduler iniciado")
except Exception as e:
    logger.error(f"❌ Error al iniciar SignalScheduler: {e}")
```

With:
```python
# Ejecutar ciclo de señales via Container
try:
    container = app.bot_data.get("container")
    if container is None:
        raise RuntimeError("Container not found in bot_data")

    admin_id = settings.admin_chat_ids[0] if settings.admin_chat_ids else None
    if admin_id is None:
        logger.warning("No admin_chat_ids configured - skipping signal cycle")
    else:
        user_config = await container.user_config_repo.get(admin_id)
        if user_config is None:
            from bot.domain.user_config import UserConfig
            user_config = UserConfig(
                user_id=admin_id,
                chat_id=admin_id,
                timeframe="4h",
            )

        await container.run_signal_cycle.execute(user_config)
        logger.info("✅ Signal cycle executed via Container")

except Exception as e:
    logger.error(f"❌ Error al ejecutar signal cycle: {e}")
```

**Step 2: Run linter to verify**

Run: `ruff check bot/main.py --fix`
Expected: No errors

---

### Task 3: Remove Unused SignalScheduler Import

**Files:**
- Modify: `bot/main.py:51`

**Step 1: Remove the SignalScheduler import**

Remove line 51:
```python
from bot.scheduler import SignalScheduler
```

**Step 2: Verify no other usage of SignalScheduler remains**

Run: `grep -n "SignalScheduler" bot/main.py`
Expected: No output

**Step 3: Run linter**

Run: `ruff check bot/main.py --fix`
Expected: Clean

---

### Task 4: Run Tests to Verify Changes

**Step 1: Run all tests**

Run: `pytest tests/unit/ -v`
Expected: All tests pass (may have pre-existing failures)

**Step 2: Run specific container-related tests if any**

Run: `pytest -k "container" -v`
Expected: Any container tests pass

---

### Task 5: Run Full Linting

**Step 1: Run full project lint**

Run: `ruff check . --fix`
Expected: No errors

**Step 2: Run format check**

Run: `ruff format --check .`
Expected: No formatting issues

---

## Summary of Changes

| File | Change |
|------|--------|
| bot/main.py:243-244 | Added Container instantiation and storage in bot_data |
| bot/main.py:216-222 | Replaced SignalScheduler with container.run_signal_cycle.execute() |
| bot/main.py:51 | Removed unused SignalScheduler import |
