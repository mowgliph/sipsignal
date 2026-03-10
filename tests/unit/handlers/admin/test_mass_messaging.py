"""Tests for mass messaging handlers."""

from bot.handlers.admin.mass_messaging import ms_conversation_handler, ms_start


def test_ms_conversation_handler_exists():
    """Test that the conversation handler is properly defined."""
    assert ms_conversation_handler is not None
    assert isinstance(ms_conversation_handler, object)


def test_ms_start_function_exists():
    """Test that ms_start function exists."""
    assert callable(ms_start)


def test_conversation_handler_has_entry_points():
    """Test that conversation handler has entry points."""
    assert ms_conversation_handler.entry_points is not None
    assert len(ms_conversation_handler.entry_points) > 0


def test_conversation_handler_has_states():
    """Test that conversation handler has states defined."""
    assert ms_conversation_handler.states is not None
    assert len(ms_conversation_handler.states) > 0
