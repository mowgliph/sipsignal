import json
import os
from unittest.mock import patch

import pytest

from bot.utils.telemetry import log_event


@pytest.fixture
def mock_events_log_path(tmp_path):
    log_path = tmp_path / "events_log.json"
    # Ensure directory exists for telemetry
    os.makedirs(os.path.dirname(str(log_path)), exist_ok=True)
    with patch("bot.utils.telemetry.EVENTS_LOG_PATH", str(log_path)):
        yield log_path


def test_log_event_success(mock_events_log_path):
    """
    Test that log_event correctly logs an event.
    """
    success = log_event("user_joined", 12345, {"source": "test"})
    assert success is True

    # Verify file content
    with open(str(mock_events_log_path)) as f:
        events = json.load(f)

    assert len(events) == 1
    assert events[0]["event_type"] == "user_joined"
    assert events[0]["user_id"] == "12345"
    assert events[0]["metadata"]["source"] == "test"


def test_log_event_invalid_type(mock_events_log_path):
    """
    Test that log_event returns False for invalid event types.
    """
    success = log_event("invalid_type", 12345)
    assert success is False

    # Verify file was not created or is empty
    if os.path.exists(str(mock_events_log_path)):
        with open(str(mock_events_log_path)) as f:
            events = json.load(f)
        assert len(events) == 0
