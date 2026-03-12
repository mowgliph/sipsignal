# Chart Indicator Buttons Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix chart indicator buttons so that clicking an indicator button regenerates the image with that indicator activated, and toggling it again removes it from the image.

**Architecture:** Fix callback data serialization in `build_chart_keyboard()` to use "T"/"F" strings instead of Python booleans, and make `parse_bool()` more robust to handle both formats.

**Tech Stack:** Python 3.13+, python-telegram-bot, matplotlib, SQLAlchemy

---

## Context

### Problem Identified
When clicking indicator buttons (EMA, BB, RSI, Pivots) in the `/chart` command, **nothing happens** - neither the button state updates nor the image regenerates.

### Root Cause
The `build_chart_keyboard()` function serializes boolean values as Python strings `"True"`/`"False"` in timeframe button callbacks, but `parse_bool()` only accepts `"T"`/`"F"`. This causes all indicator states to parse as `False` when changing timeframes.

### Current Broken Flow
```
build_chart_keyboard() creates callback:
  "chart_tf|BTCUSDT|4h|True|False|True|False"

parse_bool("True") → "TRUE" == "T" → False ❌

Result: All indicators always False after timeframe change
```

### Expected Fixed Flow
```
build_chart_keyboard() creates callback:
  "chart_tf|BTCUSDT|4h|T|F|T|F"

parse_bool("T") → "T" == "T" → True ✅

Result: Indicators preserve state correctly
```

---

## Implementation Tasks

### Task 1: Fix `parse_bool()` to be more robust

**Files:**
- Modify: `bot/handlers/chart_handler.py:16-18`
- Test: `tests/unit/test_chart_handler.py` (add tests)

**Step 1: Add test for "True"/"False" parsing**

Add to `tests/unit/test_chart_handler.py`:

```python
def test_parse_bool_true_string():
    """Test 'True' string parses to True boolean."""
    assert parse_bool("True") is True
    assert parse_bool("true") is True
    assert parse_bool("TRUE") is True


def test_parse_bool_false_string():
    """Test 'False' string parses to False boolean."""
    assert parse_bool("False") is False
    assert parse_bool("false") is False
    assert parse_bool("FALSE") is False
```

**Step 2: Run test to verify it fails**

```bash
source venv/bin/activate
pytest tests/unit/test_chart_handler.py::test_parse_bool_true_string -v
```

Expected: FAIL (assertion error)

**Step 3: Update `parse_bool()` function**

Modify `bot/handlers/chart_handler.py:16-18`:

```python
def parse_bool(value: str) -> bool:
    """Parse T/F or True/False string to boolean (case-insensitive)."""
    value = str(value).upper()
    return value == "T" or value == "TRUE"
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_chart_handler.py::test_parse_bool_true_string -v
pytest tests/unit/test_chart_handler.py::test_parse_bool_false_string -v
pytest tests/unit/test_chart_handler.py -v  # All chart handler tests
```

Expected: All PASS

**Step 5: Commit**

```bash
git add bot/handlers/chart_handler.py tests/unit/test_chart_handler.py
git commit -m "fix: make parse_bool() handle True/False strings"
```

---

### Task 2: Fix `build_chart_keyboard()` to use "T"/"F" consistently

**Files:**
- Modify: `bot/handlers/chart_handler.py:29-42`

**Step 1: Update timeframe button callback data**

Modify `bot/handlers/chart_handler.py:33-38`:

```python
# Row 1: Timeframes
tf_buttons = [
    InlineKeyboardButton(
        f"{'✅ ' if tf == timeframe else ''}{tf.upper()}",
        callback_data=f"chart_tf|{symbol}|{tf}|{'T' if show_ema else 'F'}|{'T' if show_bb else 'F'}|{'T' if show_rsi else 'F'}|{'T' if show_pivots else 'F'}",
    )
    for tf in ["1d", "4h", "1h", "15m", "30m"]
]
keyboard.append(tf_buttons)
```

**Current code (WRONG):**
```python
callback_data=f"chart_tf|{symbol}|{tf}|{show_ema}|{show_bb}|{show_rsi}|{show_pivots}"
```

**Step 2: Verify callback data length**

Run existing test:
```bash
pytest tests/unit/test_chart_handler.py::test_build_keyboard_callback_data_format -v
```

Expected: PASS (callback data should be under 64 bytes)

**Step 3: Commit**

```bash
git add bot/handlers/chart_handler.py
git commit -m "fix: serialize booleans as T/F in timeframe callbacks"
```

---

### Task 3: Add logging for debugging

**Files:**
- Modify: `bot/handlers/chart_handler.py:154-200`

**Step 1: Add logging to callback handler**

Modify `bot/handlers/chart_handler.py:154-162`:

```python
async def chart_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from chart buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("|")
    action = parts[0]

    logger.debug(f"Chart callback received: {data}")

    try:
```

**Step 2: Add logging to indicator toggle handler**

Modify `bot/handlers/chart_handler.py:230-245` (in `handle_indicator_toggle`):

```python
async def handle_indicator_toggle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    symbol: str,
    timeframe: str,
    indicator: str,
    new_state: bool,
):
    """Handle indicator toggle button click."""
    logger.debug(f"Toggling {indicator} to {new_state} for {symbol} {timeframe}")

    # Build indicator kwargs
    kwargs = {
        "show_ema": False,
        "show_bb": False,
        "show_rsi": False,
        "show_pivots": False,
    }

    # Set the toggled indicator
    if indicator == "ema":
        kwargs["show_ema"] = new_state
    elif indicator == "bb":
        kwargs["show_bb"] = new_state
    elif indicator == "rsi":
        kwargs["show_rsi"] = new_state
    elif indicator == "pivots":
        kwargs["show_pivots"] = new_state

    logger.debug(f"Chart capture kwargs: {kwargs}")
```

**Step 3: Run linting**

```bash
ruff check bot/handlers/chart_handler.py --fix
ruff format bot/handlers/chart_handler.py
```

**Step 4: Commit**

```bash
git add bot/handlers/chart_handler.py
git commit -m "feat: add debug logging to chart callbacks"
```

---

### Task 4: Add integration test for indicator toggle flow

**Files:**
- Modify: `tests/integration/test_chart_interactive.py`

**Step 1: Add test for indicator toggle**

Add to `tests/integration/test_chart_interactive.py`:

```python
@pytest.mark.asyncio
async def test_chart_indicator_toggle_flow():
    """Test that toggling indicators regenerates chart with correct state."""
    capture = ChartCapture()

    try:
        # Capture with no indicators
        chart_none = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=False, show_bb=False, show_rsi=False, show_pivots=False,
        )
        assert chart_none is not None

        # Capture with EMA only
        chart_ema = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=True, show_bb=False, show_rsi=False, show_pivots=False,
        )
        assert chart_ema is not None

        # Capture with EMA + BB
        chart_ema_bb = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=True, show_bb=True, show_rsi=False, show_pivots=False,
        )
        assert chart_ema_bb is not None

        # Toggle EMA off (only BB active)
        chart_bb_only = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=False, show_bb=True, show_rsi=False, show_pivots=False,
        )
        assert chart_bb_only is not None

        # Verify cache is working (same params = same bytes)
        chart_bb_cached = await capture.capture(
            "BTCUSDT", "4h",
            show_ema=False, show_bb=True, show_rsi=False, show_pivots=False,
        )
        assert chart_bb_only == chart_bb_cached

    finally:
        await capture.close()
```

**Step 2: Run the test**

```bash
pytest tests/integration/test_chart_interactive.py::test_chart_indicator_toggle_flow -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_chart_interactive.py
git commit -m "test: add integration test for indicator toggle flow"
```

---

### Task 5: Run full test suite and verify

**Files:**
- All chart-related tests

**Step 1: Run all chart tests**

```bash
pytest tests/unit/test_chart_handler.py tests/unit/test_chart_generator.py tests/unit/test_chart_capture.py -v
```

Expected: All PASS

**Step 2: Run integration tests**

```bash
pytest tests/integration/test_chart_interactive.py -v
```

Expected: All PASS

**Step 3: Run full test suite**

```bash
pytest --cov=. --cov-report=term-missing
```

Expected: All PASS, coverage maintained or improved

**Step 4: Run linting**

```bash
ruff check . --fix
ruff format .
```

Expected: No issues

**Step 5: Final commit**

```bash
git status
git add .
git commit -m "test: verify all chart tests pass after fix"
```

---

### Task 6: Manual testing checklist

**Files:**
- N/A (manual testing)

**Step 1: Start the bot**

```bash
source venv/bin/activate
python bot/main.py
```

**Step 2: Test in Telegram**

1. Send `/chart BTCUSDT 4h`
2. Verify chart appears with no indicators
3. Click "📈 EMA" button
4. **Expected:** Button shows "✅ 📈 EMA" AND image regenerates with EMA lines
5. Click "✅ 📈 EMA" again
6. **Expected:** Button shows "📈 EMA" (no check) AND image regenerates without EMA
7. Click "📊 BB" button
8. **Expected:** Button shows "✅ 📊 BB" AND image shows Bollinger Bands
9. Click "📉 RSI" button
10. **Expected:** Both BB and RSI buttons show ✅, image shows both indicators
11. Click "1h" timeframe button
12. **Expected:** Timeframe changes to 1h, BB and RSI remain active
13. Click "🔄 Refresh"
14. **Expected:** Image refreshes with same indicators (BB + RSI)

**Step 3: Check logs for debug output**

```bash
tail -50 bot/logs/sipsignal.log | grep -i "chart\|callback"
```

Expected: Debug logs showing callback data and toggle actions

---

## Verification Criteria

✅ All unit tests pass
✅ All integration tests pass
✅ Manual testing in Telegram confirms:
  - Indicator buttons toggle state correctly
  - Image regenerates with each indicator change
  - Timeframe changes preserve indicator state
  - Refresh button works correctly
✅ Linting passes (ruff check + format)
✅ No regression in existing functionality

---

## Rollback Plan

If issues occur:
1. Revert commits: `git revert HEAD~5..HEAD`
2. Restart bot
3. Investigate logs: `tail -100 bot/logs/sipsignal.log`

---

## Related Files Reference

- `bot/handlers/chart_handler.py` - Main handler logic
- `bot/trading/chart_capture.py` - Chart capture with cache
- `bot/utils/chart_generator.py` - Matplotlib chart generation
- `bot/main.py:473` - Callback handler registration
- `tests/unit/test_chart_handler.py` - Unit tests
- `tests/integration/test_chart_interactive.py` - Integration tests
