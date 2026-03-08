import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock
from bot.application.run_signal_cycle import RunSignalCycle
from bot.application.handle_drawdown import HandleDrawdown
from bot.application.manage_journal import ManageJournal
from bot.domain.user_config import UserConfig
from bot.domain.drawdown_state import DrawdownState
from bot.domain.active_trade import ActiveTrade

@pytest.mark.asyncio
async def test_run_signal_cycle_returns_none_when_active_trade_exists():
    market_data = AsyncMock()
    signal_repo = AsyncMock()
    trade_repo = AsyncMock()
    chart = AsyncMock()
    ai = AsyncMock()
    notifier = AsyncMock()
    
    # Mock trade_repo.get_active() to return an ActiveTrade
    trade_repo.get_active.return_value = MagicMock(spec=ActiveTrade)
    
    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, [123])
    user_config = UserConfig(user_id=1, chat_id=123)
    
    result = await use_case.execute(user_config)
    
    assert result is None
    market_data.get_ohlcv.assert_not_called()

@pytest.mark.asyncio
async def test_run_signal_cycle_returns_none_when_no_signal():
    market_data = AsyncMock()
    signal_repo = AsyncMock()
    trade_repo = AsyncMock()
    chart = AsyncMock()
    ai = AsyncMock()
    notifier = AsyncMock()
    
    trade_repo.get_active.return_value = None
    
    # Mock market_data.get_ohlcv() to return a DataFrame that won't trigger a signal
    df = pd.DataFrame({
        "open": [100.0] * 200,
        "high": [105.0] * 200,
        "low": [95.0] * 200,
        "close": [100.0] * 200,
        "volume": [1000.0] * 200
    })
    market_data.get_ohlcv.return_value = df
    
    use_case = RunSignalCycle(market_data, signal_repo, trade_repo, chart, ai, notifier, [123])
    user_config = UserConfig(user_id=1, chat_id=123)
    
    result = await use_case.execute(user_config)
    
    assert result is None

@pytest.mark.asyncio
async def test_handle_drawdown_warns_at_50_percent():
    drawdown_repo = AsyncMock()
    user_config_repo = AsyncMock()
    notifier = AsyncMock()
    
    user_id = 1
    config = UserConfig(user_id=user_id, chat_id=123, capital_total=1000.0, max_drawdown_percent=5.0)
    user_config_repo.get.return_value = config
    
    # Drawdown state at 2.4% (just below 50% of 5%)
    # Applying -2.5 USDT loss to a state that has 0.0 drawdown
    state = DrawdownState(user_id=user_id, current_drawdown_percent=-2.4, current_drawdown_usdt=-24.0)
    drawdown_repo.get.return_value = state
    
    use_case = HandleDrawdown(drawdown_repo, user_config_repo, notifier)
    
    # Apply -2.0 USDT loss -> Total drawdown = -26.0 USDT = -2.6% (which is > 2.5% warning limit)
    await use_case.execute(user_id, -2.0)
    
    notifier.send_warning.assert_called_once()
    assert "Warning" in notifier.send_warning.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_drawdown_pauses_at_100_percent():
    drawdown_repo = AsyncMock()
    user_config_repo = AsyncMock()
    notifier = AsyncMock()
    
    user_id = 1
    config = UserConfig(user_id=user_id, chat_id=123, capital_total=1000.0, max_drawdown_percent=5.0)
    user_config_repo.get.return_value = config
    
    # Drawdown state at 4.9%
    state = DrawdownState(user_id=user_id, current_drawdown_percent=-4.9, current_drawdown_usdt=-49.0)
    drawdown_repo.get.return_value = state
    
    use_case = HandleDrawdown(drawdown_repo, user_config_repo, notifier)
    
    # Apply -2.0 USDT loss -> Total drawdown = -51.0 USDT = -5.1% (which is > 5.0% pause limit)
    await use_case.execute(user_id, -2.0)
    
    # It might be called for warning too if it passed through it, but usually logic is if/elif
    notifier.send_warning.assert_called_once()
    assert "🚨 SISTEMA PAUSADO" in notifier.send_warning.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_drawdown_reset_calls_repo():
    drawdown_repo = AsyncMock()
    user_config_repo = AsyncMock()
    notifier = AsyncMock()
    
    use_case = HandleDrawdown(drawdown_repo, user_config_repo, notifier)
    await use_case.reset(1)
    
    drawdown_repo.reset.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_manage_journal_mark_taken_calls_repo():
    signal_repo = AsyncMock()
    use_case = ManageJournal(signal_repo)
    
    await use_case.mark_taken(1)
    
    signal_repo.update_status.assert_called_once_with(1, "TOMADA")
