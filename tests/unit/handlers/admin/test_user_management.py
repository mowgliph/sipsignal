"""Tests for user management handler."""

from bot.handlers.admin.user_management import users


def test_users_function_exists():
    """Test that users function exists."""
    assert callable(users)


def test_users_is_async():
    """Test that users is an async function."""
    import inspect

    assert inspect.iscoroutinefunction(users)
