# Admin Handler Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor admin.py into modular admin package for better maintainability

**Architecture:** Split 869-line admin.py into handlers/admin/ package with 5 submodules (mass_messaging, user_management, log_viewer, ad_manager, utils) maintaining same external API

**Tech Stack:** Python 3.13+, Telegram API, async/await patterns

---

### Task 1: Create admin package structure

**Files:**
- Create: `bot/handlers/admin/__init__.py`
- Create: `bot/handlers/admin/mass_messaging.py`
- Create: `bot/handlers/admin/user_management.py`
- Create: `bot/handlers/admin/log_viewer.py`
- Create: `bot/handlers/admin/ad_manager.py`
- Create: `bot/handlers/admin/utils.py`

**Step 1: Create package directory and __init__.py**

```bash
mkdir -p bot/handlers/admin
touch bot/handlers/admin/__init__.py
```

**Step 2: Create empty submodule files**

```bash
touch bot/handlers/admin/mass_messaging.py
touch bot/handlers/admin/user_management.py
touch bot/handlers/admin/log_viewer.py
touch bot/handlers/admin/ad_manager.py
touch bot/handlers/admin/utils.py
```

**Step 3: Add package imports to __init__.py**

```python
# bot/handlers/admin/__init__.py
from .mass_messaging import (
    cancel_ms,
    handle_confirmation_choice,
    handle_initial_content,
    ms_start,
    receive_additional_photo,
    receive_additional_text,
    send_broadcast,
)
from .user_management import users
from .log_viewer import logs_command
from .ad_manager import ad_command
from .utils import set_admin_util

__all__ = [
    "ad_command",
    "cancel_ms",
    "handle_confirmation_choice",
    "handle_initial_content",
    "logs_command",
    "ms_start",
    "receive_additional_photo",
    "receive_additional_text",
    "send_broadcast",
    "set_admin_util",
    "users",
]
```

**Step 4: Test package imports**

Run: `python -c "from bot.handlers.admin import users; print('Import successful')"`

Expected: "Import successful"

**Step 5: Commit**

```bash
git add bot/handlers/admin/
git commit -m "feat: create admin package structure with empty submodules"
```

### Task 2: Extract utils module

**Files:**
- Modify: `bot/handlers/admin/utils.py`
- Test: `tests/unit/handlers/admin/test_utils.py`

**Step 1: Write failing test for utils**

```python
# tests/unit/handlers/admin/test_utils.py
import pytest
from bot.handlers.admin.utils import set_admin_util, _clean_markdown

def test_clean_markdown_basic():
    result = _clean_markdown("Hello *world*")
    assert result == "Hello world"

def test_set_admin_util_decorator():
    # Mock test for decorator
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/handlers/admin/test_utils.py -v`
Expected: FAIL with import/module errors

**Step 3: Extract utils functions from admin.py**

Copy from bot/handlers/admin.py lines 42, 312-318, 335-353 to bot/handlers/admin/utils.py

```python
# bot/handlers/admin/utils.py
# Copy the _ function, set_admin_util decorator, _clean_markdown function
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/handlers/admin/test_utils.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin/utils.py tests/unit/handlers/admin/test_utils.py
git commit -m "feat: extract admin utils functions to separate module"
```

### Task 3: Extract mass_messaging module

**Files:**
- Modify: `bot/handlers/admin/mass_messaging.py`
- Test: `tests/unit/handlers/admin/test_mass_messaging.py`

**Step 1: Write failing test for mass messaging**

```python
# tests/unit/handlers/admin/test_mass_messaging.py
import pytest
from bot.handlers.admin.mass_messaging import ms_start

def test_ms_start_admin_only():
    # Mock admin check test
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/handlers/admin/test_mass_messaging.py -v`
Expected: FAIL

**Step 3: Extract mass messaging functions**

Copy from bot/handlers/admin.py:
- States: AWAITING_CONTENT, etc. (lines 47-49)
- Functions: ms_start through send_broadcast (lines 53-271)

Move imports needed: telegram imports, filters, ContextTypes, etc.

```python
# bot/handlers/admin/mass_messaging.py
# Add necessary imports
# Copy all mass messaging functions
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/handlers/admin/test_mass_messaging.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin/mass_messaging.py tests/unit/handlers/admin/test_mass_messaging.py
git commit -m "feat: extract mass messaging handlers to separate module"
```

### Task 4: Extract user_management module

**Files:**
- Modify: `bot/handlers/admin/user_management.py`
- Test: `tests/unit/handlers/admin/test_user_management.py`

**Step 1: Write failing test for user management**

```python
# tests/unit/handlers/admin/test_user_management.py
import pytest
from bot.handlers.admin.user_management import users

def test_users_command_admin_only():
    # Mock admin check test
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/handlers/admin/test_user_management.py -v`
Expected: FAIL

**Step 3: Extract users function**

Copy from bot/handlers/admin.py the users function (lines 354-635)

Move necessary imports: psutil, datetime, etc.

```python
# bot/handlers/admin/user_management.py
# Add necessary imports
# Copy users function
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/handlers/admin/test_user_management.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin/user_management.py tests/unit/handlers/admin/test_user_management.py
git commit -m "feat: extract user management handler to separate module"
```

### Task 5: Extract log_viewer module

**Files:**
- Modify: `bot/handlers/admin/log_viewer.py`
- Test: `tests/unit/handlers/admin/test_log_viewer.py`

**Step 1: Write failing test for log viewer**

```python
# tests/unit/handlers/admin/test_log_viewer.py
import pytest
from bot.handlers.admin.log_viewer import logs_command

def test_logs_command_admin_only():
    # Mock admin check test
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/handlers/admin/test_log_viewer.py -v`
Expected: FAIL

**Step 3: Extract logs_command function**

Copy from bot/handlers/admin.py the logs_command function (lines 636-763)

Move necessary imports: os, time, etc.

```python
# bot/handlers/admin/log_viewer.py
# Add necessary imports
# Copy logs_command function
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/handlers/admin/test_log_viewer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin/log_viewer.py tests/unit/handlers/admin/test_log_viewer.py
git commit -m "feat: extract log viewer handler to separate module"
```

### Task 6: Extract ad_manager module

**Files:**
- Modify: `bot/handlers/admin/ad_manager.py`
- Test: `tests/unit/handlers/admin/test_ad_manager.py`

**Step 1: Write failing test for ad manager**

```python
# tests/unit/handlers/admin/test_ad_manager.py
import pytest
from bot.handlers.admin.ad_manager import ad_command

def test_ad_command_admin_only():
    # Mock admin check test
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/handlers/admin/test_ad_manager.py -v`
Expected: FAIL

**Step 3: Extract ad_command function**

Copy from bot/handlers/admin.py the ad_command function (lines 764-869)

Move necessary imports: InlineKeyboardButton, etc.

```python
# bot/handlers/admin/ad_manager.py
# Add necessary imports
# Copy ad_command function
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/handlers/admin/test_ad_manager.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin/ad_manager.py tests/unit/handlers/admin/test_ad_manager.py
git commit -m "feat: extract ad manager handler to separate module"
```

### Task 7: Update main admin.py to use package

**Files:**
- Modify: `bot/handlers/admin.py`

**Step 1: Write test for package integration**

```python
# Test that main.py can still import from bot.handlers.admin
import pytest
from bot.handlers import admin

def test_admin_package_imports():
    assert hasattr(admin, 'users')
    assert hasattr(admin, 'logs_command')
    assert hasattr(admin, 'ad_command')
    assert hasattr(admin, 'ms_start')
```

**Step 2: Run test to verify current imports work**

Run: `pytest -k test_admin_package_imports -v`
Expected: PASS (since __init__.py imports everything)

**Step 3: Remove extracted code from admin.py**

Delete all functions that were moved to submodules, keeping only imports and any remaining code.

**Step 4: Run test to verify integration**

Run: `pytest -k test_admin_package_imports -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/handlers/admin.py
git commit -m "refactor: update admin.py to import from package submodules"
```

### Task 8: Run full test suite and lint

**Files:**
- None (verification)

**Step 1: Run pytest on admin tests**

Run: `pytest tests/unit/handlers/admin/ -v`
Expected: All tests pass

**Step 2: Run full test suite**

Run: `pytest --cov=. --cov-report=term-missing`
Expected: Coverage >80%, no failures

**Step 3: Run linting**

Run: `ruff check . --fix && ruff format .`
Expected: No linting errors

**Step 4: Test bot startup**

Run: `python -c "from bot.main import main; print('Import successful')"`
Expected: "Import successful"

**Step 5: Commit**

```bash
git add .
git commit -m "test: verify admin refactor with full test suite and linting"
```

### Task 9: Remove old admin.py if fully migrated

**Files:**
- Delete: `bot/handlers/admin.py` (if all functionality moved)

**Step 1: Verify all handlers extracted**

Check that admin.py is now just imports or empty.

**Step 2: Delete admin.py**

```bash
rm bot/handlers/admin.py
```

**Step 3: Update __init__.py to import directly from submodules**

Adjust bot/handlers/__init__.py if needed.

**Step 4: Run final tests**

Run: `pytest tests/unit/handlers/admin/ -v`
Expected: All pass

**Step 5: Commit**

```bash
git add .
git commit -m "refactor: remove old admin.py, complete modular refactor"
```
