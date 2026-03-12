"""Tests for role_required decorator."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Message, Update
from telegram.ext import ContextTypes

from bot.utils.decorators import role_required


def create_mock_update(chat_id=123, message_text="/test"):
    """Create a mock update object."""
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock()
    update.effective_chat.id = chat_id
    update.message = MagicMock(spec=Message)
    update.message.text = message_text
    update.message.reply_text = AsyncMock()
    return update


def create_mock_context():
    """Create a mock context object."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_role_required_allows_access():
    """Test that role_required allows access for users with allowed roles."""
    # Create mock update and context
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    # Create decorated function
    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    # Mock get_user to return a trader
    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"status": "trader", "user_id": 123}

        result = await test_handler(update, context)

        assert result == "allowed"
        update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_role_required_denies_access():
    """Test that role_required denies access for users without allowed roles."""
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"status": "viewer", "user_id": 123}

        result = await test_handler(update, context)

        assert result is None
        update.message.reply_text.assert_called_once()
        assert "⛔ Acceso denegado" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_role_required_user_not_found():
    """Test that role_required denies access when user is not found."""
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None

        result = await test_handler(update, context)

        assert result is None
        update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_role_required_with_admin():
    """Test that role_required allows access for admin users."""
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"status": "admin", "user_id": 123}

        result = await test_handler(update, context)

        assert result == "allowed"
        update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_role_required_with_viewer():
    """Test that role_required denies access for viewer users when not in allowed list."""
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"status": "viewer", "user_id": 123}

        result = await test_handler(update, context)

        assert result is None
        update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_role_required_with_role_change_pending():
    """Test that role_required handles role_change_pending status correctly."""
    update = create_mock_update(chat_id=123)
    context = create_mock_context()

    @role_required(["trader", "admin"])
    async def test_handler(update, context):
        return "allowed"

    with patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"status": "role_change_pending", "user_id": 123}

        result = await test_handler(update, context)

        assert result is None
        update.message.reply_text.assert_called_once()
