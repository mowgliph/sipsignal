from unittest.mock import patch

import pytest

from bot.utils.telemetry import log_event


@pytest.fixture
def mock_events_log_path(tmp_path):
    log_path = tmp_path / "events_log.json"
    with patch("bot.utils.telemetry.EVENTS_LOG_PATH", str(log_path)):
        yield log_path


def test_log_event_crashes_due_to_lock(mock_events_log_path):
    """
    Test that log_event crashes because it calls _file_lock.release()
    synchronously on an asyncio.Lock without acquiring it.
    """
    # This should raise RuntimeError: Lock is not acquired.
    # because log_event calls _file_lock.release() in finally block
    # but never acquires it.
    with pytest.raises(RuntimeError, match="Lock is not acquired"):
        log_event("user_joined", 12345)
