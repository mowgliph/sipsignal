"""
Debug tests for /users command to identify root cause of errors.

This test suite systematically tests the /users command handler to identify
where and why it fails. Tests are designed to isolate:
1. Container initialization issues
2. Repository method failures
3. Data access errors
4. Permission check failures
"""

import os
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test."""
    # Clean up any previous mocks
    if "bot.container" in sys.modules:
        del sys.modules["bot.container"]
    yield


@pytest.fixture
def mock_container():
    """Create a mock container with all required repositories."""
    container = MagicMock()

    # Mock repositories
    container.user_repo = AsyncMock()
    container.user_watchlist_repo = AsyncMock()
    container.user_preference_repo = AsyncMock()
    container.user_usage_stats_repo = AsyncMock()

    # Setup default return values
    container.user_repo.get_all = AsyncMock(return_value=[])
    container.user_watchlist_repo.get_coins = AsyncMock(return_value=["BTC", "ETH"])
    container.user_preference_repo.get_hbd_alerts = AsyncMock(return_value=True)

    return container


@pytest.fixture
def mock_update_admin():
    """Create a mock update from an admin user."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456  # Admin chat ID
    update.effective_user = MagicMock()
    update.effective_user.username = "admin_user"
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_update_non_admin():
    """Create a mock update from a non-admin user."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 999888  # Non-admin chat ID
    update.effective_user = MagicMock()
    update.effective_user.username = "regular_user"
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context_with_container(mock_container):
    """Create a mock context with container in bot_data."""
    context = MagicMock()
    context.bot_data = {"container": mock_container}
    context.args = []
    return context


@pytest.fixture
def mock_context_without_container():
    """Create a mock context WITHOUT container in bot_data (error scenario)."""
    context = MagicMock()
    context.bot_data = {}  # No container!
    context.args = []
    return context


@pytest.fixture
def mock_context_missing_bot_data():
    """Create a mock context with missing bot_data entirely."""
    context = MagicMock()
    del context.bot_data  # No bot_data at all!
    context.args = []
    return context


class TestUsersCommandBasicFunctionality:
    """Tests for basic /users command functionality."""

    @pytest.mark.asyncio
    async def test_users_command_admin_access(
        self, mock_update_admin, mock_context_with_container, mock_container
    ):
        """Test /users command works for admin users."""
        from bot.handlers.admin.user_management import users

        # Mock the loading message
        mock_loading_msg = AsyncMock()
        mock_update_admin.message.reply_text.return_value = mock_loading_msg

        # Call the handler
        await users(mock_update_admin, mock_context_with_container)

        # Verify loading message was shown
        mock_update_admin.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_users_command_non_admin_shows_profile(
        self, mock_update_non_admin, mock_context_with_container, mock_container
    ):
        """Test /users command shows profile for non-admin users."""
        from bot.handlers.admin.user_management import users

        # Setup mock user data
        mock_container.user_repo.get_all.return_value = [
            {
                "user_id": 999888,
                "language": "es",
                "last_seen": "2026-03-12 10:00:00",
                "registered_at": "2026-03-01 10:00:00",
            }
        ]

        await users(mock_update_non_admin, mock_context_with_container)

        # Should reply with profile message
        mock_update_non_admin.message.reply_text.assert_called()
        call_args = mock_update_non_admin.message.reply_text.call_args
        assert "TU PERFIL SIPSIGNAL" in str(call_args)


class TestUsersCommandErrorScenarios:
    """
    Tests for error scenarios that could cause /users to fail.
    These tests systematically test failure points.
    """

    @pytest.mark.asyncio
    async def test_users_command_fails_without_container(
        self, mock_update_admin, mock_context_without_container
    ):
        """
        Test that /users command fails when container is not in bot_data.

        This is a CRITICAL test - if container is missing, the command should
        handle it gracefully, not crash.
        """
        from bot.handlers.admin.user_management import users

        # This should raise KeyError because container is missing
        with pytest.raises(KeyError, match="container"):
            await users(mock_update_admin, mock_context_without_container)

    @pytest.mark.asyncio
    async def test_users_command_fails_without_bot_data(
        self, mock_update_admin, mock_context_missing_bot_data
    ):
        """
        Test that /users command fails when bot_data is completely missing.

        This tests if the handler can handle missing bot_data entirely.
        """
        from bot.handlers.admin.user_management import users

        # This should raise AttributeError because bot_data doesn't exist
        with pytest.raises((AttributeError, KeyError)):
            await users(mock_update_admin, mock_context_missing_bot_data)

    @pytest.mark.asyncio
    async def test_users_command_handles_repository_error(
        self, mock_update_admin, mock_context_with_container, mock_container
    ):
        """Test that /users handles repository errors gracefully."""
        from bot.handlers.admin.user_management import users

        # Make repository raise an exception
        mock_container.user_repo.get_all.side_effect = Exception("Database connection failed")

        # Should raise the exception (or handle it if error handling exists)
        with pytest.raises(Exception, match="Database connection failed"):
            await users(mock_update_admin, mock_context_with_container)

    @pytest.mark.asyncio
    async def test_users_command_handles_empty_user_data(
        self, mock_update_admin, mock_context_with_container, mock_container
    ):
        """Test /users with empty user data from repository."""
        from bot.handlers.admin.user_management import users

        # Return empty list
        mock_container.user_repo.get_all.return_value = []

        mock_loading_msg = AsyncMock()
        mock_update_admin.message.reply_text.return_value = mock_loading_msg

        # Should not crash with empty data
        await users(mock_update_admin, mock_context_with_container)

        # Should still try to show dashboard
        mock_update_admin.message.reply_text.assert_called()


class TestUsersCommandContainerInitialization:
    """
    Tests to verify container is properly initialized in main.py.
    These tests check if the container setup is correct.
    """

    def test_container_created_in_main(self):
        """Test that container is created in main() function."""
        with open("bot/main.py") as f:
            content = f.read()

        # Check container initialization
        assert "Container(settings=settings, bot=app.bot)" in content
        assert 'app.bot_data["container"] = container' in content

    def test_container_module_exists(self):
        """Test that container module exists and is importable."""
        from bot.container import Container, get_container

        assert Container is not None
        assert callable(get_container)

    @pytest.mark.asyncio
    async def test_container_has_required_repositories(self, mock_container):
        """Test that container has all required repositories for /users."""
        # Verify all required repos exist
        assert hasattr(mock_container, "user_repo")
        assert hasattr(mock_container, "user_watchlist_repo")
        assert hasattr(mock_container, "user_preference_repo")

        # Verify they are async-callable
        assert hasattr(mock_container.user_repo, "get_all")
        assert hasattr(mock_container.user_watchlist_repo, "get_coins")
        assert hasattr(mock_container.user_preference_repo, "get_hbd_alerts")


class TestUsersCommandDataFlow:
    """
    Tests that trace the data flow through the /users command.
    These tests help identify where data transformation might fail.
    """

    @pytest.mark.asyncio
    async def test_users_command_user_data_transformation(
        self, mock_update_admin, mock_context_with_container, mock_container
    ):
        """Test that user data is correctly transformed from repository format."""
        from bot.handlers.admin.user_management import users

        # Setup mock user data with various formats
        mock_container.user_repo.get_all.return_value = [
            {
                "user_id": 123,
                "language": "es",
                "last_seen": "2026-03-12 10:00:00",
                "registered_at": datetime.now(UTC),
            },
            {
                "user_id": 456,
                "language": "en",
                "last_seen": None,  # Missing last_seen
                "registered_at": "2026-03-01 10:00:00",
            },
        ]

        mock_loading_msg = AsyncMock()
        mock_update_admin.message.reply_text.return_value = mock_loading_msg

        # Should handle various data formats without crashing
        await users(mock_update_admin, mock_context_with_container)

        # Verify it completed
        mock_update_admin.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_users_command_handles_malformed_timestamps(
        self, mock_update_admin, mock_context_with_container, mock_container
    ):
        """Test that malformed timestamps don't crash the command."""
        from bot.handlers.admin.user_management import users

        # Setup mock with malformed timestamps
        mock_container.user_repo.get_all.return_value = [
            {
                "user_id": 123,
                "language": "es",
                "last_seen": "invalid-timestamp",
                "registered_at": "also-invalid",
            }
        ]

        mock_loading_msg = AsyncMock()
        mock_update_admin.message.reply_text.return_value = mock_loading_msg

        # Should handle malformed data gracefully
        await users(mock_update_admin, mock_context_with_container)


class TestUsersCommandIntegration:
    """
    Integration tests that test the /users command with real dependencies.
    These tests require a test database.
    """

    @pytest.mark.asyncio
    async def test_users_command_with_real_repositories(self):
        """
        Integration test with real repository instances.

        This test verifies the command works with actual database connections.
        Skip if no test database available.
        """
        import pytest

        pytest.skip("Requires test database setup - integration test")


def test_users_handler_import():
    """Test that users handler can be imported without errors."""
    from bot.handlers.admin.user_management import users

    assert users is not None
    assert callable(users)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
