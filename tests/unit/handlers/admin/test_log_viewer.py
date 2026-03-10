"""Tests for log viewer handler."""

from bot.handlers.admin.log_viewer import logs_command


def test_logs_command_function_exists():
    """Test that logs_command function exists."""
    assert callable(logs_command)


def test_logs_command_is_async():
    """Test that logs_command is an async function."""
    import inspect

    assert inspect.iscoroutinefunction(logs_command)
