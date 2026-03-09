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
async def test_handle_errors_does_not_catch_other_exceptions():
    with pytest.raises(ValueError):
        await unhandled_exception()
