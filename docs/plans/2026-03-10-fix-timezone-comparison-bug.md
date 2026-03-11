# Fix Timezone Comparison Bug Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the `can't compare offset-naive and offset-aware datetimes` error in the signal timeout process.

**Architecture:** Convert the timeout threshold datetime to naive (UTC) before comparing with the database `detected_at` field, ensuring both sides of the comparison have the same timezone awareness.

**Tech Stack:** Python 3.13+, datetime, asyncpg, PostgreSQL

---

## Context

### Problem
The error occurs in `bot/handlers/signal_response_handler.py:268`:
```python
timeout_threshold = datetime.now(UTC) - timedelta(seconds=SIGNAL_TIMEOUT)
```

This creates an **offset-aware** datetime, but PostgreSQL returns `detected_at` as **offset-naive** when queried, causing the comparison to fail.

### Root Cause
- `datetime.now(UTC)` creates offset-aware datetime (has timezone info)
- PostgreSQL `detected_at` column is `DateTime(timezone=True)` but returns naive datetime
- Python 3.13+ raises TypeError when comparing naive vs aware datetimes

### Solution
Convert the threshold to naive datetime before comparison:
```python
timeout_threshold = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=SIGNAL_TIMEOUT)
```

---

## Tasks

### Task 1: Fix Timezone Comparison in signal_response_handler.py

**Files:**
- Modify: `bot/handlers/signal_response_handler.py:268`

**Step 1: Read the current implementation**

Read lines 260-280 of `bot/handlers/signal_response_handler.py` to understand the context.

**Step 2: Apply the fix**

Replace line 268:

**Before:**
```python
timeout_threshold = datetime.now(UTC) - timedelta(seconds=SIGNAL_TIMEOUT)
```

**After:**
```python
# Convert to naive datetime for DB comparison (both sides must be naive)
timeout_threshold = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=SIGNAL_TIMEOUT)
```

**Step 3: Verify the import is correct**

Ensure line 7 has:
```python
from datetime import UTC, datetime, timedelta
```

**Step 4: Run linting**

```bash
ruff check bot/handlers/signal_response_handler.py --fix
ruff format bot/handlers/signal_response_handler.py
```

Expected: No errors

**Step 5: Commit**

```bash
git add bot/handlers/signal_response_handler.py
git commit -m "fix: timezone comparison in signal timeout handler"
```

---

### Task 2: Verify Bot Restart and Logs

**Files:**
- No code changes

**Step 1: Restart the bot**

```bash
cd /home/mowgli/sipsignal
./bot/botctl.sh restart
```

Expected: `✅ Bot reiniciado correctamente`

**Step 2: Check service status**

```bash
systemctl status sipsignal.service
```

Expected: `Active: active (running)`

**Step 3: Read recent logs**

```bash
sudo journalctl -u sipsignal.service --since "2026-03-10 23:37:00" --no-pager -n 40
```

**Expected Results:**
- ✅ No `can't compare offset-naive and offset-aware datetimes` error
- ✅ Signal cycle executes without timezone errors
- ✅ PriceMonitor connected to `wss://stream.binance.us:9443/ws`
- ✅ Bot status: `✅ SipSignal iniciado. Esperando mensajes...`

**Step 4: Verify signal timeout process**

Search logs for:
- `⏰ Signal timeout process iniciado`
- No error messages related to datetime comparison

---

### Task 3: Add Regression Test (Optional but Recommended)

**Files:**
- Create: `tests/unit/test_signal_timeout.py`

**Step 1: Write test for timezone handling**

```python
"""
Tests para signal timeout handler.
"""

import pytest
from datetime import UTC, datetime, timedelta


def test_timeout_threshold_comparison():
    """
    Test que verifica que el timeout threshold se puede comparar
    con datetimes de la base de datos (naive).
    """
    # Simular el cálculo del timeout threshold
    SIGNAL_TIMEOUT = 3600  # 1 hora en segundos

    # Threshold con timezone (offset-aware)
    threshold_aware = datetime.now(UTC) - timedelta(seconds=SIGNAL_TIMEOUT)

    # Threshold sin timezone (offset-naive) para comparar con DB
    threshold_naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=SIGNAL_TIMEOUT)

    # Simular detected_at de la DB (offset-naive)
    detected_at_naive = datetime.now().replace(tzinfo=None) - timedelta(seconds=3700)

    # La comparación naive-naive DEBE funcionar
    assert detected_at_naive < threshold_naive

    # La comparación aware-naive DEBE fallar
    with pytest.raises(TypeError):
        detected_at_naive < threshold_aware
```

**Step 2: Run the test**

```bash
pytest tests/unit/test_signal_timeout.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/test_signal_timeout.py
git commit -m "test: add regression test for timezone comparison"
```

---

## Acceptance Criteria

- [ ] Bot restarts without errors
- [ ] No `can't compare offset-naive and offset-aware datetimes` in logs
- [ ] Signal timeout process runs successfully
- [ ] PriceMonitor connected to Binance US WebSocket
- [ ] All existing tests pass
- [ ] Code passes linting (`ruff check . --fix`)

---

## Rollback Plan

If issues occur, revert the change:

```bash
git revert HEAD
./bot/botctl.sh restart
```

---

## Related Files

- `bot/handlers/signal_response_handler.py` - Main fix location
- `bot/domain/signal.py` - Signal entity with `detected_at`
- `bot/infrastructure/database/signal_repository.py` - Signal persistence
- `bot/db/models.py` - SQLAlchemy models
