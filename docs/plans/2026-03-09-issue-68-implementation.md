# [Issue #68] Refactorización de Manejo de Errores e Integración de Alertas

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Sustituir bloques `except Exception` genéricos por excepciones específicas y un sistema de alertas al Admin para mejorar la visibilidad operativa.

**Architecture:** Enfoque híbrido utilizando un decorador centralizado para tareas repetitivas (UI/APIs) y refactorización manual para el núcleo de trading (Nivel Crítico). Las alertas se canalizan a través del `NotifierPort` existente.

**Tech Stack:** Python 3.13, `loguru`, `python-telegram-bot`, `asyncpg`, `aiohttp`.

---

### Task 1: Implementar Decorador `@handle_errors`

**Files:**
- Create: `bot/utils/decorators.py`
- Test: `tests/unit/test_decorators.py`

**Step 1: Write the failing test**

```python
import pytest
from bot.utils.decorators import handle_errors

@handle_errors(exceptions=(ValueError,), fallback_value="default", alert_admin=False)
async def risky_func(should_fail=False):
    if should_fail:
        raise ValueError("Boom")
    return "ok"

@pytest.mark.asyncio
async def test_handle_errors_decorator_catches():
    assert await risky_func(should_fail=True) == "default"
    assert await risky_func(should_fail=False) == "ok"
```

**Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/unit/test_decorators.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'bot.utils.decorators')

**Step 3: Write minimal implementation**

```python
import functools
import asyncio
from loguru import logger

def handle_errors(exceptions=(Exception,), fallback_value=None, alert_admin=False, level="ERROR"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                log_msg = f"Error in {func.__name__}: {str(e)}"
                if level == "ERROR":
                    logger.exception(log_msg)
                else:
                    getattr(logger, level.lower())(log_msg)

                if alert_admin:
                    # TODO: Inyectar lógica de notificación al Admin en Task 2
                    pass
                return fallback_value
        return wrapper
    return decorator
```

**Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/unit/test_decorators.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/utils/decorators.py tests/unit/test_decorators.py
git commit -m "feat: add handle_errors decorator for centralized error management"
```

---

### Task 2: Integrar Alerta al Admin en el Decorador

**Files:**
- Modify: `bot/utils/decorators.py`
- Modify: `bot/container.py` (para acceder al notifier)
- Test: `tests/unit/test_decorators.py`

**Step 1: Write test for admin notification**

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_handle_errors_alerts_admin():
    mock_notifier = AsyncMock()
    with patch("bot.container.notifier", mock_notifier):
        @handle_errors(exceptions=(ValueError,), alert_admin=True)
        async def fail_with_alert():
            raise ValueError("Alert this")

        await fail_with_alert()
        mock_notifier.send_message_to_admin.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/unit/test_decorators.py::test_handle_errors_alerts_admin -v`
Expected: FAIL (AssertionError: Expected to be called once)

**Step 3: Implement notification logic**

En `bot/utils/decorators.py`, usar un import diferido o acceso vía `bot.container` para evitar ciclos.

```python
# En wrapper de handle_errors
if alert_admin:
    try:
        from bot.container import notifier
        admin_msg = f"🚨 *TECHNICAL ALERT*\nFunction: `{func.__name__}`\nError: `{type(e).__name__}: {str(e)}`"
        await notifier.send_message_to_admin(admin_msg)
    except Exception as inner_e:
        logger.error(f"Failed to alert admin: {inner_e}")
```

**Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/unit/test_decorators.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/utils/decorators.py
git commit -m "feat: integrate admin alerts into handle_errors decorator"
```

---

### Task 3: Refactorización Crítica - `strategy_engine.py`

**Files:**
- Modify: `bot/trading/strategy_engine.py`
- Test: `tests/test_strategy_engine.py`

**Step 1: Identify and replace generic blocks**

Localizar `except Exception:` en `run_cycle`.

**Step 2: Replace with specific exceptions and logging**

```python
# Antes
except Exception:
    return None

# Después
from aiohttp import ClientError
from asyncpg import PostgresError

except (ClientError, PostgresError) as e:
    logger.error(f"Critical error in strategy execution: {e}")
    # Enviar alerta manual si no usamos el decorador aquí para mayor control
    from bot.container import notifier
    await notifier.send_message_to_admin(f"🚨 Strategy Engine Fail: {str(e)}")
    return None
```

**Step 3: Run existing tests to ensure no regressions**

Run: `venv/bin/pytest tests/test_strategy_engine.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add bot/trading/strategy_engine.py
git commit -m "refactor: use specific exceptions in strategy_engine.py"
```

---

### Task 4: Refactorización Masiva con Decorador (UI/APIs)

**Files:**
- Modify: `bot/infrastructure/groq/groq_adapter.py`
- Modify: `bot/handlers/scenario_handler.py`
- Modify: `bot/core/btc_advanced_analysis.py`

**Step 1: Apply decorator to GroqAdapter**

```python
@handle_errors(exceptions=(Exception,), fallback_value="", level="WARNING")
async def get_analysis(self, prompt: str) -> str:
    # ... logic
```

**Step 2: Apply decorator to ScenarioHandler**

```python
@handle_errors(exceptions=(Exception,), level="ERROR", alert_admin=True)
async def handle_scenario(update, context):
    # ... logic
```

**Step 3: Run all unit tests**

Run: `venv/bin/pytest tests/unit/ -v`
Expected: PASS

**Step 4: Commit**

```bash
git add bot/infrastructure/groq/groq_adapter.py bot/handlers/scenario_handler.py bot/core/btc_advanced_analysis.py
git commit -m "refactor: apply @handle_errors decorator to UI and API modules"
```
