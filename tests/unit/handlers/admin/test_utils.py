"""Tests for admin utils module."""

from bot.handlers.admin.utils import _clean_markdown


def test_clean_markdown_basic():
    """Test basic markdown cleaning."""
    result = _clean_markdown("Hello *world*")
    assert result == "Hello  world "


def test_clean_markdown_underscores():
    """Test underscores are removed."""
    result = _clean_markdown("Hello _world_")
    assert result == "Hello  world "


def test_clean_markdown_backticks():
    """Test backticks are removed."""
    result = _clean_markdown("Hello `world`")
    assert result == "Hello  world "


def test_clean_markdown_brackets():
    """Test brackets are converted to parentheses."""
    result = _clean_markdown("Hello [world]")
    assert result == "Hello (world)"


def test_clean_markdown_none():
    """Test None input returns empty string."""
    result = _clean_markdown(None)
    assert result == ""


def test_clean_markdown_mixed():
    """Test mixed markdown characters."""
    result = _clean_markdown("Hello *world* _test_ `code` [link]")
    assert result == "Hello  world   test   code  (link)"
