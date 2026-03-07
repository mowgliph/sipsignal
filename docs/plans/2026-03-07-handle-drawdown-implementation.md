# HandleDrawdown Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear el caso de uso HandleDrawdown en bot/application/handle_drawdown.py que gestione el drawdown usando inyección de dependencias con DrawdownRepository, UserConfigRepository y NotifierPort.

**Architecture:** Caso de uso que recibe PnL, actualiza el estado del drawdown, envía notificaciones según umbrales (50% warning, 100% pause), y expone métodos reset y resume.

**Tech Stack:** Python 3.13+, async/await, SQLAlchemy/Puertos y Repositorios

---

### Task 1: Agregar chat_id a UserConfig

**Files:**
- Modify: `bot/domain/user_config.py`
- Test: `tests/unit/test_user_config.py` (crear si no existe)

**Step 1: Modificar UserConfig**

```python
# En bot/domain/user_config.py agregar chat_id al dataclass
from dataclasses import dataclass


@dataclass(frozen=True)
class UserConfig:
    user_id: int
    chat_id: int  # AGREGAR ESTE CAMPO
    capital_total: float = 1000.0
    risk_percent: float = 1.0
    max_drawdown_percent: float = 5.0
    direction: str = "LONG"
    timeframe_primary: str = "15m"
    timeframe: str = "15m"
    setup_completed: bool = False

    def max_drawdown_usdt(self) -> float:
        return self.capital_total * (self.max_drawdown_percent / 100)

    def warning_threshold_usdt(self) -> float:
        return self.max_drawdown_usdt() * 0.5
```

**Step 2: Commit**

```bash
git add bot/domain/user_config.py
git commit -m "feat: add chat_id to UserConfig"
```

---

### Task 2: Agregar send_warning a NotifierPort

**Files:**
- Modify: `bot/domain/ports/notifier_port.py`

**Step 1: Modificar NotifierPort**

```python
# En bot/domain/ports/notifier_port.py agregar el método send_warning
from abc import ABC, abstractmethod

from bot.domain.signal import Signal


class NotifierPort(ABC):
    @abstractmethod
    async def send_signal(
        self, chat_id: int, signal: Signal, chart: bytes | None, ai_context: str
    ) -> None: ...

    @abstractmethod
    async def send_warning(self, chat_id: int, message: str) -> None: ...
```

**Step 2: Commit**

```bash
git add bot/domain/ports/notifier_port.py
git commit -m "feat: add send_warning to NotifierPort"
```

---

### Task 3: Implementar HandleDrawdown

**Files:**
- Create: `bot/application/handle_drawdown.py`

**Step 1: Escribir el test primero**

Crear `tests/unit/test_handle_drawdown.py`:

```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from unittest.mock import AsyncMock, MagicMock

from bot.application.handle_drawdown import HandleDrawdown
from bot.domain.drawdown_state import DrawdownState
from bot.domain.user_config import UserConfig


class TestHandleDrawdown:
    def setup_method(self):
        self.mock_drawdown_repo = MagicMock()
        self.mock_user_config_repo = MagicMock()
        self.mock_notifier = AsyncMock()
        
        self.use_case = HandleDrawdown(
            drawdown_repo=self.mock_drawdown_repo,
            user_config_repo=self.mock_user_config_repo,
            notifier=self.mock_notifier,
        )

    @pytest.mark.asyncio
    async def test_execute_no_user_config_returns_none(self):
        self.mock_user_config_repo.get.return_value = None
        
        result = await self.use_case.execute(user_id=1, pnl_usdt=-50.0)
        
        assert result is None
        self.mock_drawdown_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_pnl_applies_to_state(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=5.0,
        )
        drawdown_state = DrawdownState(user_id=1)
        
        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state
        
        result = await self.use_case.execute(user_id=1, pnl_usdt=-50.0)
        
        assert result.current_drawdown_usdt == -50.0
        self.mock_drawdown_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_triggers_warning_at_50_percent(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=10.0,  # 10% max = 100 USDT
        )
        drawdown_state = DrawdownState(user_id=1)
        
        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state
        
        # -60 USDT = 6% = 60% del max (entre 50% y 100%)
        await self.use_case.execute(user_id=1, pnl_usdt=-60.0)
        
        self.mock_notifier.send_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_triggers_pause_at_100_percent(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=5.0,  # 5% max = 50 USDT
        )
        drawdown_state = DrawdownState(user_id=1)
        
        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state
        
        # -60 USDT = 6% > 5% max
        result = await self.use_case.execute(user_id=1, pnl_usdt=-60.0)
        
        assert result.is_paused is True
        self.mock_notifier.send_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_calls_drawdown_repo_reset(self):
        self.mock_drawdown_repo.reset.return_value = DrawdownState(user_id=1)
        
        result = await self.use_case.reset(user_id=1)
        
        self.mock_drawdown_repo.reset.assert_called_once_with(1)
        assert result.user_id == 1

    @pytest.mark.asyncio
    async def test_resume_sets_paused_false_and_saves(self):
        drawdown_state = DrawdownState(user_id=1, is_paused=True)
        self.mock_drawdown_repo.get.return_value = drawdown_state
        
        await self.use_case.resume(user_id=1)
        
        assert drawdown_state.is_paused is False
        self.mock_drawdown_repo.save.assert_called_once_with(drawdown_state)
```

**Step 2: Verificar que falla (ejecutar test)**

```bash
cd /home/mowgli/sipsignal && source venv/bin/activate && pytest tests/unit/test_handle_drawdown.py -v
```

Expected: FAIL - ModuleNotFoundError: No module named 'bot.application.handle_drawdown'

**Step 3: Implementar HandleDrawdown**

Crear `bot/application/handle_drawdown.py`:

```python
from bot.domain.drawdown_state import DrawdownState
from bot.domain.ports import DrawdownRepository, NotifierPort, UserConfigRepository


class HandleDrawdown:
    def __init__(
        self,
        drawdown_repo: DrawdownRepository,
        user_config_repo: UserConfigRepository,
        notifier: NotifierPort,
    ):
        self._drawdown_repo = drawdown_repo
        self._user_config_repo = user_config_repo
        self._notifier = notifier

    async def execute(self, user_id: int, pnl_usdt: float) -> DrawdownState | None:
        config = await self._user_config_repo.get(user_id)
        if config is None:
            return None

        state = await self._drawdown_repo.get(user_id)
        if state is None:
            state = DrawdownState(user_id=user_id)

        state.apply_pnl(pnl_usdt, config.capital_total)

        if state.should_pause(config.max_drawdown_percent):
            state.is_paused = True
            await self._notifier.send_warning(
                config.chat_id,
                f"🚨 SISTEMA PAUSADO\n\n"
                f"Drawdown máximo alcanzado: {abs(state.current_drawdown_percent):.1f}%\n"
                f"({abs(state.current_drawdown_usdt):.2f} USDT)\n\n"
                f"Las señales están suspendidas.\n"
                f"Usa /resume cuando estés listo para continuar.",
            )
        elif state.should_warn(config.max_drawdown_percent):
            await self._notifier.send_warning(
                config.chat_id,
                f"⚠️ Drawdown Warning\n\n"
                f"Tu drawdown actual es de {state.current_drawdown_percent:.1f}%\n"
                f"({abs(state.current_drawdown_usdt):.2f} USDT)\n\n"
                f"Has alcanzado el 50% del límite máximo ({config.max_drawdown_percent}%).\n"
                f"Revisa tu gestión de riesgo.",
            )

        await self._drawdown_repo.save(state)
        return state

    async def reset(self, user_id: int) -> DrawdownState:
        return await self._drawdown_repo.reset(user_id)

    async def resume(self, user_id: int) -> None:
        state = await self._drawdown_repo.get(user_id)
        if state is None:
            state = DrawdownState(user_id=user_id)
        state.is_paused = False
        await self._drawdown_repo.save(state)
```

**Step 4: Verificar que los tests pasan**

```bash
cd /home/mowogli/sipsignal && source venv/bin/activate && pytest tests/unit/test_handle_drawdown.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add bot/application/handle_drawdown.py tests/unit/test_handle_drawdown.py
git commit -m "feat: add HandleDrawdown use case"
```

---

### Task 4: Verificar con lint

**Step 1: Ejecutar ruff**

```bash
cd /home/mowgli/sipsignal && source venv/bin/activate && ruff check .
```

Expected: Sin errores (o errores menores que se pueden auto-fijar)

**Step 2: Auto-fijar si hay errores**

```bash
cd /home/mowgli/sipsignal && source venv/bin/activate && ruff check . --fix
```

**Step 3: Commit final**

```bash
git add -A
git commit -m "lint: fix formatting issues"
```
