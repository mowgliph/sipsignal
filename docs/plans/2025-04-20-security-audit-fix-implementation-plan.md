# Security Audit Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corregir 4 vulnerabilidades de seguridad identificadas en la auditoría: duplicados en config, migrar requests a httpx, implementar rate limiting en AccessManager y comandos admin.

**Architecture:** 
- Usar `aiolimiter` para rate limiting async
- Migrar `requests` síncrono a `httpx` async
- Crear módulo reutilizable de rate limiting en `bot/utils/rate_limiter.py`

**Tech Stack:** `aiolimiter`, `httpx`, Python 3.13+ async/await

---

## Task 1: Fix config.py - Eliminar duplicados

**Files:**
- Modify: `bot/core/config.py:31-32` (líneas duplicadas)

**Step 1: Eliminar líneas duplicadas**

Verificar que existen las líneas duplicadas:
```python
cmc_api_key_alerta: str = ""  #Primera definición línea 31
cmc_api_key_control: str = ""  #Primera definición línea 32
cmc_api_key_alerta: str = ""  #DUPLICADA línea 33
cmc_api_key_control: str = ""  #DUPLICADA línea 34
```

Eliminar las líneas 33 y 34 duplicadas.

**Step 2: Verificar que no haya errores**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && python -c "from bot.core.config import settings; print('OK')"`

Expected: Output "OK" sin errores

**Step 3: Commit**

```bash
git add bot/core/config.py
git commit -m "fix: remove duplicate API key definitions in config.py"
```

---

## Task 2: Instalar dependencias

**Files:**
- Modify: `pyproject.toml`

**Step 1: Agregar dependencias al pyproject.toml**

Agregar en `[project.dependencies]`:
```toml
aiolimiter = "^1.1.0"
httpx = "^0.27.0"
```

**Step 2: Instalar dependencias**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && pip install aiolimiter httpx`

Expected: Instalación exitosa

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add aiolimiter and httpx dependencies"
```

---

## Task 3: Crear módulo de rate limiter

**Files:**
- Create: `bot/utils/rate_limiter.py`
- Test: `tests/unit/test_rate_limiter.py`

**Step 1: Escribir el test**

```python
"""Tests for rate_limiter module."""

import asyncio
import pytest

from bot.utils.rate_limiter import RateLimiter, AdminRateLimiter


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_rate_limiter_creation():
    """Test rate limiter can be created."""
    limiter = RateLimiter(max_requests=5, time_window=60)
    assert limiter.max_requests == 5
    assert limiter.time_window == 60


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests():
    """Test rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=3, time_window=1)
    
    # Should allow 3 requests
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess():
    """Test rate limiter blocks excess requests."""
    limiter = RateLimiter(max_requests=2, time_window=1)
    
    await limiter.acquire()
    await limiter.acquire()
    
    # Third request should raise or return False
    result = await limiter.try_acquire()
    assert result is False


def test_admin_rate_limiter_singleton():
    """Test admin rate limiter is singleton."""
    r1 = AdminRateLimiter.get_instance()
    r2 = AdminRateLimiter.get_instance()
    assert r1 is r2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_rate_limiter.py -v`
Expected: FAIL - module doesn't exist yet

**Step 3: Implementar el módulo**

```python
"""Rate limiting utilities using aiolimiter."""

from aiolimiter import AsyncLimiter
from functools import lru_cache


class RateLimiter:
    """
    Async rate limiter wrapper using aiolimiter.
    
    Provides simple async rate limiting with configurable
    max requests and time window.
    """

    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self._limiter = AsyncLimiter(max_requests, time_window)

    async def acquire(self) -> None:
        """Acquire rate limit slot, waiting if necessary."""
        await self._limiter.acquire()

    async def try_acquire(self) -> bool:
        """
        Try to acquire rate limit slot without waiting.
        
        Returns:
            True if acquired, False if rate limited
        """
        try:
            await self._limiter.acquire()
            return True
        except Exception:
            return False

    def reset(self) -> None:
        """Reset the rate limiter."""
        self._limiter = AsyncLimiter(self.max_requests, self.time_window)


class AdminRateLimiter:
    """
    Singleton rate limiter for admin commands.
    
    Limits admin commands to prevent abuse.
    """
    
    _instance: RateLimiter | None = None
    
    @classmethod
    def get_instance(cls) -> RateLimiter:
        """Get singleton instance of admin rate limiter."""
        if cls._instance is None:
            # 5 requests per minute for admin commands
            cls._instance = RateLimiter(max_requests=5, time_window=60)
        return cls._instance


class AdminNotificationRateLimiter:
    """
    Singleton rate limiter for admin notifications.
    
    Limits notifications to admins to prevent spam.
    """
    
    _instance: RateLimiter | None = None
    
    @classmethod
    def get_instance(cls) -> RateLimiter:
        """Get singleton instance of notification rate limiter."""
        if cls._instance is None:
            # 1 request per 10 seconds for admin notifications
            cls._instance = RateLimiter(max_requests=1, time_window=10)
        return cls._instance
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_rate_limiter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bot/utils/rate_limiter.py tests/unit/test_rate_limiter.py
git commit -m "feat: add rate limiter module with aiolimiter"
```

---

## Task 4: Actualizar AccessManager con rate limiting

**Files:**
- Modify: `bot/core/access_manager.py`

**Step 1: Agregar imports y inicializar rate limiter**

Al inicio del archivo agregar:
```python
from bot.utils.rate_limiter import AdminNotificationRateLimiter
```

En el método `__init__`, agregar:
```python
self._notification_limiter = AdminNotificationRateLimiter.get_instance()
self._last_notification_user: dict[int, datetime] = {}  # Track last notification per user
self.NOTIFICATION_COOLDOWN_SECONDS = 60  # Don't notify same user within 60s
```

**Step 2: Modificar método _notify_admins para usar rate limiting**

En el método `_notify_admins`, rodear el envío de notificaciones:

```python
async def _notify_admins(self, bot: Bot, user_chat_id: int, username: str | None) -> None:
    """Notifica a todos los administradores sobre una nueva solicitud de acceso."""
    
    # Rate limiting - check if we should send notification
    limiter = AdminNotificationRateLimiter.get_instance()
    
    # Check cooldown for this specific user (don't spam about same user)
    now = datetime.now(UTC)
    last_notify = self._last_notification_user.get(user_chat_id)
    
    if last_notify and (now - last_notify).total_seconds() < self.NOTIFICATION_COOLDOWN_SECONDS:
        # Already notified recently about this user, skip
        return
    
    # Try to acquire rate limit slot
    if not await limiter.try_acquire():
        # Rate limited, skip notification but continue
        from bot.utils.logger import logger
        logger.warning(f"Admin notification rate limited, skipping for user {user_chat_id}")
        return
    
    # Update last notification time for this user
    self._last_notification_user[user_chat_id] = now
    
    # ... rest of existing code ...
```

**Step 3: Run tests**

Run: `pytest tests/unit/ -v -k "access" --tb=short`
Expected: PASS (o los que existan)

**Step 4: Commit**

```bash
git add bot/core/access_manager.py
git commit -m "feat: add rate limiting to AccessManager notifications"
```

---

## Task 5: Proteger comandos admin con rate limiting

**Files:**
- Modify: `bot/handlers/access_admin.py`
- Modify: `bot/utils/__init__.py` (exportar rate limiter)

**Step 1: Agregar imports**

```python
from bot.utils.rate_limiter import AdminRateLimiter
```

**Step 2: Crear decorator de rate limiting para comandos admin**

Agregar al inicio del archivo (después de los imports):

```python
def rate_limited_admin(func):
    """
    Decorator that applies rate limiting to admin commands.
    
    Combined with @admin_only decorator.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        limiter = AdminRateLimiter.get_instance()
        if not await limiter.try_acquire():
            # Get update from args
            update = args[0] if args else None
            if update and hasattr(update, 'message'):
                await update.message.reply_text(
                    "⏳ Demasiadas solicitudes. Por favor, espera un momento."
                )
            return None
        return await func(*args, **kwargs)
    return wrapper
```

**Step 3: Aplicar decorator a comandos sensibles**

Modificar las definiciones de funciones:

```python
@admin_only
@rate_limited_admin
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... existing code ...

@admin_only
@rate_limited_admin  
async def deny_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... existing code ...

@admin_only
@rate_limited_admin
async def make_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... existing code ...
```

**Step 4: Verificar que funcione**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && python -c "from bot.handlers.access_admin import approve_command; print('OK')"`

Expected: Output "OK"

**Step 5: Commit**

```bash
git add bot/handlers/access_admin.py bot/utils/__init__.py
git commit -m "feat: add rate limiting to admin commands"
```

---

## Task 6: Migrar api_client.py de requests a httpx

**Files:**
- Modify: `bot/core/api_client.py`
- Test: `tests/unit/test_api_client.py` (si existe)

**Step 1: Revisar api_client.py actual**

Leer el archivo para entender las funciones que usan `requests`.

**Step 2: Migrar a httpx async**

Reemplazar:
```python
import requests

response = requests.get(url, headers=headers, params=params, timeout=10)
```

Con:
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers, params=params, timeout=10.0)
```

**Step 3: Verificar que funcione**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && python -c "from bot.core.api_client import *; print('OK')"`

Expected: Output "OK" (puede mostrar warnings si no hay API keys configuradas, pero debe importar bien)

**Step 4: Commit**

```bash
git add bot/core/api_client.py
git commit -m "refactor: migrate api_client from requests to httpx async"
```

---

## Task 7: Verificación final

**Step 1: Run all tests**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && pytest tests/unit/ -v --tb=short`

Expected: Todos los tests pasando

**Step 2: Run linter**

Run: `cd /home/mowgli/sipsignal && source venv/bin/activate && ruff check bot/ --fix && ruff format bot/`

Expected: Sin errores

**Step 3: Commit**

```bash
git add .
git commit -m "fix: security audit fixes - rate limiting and httpx migration"
```

---

## Resumen de archivos modificados

| Archivo | Acción |
|---------|--------|
| `bot/core/config.py` | Eliminar duplicados |
| `pyproject.toml` | Agregar dependencias |
| `bot/utils/rate_limiter.py` | **NUEVO** - Módulo de rate limiting |
| `tests/unit/test_rate_limiter.py` | **NUEVO** - Tests |
| `bot/core/access_manager.py` | Agregar rate limiting |
| `bot/handlers/access_admin.py` | Proteger comandos admin |
| `bot/core/api_client.py` | Migrar a httpx |

---

## Plan completo y guardado en `docs/plans/2025-04-20-security-audit-fix-implementation-plan.md`. Dos opciones de ejecución:**

**1. Subagent-Driven (esta sesión)** - Dispacho subagentes por tarea, reviso entre tareas, iteración rápida

**2. Parallel Session (separada)** - Abrir nueva sesión con executing-plans, ejecución por lotes con checkpoints

**¿Qué enfoque prefieres?**