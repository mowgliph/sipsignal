"""Tests para AccessManager middleware."""

import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset rate limiter singletons before each test."""
    from bot.utils.rate_limiter import AdminNotificationRateLimiter

    AdminNotificationRateLimiter._instance = None
    yield
    AdminNotificationRateLimiter._instance = None


@pytest.fixture
def access_manager():
    """Crea una instancia de AccessManager para testing."""
    from bot.core.access_manager import AccessManager

    return AccessManager(admin_chat_ids=[123456, 789012])


@pytest.fixture
def mock_update():
    """Crea un update mockeado."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 999888
    update.effective_user = MagicMock()
    update.effective_user.username = "test_user"
    update.message = MagicMock()
    return update


@pytest.fixture
def mock_application():
    """Crea una aplicación mockeada."""
    app = MagicMock()
    app.bot = MagicMock()
    app.bot.send_message = AsyncMock()
    return app


class TestAccessManagerInit:
    """Tests para la inicialización de AccessManager."""

    def test_init_with_admin_chat_ids(self):
        """Verifica que AccessManager se inicializa con admin_chat_ids."""
        from bot.core.access_manager import AccessManager

        manager = AccessManager(admin_chat_ids=[111, 222, 333])
        assert manager._admin_chat_ids == [111, 222, 333]

    def test_init_with_single_admin(self):
        """Verifica que funciona con un solo admin."""
        from bot.core.access_manager import AccessManager

        manager = AccessManager(admin_chat_ids=[999])
        assert len(manager._admin_chat_ids) == 1


class TestExtractChatId:
    """Tests para _extract_chat_id."""

    def test_extract_chat_id_from_update(self, access_manager, mock_update):
        """Verifica que extrae correctamente el chat_id."""
        chat_id = access_manager._extract_chat_id(mock_update)
        assert chat_id == 999888

    def test_extract_chat_id_returns_none_when_no_chat(self, access_manager):
        """Verifica que retorna None cuando no hay chat."""
        update = MagicMock()
        update.effective_chat = None
        chat_id = access_manager._extract_chat_id(update)
        assert chat_id is None


class TestExtractUsername:
    """Tests para _extract_username."""

    def test_extract_username_from_update(self, access_manager, mock_update):
        """Verifica que extrae correctamente el username."""
        username = access_manager._extract_username(mock_update)
        assert username == "test_user"

    def test_extract_username_returns_none_when_no_user(self, access_manager):
        """Verifica que retorna None cuando no hay usuario."""
        update = MagicMock()
        update.effective_user = None
        username = access_manager._extract_username(update)
        assert username is None


class TestIsMessageUpdate:
    """Tests para _is_message_update."""

    def test_is_message_update_returns_true(self, access_manager, mock_update):
        """Verifica que retorna True para mensajes regulares."""
        assert access_manager._is_message_update(mock_update) is True

    def test_is_message_update_returns_false_for_callback(self, access_manager):
        """Verifica que retorna False para callback queries."""
        update = MagicMock()
        update.message = None
        update.callback_query = MagicMock()
        assert access_manager._is_message_update(update) is False


class TestIsRequestExpired:
    """Tests para _is_request_expired."""

    def test_expired_when_requested_at_is_none(self, access_manager):
        """Verifica que retorna True cuando requested_at es None."""
        assert access_manager._is_request_expired(None) is True

    def test_not_expired_when_recent(self, access_manager):
        """Verifica que retorna False para solicitudes recientes."""
        recent_time = datetime.now(UTC) - timedelta(hours=1)
        assert access_manager._is_request_expired(recent_time) is False

    def test_expired_when_old(self, access_manager):
        """Verifica que retorna True para solicitudes de más de 24h."""
        old_time = datetime.now(UTC) - timedelta(hours=25)
        assert access_manager._is_request_expired(old_time) is True

    def test_expired_at_boundary(self, access_manager):
        """Verifica el límite exacto de 24 horas."""
        boundary_time = datetime.now(UTC) - timedelta(hours=24, seconds=1)
        assert access_manager._is_request_expired(boundary_time) is True

    def test_not_expired_at_boundary(self, access_manager):
        """Verifica justo antes del límite de 24 horas."""
        boundary_time = datetime.now(UTC) - timedelta(hours=23, minutes=59)
        assert access_manager._is_request_expired(boundary_time) is False

    def test_handles_naive_datetime(self, access_manager):
        """Verifica que maneja datetime sin timezone."""
        naive_time = datetime.now(UTC) - timedelta(hours=25)
        assert access_manager._is_request_expired(naive_time) is True


class TestHandleUpdate:
    """Tests para handle_update."""

    @pytest.mark.asyncio
    async def test_returns_true_for_non_message_updates(self, access_manager, mock_application):
        """Verifica que permite continuar para updates que no son mensajes."""
        update = MagicMock()
        update.effective_chat = None
        update.message = None

        result = await access_manager.handle_update(update, mock_application)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_for_callback_queries(self, access_manager, mock_application):
        """Verifica que permite continuar para callback queries."""
        update = MagicMock()
        update.effective_chat = MagicMock()
        update.effective_chat.id = 123
        update.effective_user = None
        update.message = None
        update.callback_query = MagicMock()

        result = await access_manager.handle_update(update, mock_application)
        assert result is True

    @pytest.mark.asyncio
    async def test_non_permitted_user_creates_request(
        self, access_manager, mock_update, mock_application
    ):
        """Verifica que usuarios no permitidos crean solicitud."""
        with (
            patch("bot.core.access_manager.get_user", return_value=None),
            patch(
                "bot.core.access_manager.create_user",
                return_value={"status": "non_permitted", "requested_at": None},
            ),
            patch("bot.core.access_manager.request_access", new_callable=AsyncMock) as mock_request,
            patch(
                "bot.core.access_manager.AccessManager._notify_admins", new_callable=AsyncMock
            ) as mock_notify,
            patch(
                "bot.core.access_manager.AccessManager._send_message", new_callable=AsyncMock
            ) as mock_send,
        ):
            result = await access_manager.handle_update(mock_update, mock_application)

            assert result is False
            mock_request.assert_called_once()
            mock_notify.assert_called_once()
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_pending_user_stops_processing(
        self, access_manager, mock_update, mock_application
    ):
        """Verifica que usuarios pendientes detienen el procesamiento."""
        pending_user = {
            "status": "pending",
            "requested_at": datetime.now(UTC) - timedelta(hours=1),
        }

        with (
            patch("bot.core.access_manager.get_user", return_value=pending_user),
            patch(
                "bot.core.access_manager.AccessManager._send_message", new_callable=AsyncMock
            ) as mock_send,
        ):
            result = await access_manager.handle_update(mock_update, mock_application)

            assert result is False
            mock_send.assert_called_once()
            # call_args[0] contains positional args: (bot, chat_id, text)
            assert "⏳" in mock_send.call_args[0][2]

    @pytest.mark.asyncio
    async def test_approved_user_allows_continuation(
        self, access_manager, mock_update, mock_application
    ):
        """Verifica que usuarios aprobados pueden continuar."""
        # Note: "approved" status is now replaced with role-based statuses
        # Using "trader" as an example of an approved user
        approved_user = {
            "status": "trader",
            "requested_at": datetime.now(UTC) - timedelta(hours=1),
        }

        with patch("bot.core.access_manager.get_user", return_value=approved_user):
            result = await access_manager.handle_update(mock_update, mock_application)
            assert result is True

    @pytest.mark.asyncio
    async def test_admin_user_allows_continuation(
        self, access_manager, mock_update, mock_application
    ):
        """Verifica que administradores pueden continuar."""
        admin_user = {
            "status": "admin",
            "requested_at": None,
        }

        with patch("bot.core.access_manager.get_user", return_value=admin_user):
            result = await access_manager.handle_update(mock_update, mock_application)
            assert result is True

    @pytest.mark.asyncio
    async def test_expired_pending_request_renotifies_admins(
        self, access_manager, mock_update, mock_application
    ):
        """Verifica que solicitudes expiradas re-notifican a admins."""
        expired_user = {
            "status": "pending",
            "requested_at": datetime.now(UTC) - timedelta(hours=25),
        }

        with (
            patch("bot.core.access_manager.get_user", return_value=expired_user),
            patch("bot.core.access_manager.request_access", new_callable=AsyncMock) as mock_request,
            patch(
                "bot.core.access_manager.AccessManager._notify_admins", new_callable=AsyncMock
            ) as mock_notify,
            patch("bot.core.access_manager.AccessManager._send_message", new_callable=AsyncMock),
        ):
            result = await access_manager.handle_update(mock_update, mock_application)

            assert result is False
            mock_request.assert_called_once()
            mock_notify.assert_called_once()


class TestNotifyAdmins:
    """Tests para _notify_admins."""

    @pytest.mark.asyncio
    async def test_notify_all_admins(self, access_manager):
        """Verifica que notifica a todos los admins."""
        bot = MagicMock()
        bot.send_message = AsyncMock()

        await access_manager._notify_admins(bot, 123456, "test_user")

        assert bot.send_message.call_count == len(access_manager._admin_chat_ids)

    @pytest.mark.asyncio
    async def test_notify_includes_user_info(self, access_manager):
        """Verifica que la notificación incluye información del usuario."""
        bot = MagicMock()
        bot.send_message = AsyncMock()

        await access_manager._notify_admins(bot, 123456, "test_user")

        for call in bot.send_message.call_args_list:
            text = call[1]["text"]
            assert "123456" in text
            assert "@test_user" in text
            # Note: Inline buttons are now used instead of text commands
            # Check that keyboard is provided with approve/deny callbacks
            assert "reply_markup" in call[1]
            keyboard = call[1]["reply_markup"]
            # Verify keyboard has approve/deny buttons
            assert len(keyboard.inline_keyboard) > 0
            first_row = keyboard.inline_keyboard[0]
            assert any("access_approve" in btn.callback_data for btn in first_row)
            assert any("access_deny" in btn.callback_data for btn in first_row)

    @pytest.mark.asyncio
    async def test_notify_handles_missing_username(self, access_manager):
        """Verifica que maneja correctamente cuando no hay username."""
        bot = MagicMock()
        bot.send_message = AsyncMock()

        await access_manager._notify_admins(bot, 123456, None)

        for call in bot.send_message.call_args_list:
            text = call[1]["text"]
            assert "123456" in text
            assert "@test_user" not in text

    @pytest.mark.asyncio
    async def test_notify_handles_send_error(self, access_manager):
        """Verifica que maneja errores al enviar notificaciones."""
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Send failed"))

        with patch("bot.core.access_manager.logger") as mock_logger:
            await access_manager._notify_admins(bot, 123456, "test_user")
            assert mock_logger.error.called


class TestSendMessage:
    """Tests para _send_message."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, access_manager):
        """Verifica envío exitoso de mensaje."""
        bot = MagicMock()
        bot.send_message = AsyncMock()

        await access_manager._send_message(bot, 123456, "Test message")

        bot.send_message.assert_called_once_with(
            chat_id=123456,
            text="Test message",
        )

    @pytest.mark.asyncio
    async def test_send_message_error(self, access_manager):
        """Verifica que maneja errores al enviar."""
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Send failed"))

        with patch("bot.core.access_manager.logger") as mock_logger:
            await access_manager._send_message(bot, 123456, "Test message")
            assert mock_logger.error.called


class TestGetOrCreateUser:
    """Tests para _get_or_create_user."""

    @pytest.mark.asyncio
    async def test_get_existing_user(self, access_manager):
        """Verifica que obtiene usuario existente."""
        existing_user = {"user_id": 123, "status": "approved"}

        with (
            patch("bot.core.access_manager.get_user", return_value=existing_user),
            patch("bot.core.access_manager.create_user", new_callable=AsyncMock) as mock_create,
        ):
            result = await access_manager._get_or_create_user(123, "test_user")

            assert result == existing_user
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_new_user(self, access_manager):
        """Verifica que crea usuario nuevo cuando no existe."""
        new_user = {"user_id": 123, "status": "non_permitted"}

        with (
            patch("bot.core.access_manager.get_user", return_value=None),
            patch("bot.core.access_manager.create_user", return_value=new_user),
        ):
            result = await access_manager._get_or_create_user(123, "test_user")

            assert result == new_user
