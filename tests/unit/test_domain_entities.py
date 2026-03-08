from datetime import datetime

from bot.domain.drawdown_state import DrawdownState
from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig


# Tests for Signal
def test_signal_is_valid_long():
    signal = Signal(
        id=1,
        direction="LONG",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49500.0,
        rr_ratio=2.0,
        atr_value=500.0,
        supertrend_line=49000.0,
        timeframe="15m",
        detected_at=datetime.now(),
    )
    assert signal.is_valid() is True


def test_signal_invalid_direction():
    signal = Signal(
        id=2,
        direction="HOLD",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49500.0,
        rr_ratio=2.0,
        atr_value=500.0,
        supertrend_line=49000.0,
        timeframe="15m",
        detected_at=datetime.now(),
    )
    assert signal.is_valid() is False


def test_signal_risk_amount():
    signal = Signal(
        id=3,
        direction="LONG",
        entry_price=50000.0,
        tp1_level=51000.0,
        sl_level=49500.0,
        rr_ratio=2.0,
        atr_value=500.0,
        supertrend_line=49000.0,
        timeframe="15m",
        detected_at=datetime.now(),
    )
    # 1.0% of 10000 is 100.0
    assert signal.risk_amount(10000, 1.0) == 100.0


def test_signal_position_size():
    signal = Signal(
        id=4,
        direction="LONG",
        entry_price=100.0,
        tp1_level=110.0,
        sl_level=90.0,
        rr_ratio=1.0,
        atr_value=5.0,
        supertrend_line=85.0,
        timeframe="15m",
        detected_at=datetime.now(),
    )
    # Risk = 1% of 1000 = 10
    # Stop distance = 100 - 90 = 10
    # Size = 10 / 10 = 1.0
    assert signal.position_size(1000, 1.0) == 1.0


# Tests for DrawdownState
def test_apply_pnl_loss():
    state = DrawdownState(user_id=1)
    state.apply_pnl(-50.0, 1000.0)
    assert state.current_drawdown_usdt == -50.0
    assert state.losses_count == 1
    assert state.current_drawdown_percent == -5.0


def test_apply_pnl_profit():
    state = DrawdownState(user_id=1)
    state.apply_pnl(50.0, 1000.0)
    assert state.current_drawdown_usdt == 50.0
    assert state.losses_count == 0
    assert state.current_drawdown_percent == 5.0


def test_should_warn_at_50_percent():
    # 2.5% drawdown with limit 5% is 50% of the limit
    state = DrawdownState(user_id=1, current_drawdown_percent=-2.5)
    assert state.should_warn(5.0) is True


def test_should_pause_at_100_percent():
    # 5.1% drawdown with limit 5% is > 100% of the limit
    state = DrawdownState(user_id=1, current_drawdown_percent=-5.1)
    assert state.should_pause(5.0) is True


# Tests for UserConfig
def test_max_drawdown_usdt():
    config = UserConfig(user_id=1, chat_id=123, capital_total=1000.0, max_drawdown_percent=5.0)
    assert config.max_drawdown_usdt() == 50.0


def test_warning_threshold():
    config = UserConfig(user_id=1, chat_id=123, capital_total=1000.0, max_drawdown_percent=5.0)
    # 50% of 50 is 25.0
    assert config.warning_threshold_usdt() == 25.0
