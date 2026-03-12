"""
Test to verify the root cause of /users command error.

ROOT CAUSE IDENTIFIED:
In user_management.py, line 47-48:
    usuarios = await user_repo.get_all()  # Returns LIST
    usuarios_dict = {str(u["user_id"]): u for u in usuarios}  # Dict created but not used

Then line 110:
    for _uid, u in usuarios.items():  # ERROR! usuarios is a LIST, not dict

The code should use usuarios_dict.items() instead of usuarios.items()
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture
def mock_container():
    """Create mock container."""
    container = MagicMock()
    container.user_repo = AsyncMock()
    container.user_watchlist_repo = AsyncMock()
    container.user_preference_repo = AsyncMock()
    container.user_usage_stats_repo = AsyncMock()
    return container


@pytest.fixture
def mock_admin_update():
    """Create mock admin update."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456
    update.effective_user = MagicMock()
    update.effective_user.username = "admin_user"
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.edit_text = AsyncMock()
    return update


@pytest.fixture
def mock_context(mock_container):
    """Create mock context with container."""
    context = MagicMock()
    context.bot_data = {"container": mock_container}
    return context


class TestRootCauseAnalysis:
    """Tests to verify the root cause of the /users error."""

    @pytest.mark.asyncio
    async def test_repository_returns_list_not_dict(
        self, mock_container, mock_admin_update, mock_context
    ):
        """
        Verify that the FIXED code works correctly when repository returns a LIST.

        After the fix, the code should use usuarios_dict.items() instead of usuarios.items().
        """
        from bot.handlers.admin.user_management import users

        # Repository returns a LIST of user dicts
        mock_container.user_repo.get_all.return_value = [
            {"user_id": 123, "language": "es"},
            {"user_id": 456, "language": "en"},
        ]

        # Mock ADMIN_CHAT_IDS and telemetry functions
        with (
            patch("bot.handlers.admin.user_management.ADMIN_CHAT_IDS", [123456]),
            patch(
                "bot.handlers.admin.user_management.get_retention_metrics_from_repo"
            ) as mock_retention,
            patch(
                "bot.handlers.admin.user_management.get_commands_per_user_from_repo"
            ) as mock_cmds,
            patch("bot.handlers.admin.user_management.get_daily_events_from_repo") as mock_daily,
            patch(
                "bot.handlers.admin.user_management.get_users_registration_stats_from_repo"
            ) as mock_reg,
        ):
            # Setup mock returns
            mock_retention.return_value = {
                "retention_7d": 50,
                "churn_rate": 10,
                "stickiness": 0.3,
            }
            mock_cmds.return_value = {"avg_per_user": 5}
            mock_daily.return_value = {"joins_today": 3, "commands_today": 15}
            mock_reg.return_value = {"with_registered_at": 100, "data_quality_pct": 95}

            # Mock the loading message
            mock_loading_msg = AsyncMock()
            mock_admin_update.message.reply_text.return_value = mock_loading_msg

            # After fix, this should NOT raise an error
            await users(mock_admin_update, mock_context)

            # Verify it completed successfully
            mock_admin_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_fixed_code_uses_dict_not_list(
        self, mock_container, mock_admin_update, mock_context
    ):
        """
        Test that the FIXED code uses usuarios_dict (dict) instead of usuarios (list).

        After the fix, this test should pass.
        """
        from bot.handlers.admin.user_management import users

        # Setup mock data
        mock_container.user_repo.get_all.return_value = [
            {
                "user_id": 123,
                "language": "es",
                "last_seen": "2026-03-12 10:00:00",
                "registered_at": "2026-03-01 10:00:00",
            }
        ]
        mock_container.user_watchlist_repo.get_coins.return_value = ["BTC"]
        mock_container.user_preference_repo.get_hbd_alerts.return_value = True

        # Mock the loading message
        mock_loading_msg = AsyncMock()
        mock_admin_update.message.reply_text.return_value = mock_loading_msg

        # After fix, this should NOT raise an error
        try:
            await users(mock_admin_update, mock_context)
            # If we get here, the fix is in place
            print("✓ Code is fixed - no AttributeError raised")
        except AttributeError as e:
            if "'list' object has no attribute 'items'" in str(e):
                print(f"✗ Bug still present: {e}")
                raise
            # Other AttributeErrors are different issues
            raise

    def test_verify_bug_in_source_code(self):
        """
        Verify that the bug has been FIXED in the source code.

        This test reads the source file and checks that the fix is in place.
        """
        with open("bot/handlers/admin/user_management.py") as f:
            content = f.read()

        lines = content.split("\n")

        # Find line where usuarios is assigned (should be list)
        usuarios_assignment_line = None
        for i, line in enumerate(lines):
            if "usuarios = await user_repo.get_all()" in line:
                usuarios_assignment_line = i
                break

        assert usuarios_assignment_line is not None, "Could not find usuarios assignment"

        # Find line where .items() is called - should use usuarios_dict, not usuarios
        usuarios_items_line = None
        usuarios_dict_items_line = None

        for i, line in enumerate(lines):
            if "usuarios.items()" in line and "usuarios_dict.items()" not in line:
                usuarios_items_line = i
            if "usuarios_dict.items()" in line:
                usuarios_dict_items_line = i

        # The fix: usuarios_dict.items() should be used, not usuarios.items()
        assert usuarios_dict_items_line is not None, "usuarios_dict.items() should be used"
        assert usuarios_items_line is None, "Bug still present: usuarios.items() found"

        # Verify that usuarios_dict is created
        usuarios_dict_created = False
        for line in lines:
            if "usuarios_dict = {" in line:
                usuarios_dict_created = True
                break

        assert usuarios_dict_created, "usuarios_dict should be created"

        print(f"✓ Fix verified: Line {usuarios_assignment_line + 1} creates list")
        print(f"✓ Fix verified: Line {usuarios_dict_items_line + 1} uses usuarios_dict.items()")
        print("✓ Bug is FIXED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
