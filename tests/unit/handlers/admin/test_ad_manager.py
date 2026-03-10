"""Tests for ad manager handler."""

from bot.handlers.admin.ad_manager import ad_command


def test_ad_command_function_exists():
    """Test that ad_command function exists."""
    assert callable(ad_command)


def test_ad_command_is_async():
    """Test that ad_command is an async function."""
    import inspect

    assert inspect.iscoroutinefunction(ad_command)
