"""Tests for ScreenshotAdapter."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import AsyncMock, patch

import pytest


class TestScreenshotAdapter:
    def test_hereda_de_chart_port(self):
        from bot.domain.ports.chart_port import ChartPort
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        assert issubclass(ScreenshotAdapter, ChartPort)

    def test_constructor_con_api_key(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        adapter = ScreenshotAdapter(api_key="test_key_123")
        assert adapter.api_key == "test_key_123"

    def test_constructor_fallback_a_config(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        with patch(
            "bot.infrastructure.telegram.screenshot_adapter.SCREENSHOT_API_KEY",
            "config_key",
        ):
            adapter = ScreenshotAdapter()
            assert adapter.api_key == "config_key"

    def test_constructor_api_key_sobreescribe_config(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        with patch(
            "bot.infrastructure.telegram.screenshot_adapter.SCREENSHOT_API_KEY",
            "config_key",
        ):
            adapter = ScreenshotAdapter(api_key="override_key")
            assert adapter.api_key == "override_key"

    @pytest.mark.asyncio
    async def test_capture_retorna_none_en_error(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        adapter = ScreenshotAdapter(api_key="test")
        with patch.object(adapter, "_capture_with_matplotlib", new_callable=AsyncMock) as mock_mpl:
            mock_mpl.return_value = None
            with patch.object(adapter, "_capture_with_api", new_callable=AsyncMock) as mock_api:
                mock_api.side_effect = Exception("API Error")
                result = await adapter.capture("BTCUSDT", "4h")
                assert result is None

    @pytest.mark.asyncio
    async def test_close_cierra_recursos(self):
        from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter

        adapter = ScreenshotAdapter(api_key="test")
        mock_session = AsyncMock()
        mock_session.closed = False
        adapter.session = mock_session
        adapter.data_fetcher = AsyncMock()

        await adapter.close()

        mock_session.close.assert_called_once()
        adapter.data_fetcher.close.assert_called_once()
