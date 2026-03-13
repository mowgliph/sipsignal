"""Tests for referral handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update

from bot.handlers.referral_handler import ref_command


def create_mock_update(chat_id=12345):
    """Create a mock update object."""
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock()
    update.effective_chat.id = chat_id
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


def create_mock_context():
    """Create a mock context object."""
    return MagicMock()


@pytest.mark.asyncio
async def test_ref_command_generates_code():
    """Test /ref generates code for user without one."""
    update = create_mock_update(chat_id=12345)
    context = create_mock_context()

    async def mock_generate(self, user_id):
        return "TEST1234"

    async def mock_get_stats(user_id):
        return {"count": 0, "last_referred": None}

    with (
        patch("bot.utils.decorators.get_user", new_callable=AsyncMock) as mock_get_user,
        patch(
            "bot.infrastructure.database.referral_repository.PostgreSQLReferralRepository.get_referrer_code",
            return_value=None,
        ),
        patch(
            "bot.infrastructure.database.referral_repository.PostgreSQLReferralRepository.generate_referrer_code",
            mock_generate,
        ),
        patch(
            "bot.handlers.referral_handler._get_referral_stats",
            mock_get_stats,
        ),
    ):
        mock_get_user.return_value = {"status": "approved", "user_id": 12345}
        await ref_command(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "TEST1234" in call_args
    assert "t.me/sipsignalbot?start=TEST1234" in call_args
