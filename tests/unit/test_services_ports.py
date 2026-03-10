"""Tests para los puertos de servicios externos."""

from abc import ABC
from datetime import UTC, datetime

import pytest

from bot.domain.ports.services import (
    AIAnalysisPort,
    ChartPort,
    MarketDataPort,
    NotifierPort,
)
from bot.domain.signal import Signal
from bot.domain.user_config import UserConfig


class TestMarketDataPort:
    def test_is_abstract(self):
        assert issubclass(MarketDataPort, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            MarketDataPort()


class TestChartPort:
    def test_is_abstract(self):
        assert issubclass(ChartPort, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            ChartPort()


class TestAIAnalysisPort:
    def test_is_abstract(self):
        assert issubclass(AIAnalysisPort, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AIAnalysisPort()


class TestNotifierPort:
    def test_is_abstract(self):
        assert issubclass(NotifierPort, ABC)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            NotifierPort()


class ConcreteMarketDataPort(MarketDataPort):
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int):
        return []


class ConcreteChartPort(ChartPort):
    async def capture(self, symbol: str, timeframe: str):
        return b"fake_image"


class ConcreteAIAnalysisPort(AIAnalysisPort):
    async def analyze_signal(self, signal: Signal) -> str:
        return "analisis"

    async def analyze_scenario(self) -> str:
        return "escenario"


class ConcreteNotifierPort(NotifierPort):
    async def send_signal(
        self,
        chat_id: int,
        signal: Signal,
        chart: bytes | None,
        ai_context: str,
        user_config: UserConfig,
    ) -> None:
        pass

    async def send_message(self, chat_id: int, text: str) -> None:
        pass

    async def send_warning(self, chat_id: int, text: str) -> None:
        pass


class TestConcreteImplementations:
    @pytest.mark.asyncio
    async def test_market_data_port_implementation(self):
        port = ConcreteMarketDataPort()
        result = await port.get_ohlcv("BTCUSDT", "15m", 100)
        assert result == []

    @pytest.mark.asyncio
    async def test_chart_port_implementation(self):
        port = ConcreteChartPort()
        result = await port.capture("BTCUSDT", "1h")
        assert result == b"fake_image"

    @pytest.mark.asyncio
    async def test_ai_analysis_port_implementation(self):
        port = ConcreteAIAnalysisPort()
        signal = Signal(
            id=1,
            direction="LONG",
            entry_price=50000.0,
            tp1_level=51000.0,
            sl_level=49000.0,
            rr_ratio=2.0,
            atr_value=500.0,
            supertrend_line=49500.0,
            timeframe="15m",
            detected_at=datetime.now(UTC),
        )
        result = await port.analyze_signal(signal)
        assert result == "analisis"

        scenario = await port.analyze_scenario()
        assert scenario == "escenario"

    @pytest.mark.asyncio
    async def test_notifier_port_implementation(self):
        port = ConcreteNotifierPort()
        signal = Signal(
            id=1,
            direction="LONG",
            entry_price=50000.0,
            tp1_level=51000.0,
            sl_level=49000.0,
            rr_ratio=2.0,
            atr_value=500.0,
            supertrend_line=49500.0,
            timeframe="15m",
            detected_at=datetime.now(UTC),
        )
        user_config = UserConfig(user_id=123, chat_id=123, capital_total=1000.0)

        await port.send_signal(123, signal, b"chart", "context", user_config)
        await port.send_message(123, "mensaje")
        await port.send_warning(123, "aviso")
