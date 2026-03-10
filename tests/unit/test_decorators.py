from unittest.mock import AsyncMock, patch

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


@handle_errors(exceptions=(TypeError,), fallback_value="fallback", alert_admin=False)
async def unhandled_exception():
    raise ValueError("Not a TypeError")


@pytest.mark.asyncio
async def test_handle_errors_alerts_admin():
    mock_notifier = AsyncMock()
    mock_container = AsyncMock()
    mock_container.notifier = mock_notifier

    # Mockear get_container() para que devuelva el contenedor mock
    with patch("bot.container.get_container", return_value=mock_container):

        @handle_errors(exceptions=(ValueError,), alert_admin=True)
        async def fail_with_alert():
            raise ValueError("Alert this")

        await fail_with_alert()
        # Verificar que se llamó al método de envío de mensajes al admin
        mock_notifier.send_message_to_admin.assert_called_once()
        args, _ = mock_notifier.send_message_to_admin.call_args
        assert "fail_with_alert" in args[0]
        assert "ValueError" in args[0]
