"""Tests for role management database functions."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import AsyncMock, patch

from bot.db.users import (
    approve_role_change,
    deny_role_change,
    get_user_requested_role,
    request_role_change,
    set_user_role,
)


@pytest.mark.asyncio
async def test_set_user_role():
    """Test setting user role."""
    with patch("bot.db.users.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "UPDATE 1"

        result = await set_user_role(123, "trader")

        assert result is True
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0]
        assert "UPDATE users" in args[0]
        assert args[1] == 123
        assert args[2] == "trader"


@pytest.mark.asyncio
async def test_set_user_role_not_found():
    """Test setting role for non-existent user."""
    with patch("bot.db.users.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "UPDATE 0"

        result = await set_user_role(999, "trader")

        assert result is False


@pytest.mark.asyncio
async def test_request_role_change():
    """Test requesting a role change."""
    with patch("bot.db.users.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "UPDATE 1"

        result = await request_role_change(123, "trader")

        assert result is True
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0]
        assert "UPDATE users" in args[0]
        assert "role_change_pending" in args[0]
        assert args[1] == 123
        assert args[2] == "trader"


@pytest.mark.asyncio
async def test_approve_role_change():
    """Test approving a role change."""
    with patch("bot.db.users.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "UPDATE 1"

        result = await approve_role_change(123, "trader")

        assert result is True
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0]
        assert "UPDATE users" in args[0]
        assert args[1] == 123
        assert args[2] == "trader"


@pytest.mark.asyncio
async def test_deny_role_change():
    """Test denying a role change (should restore previous role)."""
    with patch("bot.db.users.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "UPDATE 1"

        result = await deny_role_change(123)

        assert result is True
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0]
        assert "UPDATE users" in args[0]
        assert "previous_role" in args[0]
        assert args[1] == 123


@pytest.mark.asyncio
async def test_get_user_requested_role():
    """Test getting user's requested role."""
    mock_user = {"requested_role": "trader"}

    with patch("bot.db.users.fetchrow", new_callable=AsyncMock) as mock_fetchrow:
        mock_fetchrow.return_value = mock_user

        result = await get_user_requested_role(123)

        assert result == "trader"
        mock_fetchrow.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_requested_role_not_found():
    """Test getting requested role for non-existent user."""
    with patch("bot.db.users.fetchrow", new_callable=AsyncMock) as mock_fetchrow:
        mock_fetchrow.return_value = None

        result = await get_user_requested_role(999)

        assert result is None
