# Telemetry Lock Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all synchronous lock acquisition and release calls in `bot/utils/telemetry.py` to ensure compatibility with `asyncio.Lock()`.

**Architecture:** Replace synchronous lock calls with `# TODO: migrate to asyncio.Lock properly` comments.

**Tech Stack:** Python, pytest

---

### Task 1: Clean up `log_event` function

**Files:**
- Modify: `bot/utils/telemetry.py`
- Test: `tests/unit/test_telemetry.py` (Verify it doesn't crash)

**Step 1: Write a test to call `log_event`**

```python
import pytest
from bot.utils.telemetry import log_event

def test_log_event_no_crash():
    # Should not raise TypeError: '_file_lock' is not a lock
    # Or similar errors from calling sync methods on asyncio.Lock
    result = log_event("command_used", 12345, {"command": "start"})
    assert result is True
```

**Step 2: Run test to verify it fails (or crashes)**

Run: `pytest tests/unit/test_telemetry.py::test_log_event_no_crash -v`

**Step 3: Remove synchronous lock release in `log_event`**

Modify `bot/utils/telemetry.py`:
- Remove `finally: _file_lock.release()` from `log_event`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_telemetry.py::test_log_event_no_crash -v`

**Step 5: Commit**

```bash
git add bot/utils/telemetry.py
git commit -m "chore: remove sync lock release from log_event"
```

---

### Task 2: Clean up `export_events` function

**Files:**
- Modify: `bot/utils/telemetry.py`

**Step 1: Remove synchronous lock release in `export_events`**

Modify `bot/utils/telemetry.py`:
- Add `# TODO: migrate to asyncio.Lock properly` at the start of `export_events`.
- Remove `finally: _file_lock.release()`.

**Step 2: Commit**

```bash
git add bot/utils/telemetry.py
git commit -m "chore: remove sync lock release from export_events"
```

---

### Task 3: Clean up `get_summary` function

**Files:**
- Modify: `bot/utils/telemetry.py`

**Step 1: Remove synchronous lock acquisition and release in `get_summary`**

Modify `bot/utils/telemetry.py`:
- Remove the block:
```python
    acquired = _file_lock.acquire(timeout=LOCK_TIMEOUT_SECONDS)
    if not acquired:
        logger.error("Failed to acquire telemetry lock within timeout")
        return {}
```
- Replace with `# TODO: migrate to asyncio.Lock properly`.
- Remove `finally: _file_lock.release()`.

**Step 2: Commit**

```bash
git add bot/utils/telemetry.py
git commit -m "chore: remove sync lock from get_summary"
```

---

### Task 4: Final verification and Linting

**Step 1: Run all tests**

Run: `pytest tests/unit/test_telemetry.py -v`

**Step 2: Run linting**

Run: `ruff check bot/utils/telemetry.py --fix && ruff format bot/utils/telemetry.py`

**Step 3: Final Commit**

```bash
git add bot/utils/telemetry.py
git commit -m "chore: telemetry lock cleanup complete and formatted"
```
