import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.application.handle_drawdown import HandleDrawdown
from bot.domain.drawdown_state import DrawdownState
from bot.domain.user_config import UserConfig


class TestHandleDrawdown:
    def setup_method(self):
        self.mock_drawdown_repo = MagicMock()
        self.mock_user_config_repo = MagicMock()
        self.mock_notifier = AsyncMock()

        self.mock_drawdown_repo.get = AsyncMock()
        self.mock_drawdown_repo.save = AsyncMock()
        self.mock_drawdown_repo.reset = AsyncMock()
        self.mock_user_config_repo.get = AsyncMock()

        self.use_case = HandleDrawdown(
            drawdown_repo=self.mock_drawdown_repo,
            user_config_repo=self.mock_user_config_repo,
            notifier=self.mock_notifier,
        )

    @pytest.mark.asyncio
    async def test_execute_no_user_config_returns_none(self):
        self.mock_user_config_repo.get.return_value = None

        result = await self.use_case.execute(user_id=1, pnl_usdt=-50.0)

        assert result is None
        self.mock_drawdown_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_pnl_applies_to_state(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=5.0,
        )
        drawdown_state = DrawdownState(user_id=1)

        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state

        result = await self.use_case.execute(user_id=1, pnl_usdt=-50.0)

        assert result.current_drawdown_usdt == -50.0
        self.mock_drawdown_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_triggers_warning_at_50_percent(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=10.0,
        )
        drawdown_state = DrawdownState(user_id=1)

        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state

        await self.use_case.execute(user_id=1, pnl_usdt=-60.0)

        self.mock_notifier.send_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_triggers_pause_at_100_percent(self):
        user_config = UserConfig(
            user_id=1,
            chat_id=123,
            capital_total=1000.0,
            max_drawdown_percent=5.0,
        )
        drawdown_state = DrawdownState(user_id=1)

        self.mock_user_config_repo.get.return_value = user_config
        self.mock_drawdown_repo.get.return_value = drawdown_state

        result = await self.use_case.execute(user_id=1, pnl_usdt=-60.0)

        assert result.is_paused is True
        self.mock_notifier.send_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_calls_drawdown_repo_reset(self):
        self.mock_drawdown_repo.reset.return_value = DrawdownState(user_id=1)

        result = await self.use_case.reset(user_id=1)

        self.mock_drawdown_repo.reset.assert_called_once_with(1)
        assert result.user_id == 1

    @pytest.mark.asyncio
    async def test_resume_sets_paused_false_and_saves(self):
        drawdown_state = DrawdownState(user_id=1, is_paused=True)
        self.mock_drawdown_repo.get.return_value = drawdown_state

        await self.use_case.resume(user_id=1)

        assert drawdown_state.is_paused is False
        self.mock_drawdown_repo.save.assert_called_once_with(drawdown_state)
