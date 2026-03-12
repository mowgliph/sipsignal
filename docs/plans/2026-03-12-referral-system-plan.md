# Referral System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `subagent-driven-development` to implement this plan task-by-task.

**Goal:** Implement a referral tracking system with `/ref` command for generating unique referral codes and links.

**Architecture:** Repository pattern with PostgreSQL storage, utility module for code generation, and Telegram handler for user interaction.

**Tech Stack:** Python 3.13+, asyncpg, SQLAlchemy, Telegram Bot API, pytest

---

## Task 1: Database Migration

**Files:**
- Create: `bot/db/migrations/004_referral_system.sql`

**Step 1: Write migration SQL**

```sql
-- Migration: 004_referral_system.sql
-- Description: Add referral tracking system to users table

-- 1. Add columns to users table
ALTER TABLE users
ADD COLUMN referrer_code VARCHAR(32) UNIQUE,
ADD COLUMN referred_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_referrer_code ON users(referrer_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);

-- 3. Create referrals tracking table
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(referrer_id, referred_id)
);

-- 4. Create indexes for referrals table
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);

-- 5. Add documentation comments
COMMENT ON TABLE referrals IS 'Tracking de referidos entre usuarios';
COMMENT ON COLUMN users.referrer_code IS 'Código único para referidos';
COMMENT ON COLUMN users.referred_by IS 'ID del usuario que lo refirió';
```

**Step 2: Apply migration**

```bash
cd /home/mowgli/sipsignal
source venv/bin/activate
alembic upgrade head
```

Expected: Migration applied successfully, no errors

**Step 3: Verify migration**

```bash
psql $DATABASE_URL -c "\d users"
psql $DATABASE_URL -c "\d referrals"
```

Expected: New columns and table visible

**Step 4: Commit**

```bash
git add bot/db/migrations/004_referral_system.sql
git commit -m "db: add referral system migration"
```

---

## Task 2: Referral Code Generator Utility

**Files:**
- Create: `bot/utils/referral_code.py`
- Test: `tests/unit/test_referral_code.py`

**Step 1: Write unit tests**

```python
"""Tests for referral code generator."""

import pytest

from bot.utils.referral_code import generate_referral_code


def test_generate_referral_code_length():
    """Código debe tener 8 caracteres por defecto."""
    code = generate_referral_code()
    assert len(code) == 8


def test_generate_referral_code_alphanumeric():
    """Código debe ser alfanumérico en mayúsculas."""
    code = generate_referral_code()
    assert code.isalnum()
    assert code == code.upper()


def test_generate_referral_code_no_confusing_chars():
    """Código no debe tener caracteres confusos (0, O, I, L)."""
    code = generate_referral_code()
    assert all(c not in '0OIL' for c in code)


def test_generate_referral_code_custom_length():
    """Código debe soportar longitud personalizada."""
    code = generate_referral_code(length=12)
    assert len(code) == 12


def test_generate_referral_code_uniqueness():
    """Códigos generados deben ser únicos."""
    codes = [generate_referral_code() for _ in range(1000)]
    assert len(codes) == len(set(codes))
```

**Step 2: Run tests to verify they fail**

```bash
cd /home/mowgli/sipsignal
source venv/bin/activate
pytest tests/unit/test_referral_code.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'bot.utils.referral_code'"

**Step 3: Write implementation**

```python
"""Generador de códigos de referido únicos y legibles."""

import secrets
import string


def generate_referral_code(length: int = 8) -> str:
    """
    Genera un código de referido único y legible.

    Args:
        length: Longitud del código (default: 8).

    Returns:
        Código alfanumérico en mayúsculas, sin caracteres confusos.
    """
    alphabet = string.ascii_uppercase + string.digits
    # Excluir caracteres confusos (0, O, I, L)
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('L', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/test_referral_code.py -v
```

Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add bot/utils/referral_code.py tests/unit/test_referral_code.py
git commit -m "feat: add referral code generator utility"
```

---

## Task 3: Referral Repository Interface

**Files:**
- Modify: `bot/domain/ports/repositories.py:56-160`

**Step 1: Add ReferralRepository interface**

```python
class ReferralRepository(ABC):
    """Repository protocol for referral tracking operations."""

    @abstractmethod
    async def get_referrer_code(self, user_id: int) -> str | None:
        """
        Get user's referral code.

        Args:
            user_id: The Telegram user ID.

        Returns:
            Referral code string if exists, None otherwise.
        """
        ...

    @abstractmethod
    async def generate_referrer_code(self, user_id: int) -> str:
        """
        Generate and save unique referral code for user.

        Args:
            user_id: The Telegram user ID.

        Returns:
            Generated referral code.
        """
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> int | None:
        """
        Get user_id from referral code.

        Args:
            code: Referral code string.

        Returns:
            User ID if found, None otherwise.
        """
        ...

    @abstractmethod
    async def record_referral(self, referrer_id: int, referred_id: int) -> None:
        """
        Record new referral relationship.

        Args:
            referrer_id: ID of user who made the referral.
            referred_id: ID of user who was referred.
        """
        ...

    @abstractmethod
    async def get_referrals(self, referrer_id: int) -> list[dict]:
        """
        Get list of users referred by this user.

        Args:
            referrer_id: ID of the referrer.

        Returns:
            List of referral dictionaries with referred user info.
        """
        ...

    @abstractmethod
    async def get_referral_count(self, referrer_id: int) -> int:
        """
        Get total number of referrals for a user.

        Args:
            referrer_id: ID of the referrer.

        Returns:
            Count of referrals.
        """
        ...

    @abstractmethod
    async def get_referrer(self, referred_id: int) -> int | None:
        """
        Get the ID of who referred this user.

        Args:
            referred_id: ID of the referred user.

        Returns:
            Referrer user ID if exists, None otherwise.
        """
        ...
```

**Step 2: Commit**

```bash
git add bot/domain/ports/repositories.py
git commit -m "domain: add ReferralRepository interface"
```

---

## Task 4: PostgreSQL Referral Repository Implementation

**Files:**
- Create: `bot/infrastructure/database/referral_repository.py`
- Test: `tests/integration/test_referral_repository.py`

**Step 1: Write implementation**

```python
"""PostgreSQL implementation of ReferralRepository."""

from bot.core import database
from bot.domain.ports.repositories import ReferralRepository
from bot.utils.referral_code import generate_referral_code


class PostgreSQLReferralRepository(ReferralRepository):
    async def get_referrer_code(self, user_id: int) -> str | None:
        """Get user's referral code."""
        record = await database.fetchrow(
            "SELECT referrer_code FROM users WHERE user_id = $1",
            user_id,
        )
        return record["referrer_code"] if record else None

    async def generate_referrer_code(self, user_id: int) -> str:
        """Generate and save unique referral code for user."""
        # Check if already exists
        existing = await self.get_referrer_code(user_id)
        if existing:
            return existing

        # Generate unique code with retry
        max_retries = 10
        for _ in range(max_retries):
            code = generate_referral_code()
            # Check uniqueness
            existing_user = await self.get_by_code(code)
            if existing_user is None:
                # Save code
                await database.execute(
                    "UPDATE users SET referrer_code = $1 WHERE user_id = $2",
                    code,
                    user_id,
                )
                return code

        raise RuntimeError("Failed to generate unique referral code")

    async def get_by_code(self, code: str) -> int | None:
        """Get user_id from referral code."""
        record = await database.fetchrow(
            "SELECT user_id FROM users WHERE referrer_code = $1",
            code,
        )
        return record["user_id"] if record else None

    async def record_referral(self, referrer_id: int, referred_id: int) -> None:
        """Record new referral relationship."""
        # Prevent self-referral
        if referrer_id == referred_id:
            raise ValueError("Cannot refer oneself")

        # Check if already recorded
        existing = await database.fetchrow(
            "SELECT 1 FROM referrals WHERE referrer_id = $1 AND referred_id = $2",
            referrer_id,
            referred_id,
        )
        if existing:
            return  # Already recorded

        await database.execute(
            """
            INSERT INTO referrals (referrer_id, referred_id)
            VALUES ($1, $2)
            """,
            referrer_id,
            referred_id,
        )

    async def get_referrals(self, referrer_id: int) -> list[dict]:
        """Get list of users referred by this user."""
        records = await database.fetch(
            """
            SELECT u.*, r.referred_at
            FROM referrals r
            JOIN users u ON r.referred_id = u.user_id
            WHERE r.referrer_id = $1
            ORDER BY r.referred_at DESC
            """,
            referrer_id,
        )
        return [dict(r) for r in records]

    async def get_referral_count(self, referrer_id: int) -> int:
        """Get total number of referrals for a user."""
        record = await database.fetchval(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1",
            referrer_id,
        )
        return int(record) if record else 0

    async def get_referrer(self, referred_id: int) -> int | None:
        """Get the ID of who referred this user."""
        record = await database.fetchrow(
            "SELECT referrer_id FROM referrals WHERE referred_id = $1",
            referred_id,
        )
        return record["referrer_id"] if record else None
```

**Step 2: Write integration tests**

```python
"""Integration tests for PostgreSQLReferralRepository."""

import pytest

from bot.core import database
from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository


@pytest.fixture
async def repo():
    """Create repository instance."""
    return PostgreSQLReferralRepository()


@pytest.fixture
async def test_users():
    """Create test users."""
    # Create user 1
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999001,
    )
    # Create user 2
    await database.execute(
        """
        INSERT INTO users (user_id, status, language, registered_at, is_active)
        VALUES ($1, 'approved', 'es', NOW(), TRUE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        999002,
    )
    yield
    # Cleanup
    await database.execute("DELETE FROM users WHERE user_id IN (999001, 999002)")
    await database.execute("DELETE FROM referrals WHERE referrer_id = 999001")


async def test_generate_referrer_code(repo, test_users):
    """Test code generation for user."""
    code = await repo.generate_referrer_code(999001)
    assert len(code) == 8
    assert code.isalnum()

    # Should return same code on second call
    code2 = await repo.generate_referrer_code(999001)
    assert code == code2


async def test_get_by_code(repo, test_users):
    """Test getting user by referral code."""
    code = await repo.generate_referrer_code(999001)
    user_id = await repo.get_by_code(code)
    assert user_id == 999001


async def test_get_by_invalid_code(repo):
    """Test getting user by invalid code returns None."""
    user_id = await repo.get_by_code("INVALID123")
    assert user_id is None


async def test_record_referral(repo, test_users):
    """Test recording referral relationship."""
    await repo.generate_referrer_code(999001)
    await repo.record_referral(999001, 999002)

    count = await repo.get_referral_count(999001)
    assert count == 1


async def test_self_referral_blocked(repo, test_users):
    """Test that self-referral is blocked."""
    with pytest.raises(ValueError, match="Cannot refer oneself"):
        await repo.record_referral(999001, 999001)


async def test_get_referrals(repo, test_users):
    """Test getting list of referrals."""
    await repo.generate_referrer_code(999001)
    await repo.record_referral(999001, 999002)

    referrals = await repo.get_referrals(999001)
    assert len(referrals) == 1
    assert referrals[0]["user_id"] == 999002


async def test_get_referrer(repo, test_users):
    """Test getting referrer of a user."""
    await repo.generate_referrer_code(999001)
    await repo.record_referral(999001, 999002)

    referrer = await repo.get_referrer(999002)
    assert referrer == 999001
```

**Step 3: Run tests**

```bash
pytest tests/integration/test_referral_repository.py -v
```

Expected: All tests PASS (requires database connection)

**Step 4: Commit**

```bash
git add bot/infrastructure/database/referral_repository.py tests/integration/test_referral_repository.py
git commit -m "infra: add PostgreSQLReferralRepository implementation"
```

---

## Task 5: Wire Repository in Container

**Files:**
- Modify: `bot/container.py:1-50`

**Step 1: Add referral repository to Container**

```python
# Add import at top
from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

# Add to __init__ method (after line 50)
self.referral_repo = PostgreSQLReferralRepository()
```

**Step 2: Commit**

```bash
git add bot/container.py
git commit -m "container: wire referral repository"
```

---

## Task 6: Referral Handler

**Files:**
- Create: `bot/handlers/referral_handler.py`
- Test: `tests/unit/test_referral_handler.py`

**Step 1: Write handler implementation**

```python
"""Handler for /ref command."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from bot.core.database import fetchrow
from bot.utils import role_required
from bot.utils.logger import logger
from bot.utils.referral_code import generate_referral_code


async def _get_referral_stats(user_id: int) -> dict:
    """Get referral statistics for user."""
    from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

    repo = PostgreSQLReferralRepository()
    count = await repo.get_referral_count(user_id)
    referrals = await repo.get_referrals(user_id)

    last_referred = None
    if referrals:
        last = referrals[0]
        username = last.get("username")
        last_referred = {
            "username": f"@{username}" if username else f"User {last['user_id']}",
            "date": last.get("referred_at"),
        }

    return {
        "count": count,
        "last_referred": last_referred,
    }


@role_required(["approved", "trader", "admin"])
async def ref_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show user's referral code and link.

    Usage: /ref
    """
    user_id = update.effective_chat.id

    try:
        # Get or generate referral code
        from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

        repo = PostgreSQLReferralRepository()
        code = await repo.get_referrer_code(user_id)

        if not code:
            code = await repo.generate_referrer_code(user_id)
            logger.info(f"Generated referral code {code} for user {user_id}")

        # Get stats
        stats = await _get_referral_stats(user_id)

        # Build message
        message = (
            f"🔗 *TU ENLACE DE REFERIDO*\n"
            f"─────────────────────\n\n"
            f"Tu código: `{code}`\n\n"
            f"Enlace directo:\n"
            f"t.me/sipsignal_bot?start={code}\n\n"
            f"Comparte este enlace para invitar amigos a SipSignal.\n\n"
            f"📊 *Estadísticas:*\n"
            f"• Referidos totales: {stats['count']}\n"
        )

        if stats["last_referred"]:
            last = stats["last_referred"]
            message += f"• Último referido: {last['username']}\n"

        if stats["count"] == 0:
            message += "\n¡Comparte tu enlace para comenzar!\n"

        message += "\n─────────────────────\n"
        message += "Usa /ref stats para ver lista completa"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error en /ref: {e}")
        await update.message.reply_text("⚠️ Error al procesar. Intenta de nuevo.")


async def ref_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show detailed list of referrals.

    Usage: /ref stats
    """
    user_id = update.effective_chat.id

    try:
        from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository

        repo = PostgreSQLReferralRepository()
        referrals = await repo.get_referrals(user_id)
        count = len(referrals)

        if count == 0:
            await update.message.reply_text(
                "📊 *TUS REFERIDOS*\n"
                f"─────────────────────\n\n"
                "Aún no tienes referidos.\n\n"
                "¡Comparte tu enlace para comenzar!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # Build list (max 20 for readability)
        message = f"📊 *TUS REFERIDOS* ({count})\n"
        message += "─────────────────────\n\n"

        for i, ref in enumerate(referrals[:20], 1):
            username = ref.get("username")
            user_str = f"@{username}" if username else f"User {ref['user_id']}"
            date_str = ref.get("referred_at", "").strftime("%d/%m/%Y") if ref.get("referred_at") else "N/A"
            message += f"{i}. {user_str} - {date_str}\n"

        if count > 20:
            message += f"\n... y {count - 20} más"

        message += f"\n\n─────────────────────\n"
        message += f"Total: {count} referidos"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error en /ref stats: {e}")
        await update.message.reply_text("⚠️ Error al obtener datos. Intenta de nuevo.")


# Handlers for registration in bot
ref_handler = CommandHandler("ref", ref_command)
ref_stats_handler = CommandHandler("ref", ref_stats_command, filters=lambda x: len(x.message.text.split()) > 1 and x.message.text.split()[1] == "stats")
```

**Step 2: Write unit tests**

```python
"""Tests for referral handler."""

import pytest
from telegram import Update, User
from telegram.ext import ContextTypes

from bot.handlers.referral_handler import ref_command


@pytest.fixture
def mock_update():
    """Create mock update object."""
    user = User(id=12345, first_name="Test", is_bot=False)
    message = type('Message', (), {
        'chat': type('Chat', (), {'id': 12345})(),
        'reply_text': pytest.AsyncMock(),
    })()
    update = type('Update', (), {'effective_user': user, 'effective_chat': type('Chat', (), {'id': 12345})(), 'message': message})()
    return update


@pytest.fixture
def mock_context():
    """Create mock context object."""
    context = type('Context', (), {'bot_data': {}})()
    return context


@pytest.mark.asyncio
async def test_ref_command_generates_code(mock_update, mock_context, monkeypatch):
    """Test /ref generates code for user without one."""
    async def mock_generate(user_id):
        return "TEST1234"

    async def mock_count(user_id):
        return 0

    async def mock_get_referrals(user_id):
        return []

    monkeypatch.setattr("bot.infrastructure.database.referral_repository.PostgreSQLReferralRepository.get_referrer_code", lambda self, uid: None)
    monkeypatch.setattr("bot.infrastructure.database.referral_repository.PostgreSQLReferralRepository.generate_referrer_code", mock_generate)
    monkeypatch.setattr("bot.handlers.referral_handler._get_referral_stats", lambda uid: {"count": 0, "last_referred": None})

    await ref_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "TEST1234" in call_args
    assert "t.me/sipsignal_bot?start=TEST1234" in call_args
```

**Step 3: Run tests**

```bash
pytest tests/unit/test_referral_handler.py -v
```

Expected: Tests PASS

**Step 4: Commit**

```bash
git add bot/handlers/referral_handler.py tests/unit/test_referral_handler.py
git commit -m "feat: add /ref command handler"
```

---

## Task 7: Modify /start to Accept Referral Code

**Files:**
- Modify: `bot/handlers/general.py:33-90`
- Modify: `bot/db/users.py:45-60`

**Step 1: Modify start function to accept referral code**

```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start. Registra al usuario."""

    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or "es"

    # Check for referral code in args
    referral_code = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0].strip()

    # Register user (pass referral code if exists)
    await register_or_update_user(user_id, user_lang, referral_code)

    nombre_usuario = update.effective_user.first_name

    mensaje = (
        "*⚡ SIPSIGNAL - Sistema de Señales BTC*\n"
        "─────────────\n\n"
        f"Hola {nombre_usuario}! 👋 Bienvenido a SipSignal, tu asistente de trading automatizado para Bitcoin.\n\n"
        "*🎯 ¿Qué hace SipSignal?*\n\n"
        "SipSignal analiza el mercado de BTC/USDT 24/7 y te envía señales de trading cuando detecta oportunidades según tu estrategia. "
        "Incluye monitoreo de TP/SL en tiempo real. No ejecuta órdenes automáticamente - te notifica para que tú decidas.\n\n"
        "*📱 Comandos disponibles:*\n\n"
        "/signal - Análisis técnico instantáneo de BTC\n"
        "/chart [tf] - Ver gráfico (5m, 15m, 1h, 4h, 1D)\n"
        "/risk [entrada] [sl] [tp] - Calcular ratio riesgo/beneficio\n"
        "/journal - Historial de señales emitidas\n"
        "/capital - Gestión de capital y drawdown\n"
        "/status - Estado del sistema y último análisis\n\n"
        "*🔍 Análisis incluye:*\n\n"
        "• RSI, MACD, Bollinger Bands, EMA\n"
        "• Soportes y resistencias\n"
        "• Contexto de mercado con IA (Groq)\n"
        "• Ratio riesgo:beneficio recomendado\n\n"
        "Usa /help para más detalles o /status para ver el estado actual del sistema."
    )

    await update.message.reply_text(mensaje, parse_mode=ParseMode.MARKDOWN)
```

**Step 2: Modify register_or_update_user to handle referral**

```python
async def register_or_update_user(user_id: int, language: str = "es", referral_code: str | None = None) -> dict:
    """
    Registra un nuevo usuario o actualiza last_seen si ya existe.
    Si hay código de referido válido, lo registra.
    Retorna los datos del usuario.
    """
    existing = await get_user(user_id)
    if existing:
        await update_last_seen(user_id)
        return await get_user(user_id)
    else:
        # New user - check referral code
        referrer_id = None
        if referral_code:
            from bot.infrastructure.database.referral_repository import PostgreSQLReferralRepository
            repo = PostgreSQLReferralRepository()
            referrer_id = await repo.get_by_code(referral_code)

            # Prevent self-referral
            if referrer_id == user_id:
                referrer_id = None

        # Create user
        user_data = await create_user(user_id, language, referrer_id)

        # Record referral if valid
        if referrer_id and referrer_id != user_id:
            try:
                await repo.record_referral(referrer_id, user_id)
                logger.info(f"Recorded referral: user {referrer_id} referred user {user_id}")
            except Exception as e:
                logger.error(f"Error recording referral: {e}")

        return user_data
```

**Step 3: Modify create_user signature**

```python
async def create_user(user_id: int, language: str = "es", referred_by: int | None = None) -> dict:
    """Crea un nuevo usuario en la base de datos."""
    now = datetime.now(UTC)
    await execute(
        """
        INSERT INTO users (user_id, language, registered_at, last_seen, is_active, referred_by)
        VALUES ($1, $2, $3, $3, TRUE, $4)
        ON CONFLICT (user_id) DO NOTHING
        """,
        user_id,
        language,
        now,
        referred_by,
    )
    return await get_user(user_id)
```

**Step 4: Commit**

```bash
git add bot/handlers/general.py bot/db/users.py
git commit -m "feat: modify /start to accept referral codes"
```

---

## Task 8: Register Handlers in main.py

**Files:**
- Modify: `bot/main.py:1-50`, `bot/main.py:250-300`

**Step 1: Add import**

```python
from bot.handlers.referral_handler import ref_handler, ref_stats_handler
```

**Step 2: Register handlers (after line 280, before CallbackQueryHandlers)**

```python
# ============================================
# Comandos de Usuario
# ============================================
app.add_handler(CommandHandler("lang", lang_command))
app.add_handler(CommandHandler("my_role", my_role_command))
app.add_handler(CommandHandler("change_role", change_role_command))
app.add_handler(ref_handler)
app.add_handler(ref_stats_handler)
```

**Step 3: Commit**

```bash
git add bot/main.py
git commit -m "main: register referral handlers"
```

---

## Task 9: Update Help Message

**Files:**
- Modify: `bot/handlers/general.py:10-25`

**Step 1: Add /ref to help message**

```python
HELP_MSG = {
    "es": """📚 *Ayuda de SipSignal*

*Comandos Básicos:*
/start - Iniciar el bot
/help - Mostrar esta ayuda
/status - Ver estado del bot
/myid - Obtener tu ID
/mk - Datos de mercado
/p <símbolo> - Precio de cripto
/ta <símbolo> - Análisis técnico
/signal - Análisis técnico instantáneo de BTC
/chart [tf] - Ver gráfico (5m, 15m, 1h, 4h, 1D)
/journal - Historial de señales emitidas
/capital - Gestión de capital y drawdown
/lang - Cambiar idioma
/ref - Tu enlace de referido

*Para más información:* Contacta a un administrador.
"""
}
```

**Step 2: Commit**

```bash
git add bot/handlers/general.py
git commit -m "docs: add /ref to help message"
```

---

## Task 10: Run Full Test Suite

**Files:**
- All test files

**Step 1: Run all tests**

```bash
cd /home/mowgli/sipsignal
source venv/bin/activate
pytest --cov=. --cov-report=term-missing
```

Expected: All tests PASS, coverage maintained or improved

**Step 2: Run linter**

```bash
ruff check . --fix
ruff format .
```

Expected: No errors

**Step 3: Commit final changes**

```bash
git add .
git commit -m "test: add comprehensive referral system tests"
```

---

## Task 11: Manual Testing

**Step 1: Test /ref command**

```bash
# Start bot
python bot/main.py

# In Telegram:
/ref
```

Expected: Shows referral code and link

**Step 2: Test referral registration**

```bash
# Copy link from /ref output
# Open in new Telegram account or incognito
# Click link

# Should see welcome message
# Verify referred_by is set correctly in database
```

**Step 3: Test /ref stats**

```bash
/ref stats
```

Expected: Shows list of referred users

**Step 4: Test edge cases**

```bash
# Invalid referral code
/start INVALIDCODE123

# Self-referral (should be blocked)
# Multiple referrals from same user
```

---

## Task 12: Documentation Update

**Files:**
- Modify: `README.md` or `QWEN.md`

**Step 1: Add /ref to available commands**

Add to commands table in README.md:

```markdown
| Command | Description |
|---------|-------------|
| `/ref` | Generate referral link |
| `/ref stats` | View referral statistics |
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add /ref command to documentation"
```

---

## Summary

**Total Tasks:** 12
**Estimated Time:** 60-90 minutes
**Files Created:** 5
**Files Modified:** 5
**Tests Added:** 15+

**Key Dependencies:**
- `@python-testing-patterns` - For test structure
- `@postgresql-table-design` - For database schema
- `@python-error-handling` - For robust error handling

**Completion Criteria:**
- [ ] All tests pass
- [ ] Linting passes
- [ ] Manual testing successful
- [ ] Documentation updated
- [ ] Code committed with clear messages
