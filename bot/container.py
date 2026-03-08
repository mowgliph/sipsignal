"""Dependency injection container for the bot."""

from telegram import Bot

from bot.application.get_scenario_analysis import GetScenarioAnalysis
from bot.application.get_signal_analysis import GetSignalAnalysis
from bot.application.handle_drawdown import HandleDrawdown
from bot.application.manage_journal import ManageJournal
from bot.application.run_signal_cycle import RunSignalCycle
from bot.core.config import Settings
from bot.domain.ports.market_data_port import MarketDataPort
from bot.infrastructure.binance.binance_adapter import BinanceAdapter
from bot.infrastructure.database.active_trade_repository import (
    PostgreSQLActiveTradeRepository,
)
from bot.infrastructure.database.signal_repository import PostgreSQLSignalRepository
from bot.infrastructure.database.user_repositories import (
    PostgreSQLDrawdownRepository,
    PostgreSQLUserConfigRepository,
    PostgreSQLUserPreferenceRepository,
    PostgreSQLUserRepository,
    PostgreSQLUserUsageStatsRepository,
    PostgreSQLUserWatchlistRepository,
)
from bot.infrastructure.groq.groq_adapter import GroqAdapter
from bot.infrastructure.telegram.screenshot_adapter import ScreenshotAdapter
from bot.infrastructure.telegram.telegram_notifier import TelegramNotifier


class Container:
    """Dependency injection container that wires all components."""

    def __init__(self, settings: Settings, bot: Bot):
        """
        Initialize the container with settings and bot instance.

        Args:
            settings: Application settings from bot.core.config
            bot: Telegram bot instance
        """
        self._settings = settings
        self._bot = bot

        self.market_data: MarketDataPort = BinanceAdapter()
        self.chart = ScreenshotAdapter(api_key=settings.screenshot_api_key)
        self.ai = GroqAdapter(api_key=settings.groq_api_key)
        self.notifier = TelegramNotifier()

        self.signal_repo = PostgreSQLSignalRepository()
        self.trade_repo = PostgreSQLActiveTradeRepository()
        self.user_config_repo = PostgreSQLUserConfigRepository()
        self.drawdown_repo = PostgreSQLDrawdownRepository()
        self.user_repo = PostgreSQLUserRepository()
        self.user_watchlist_repo = PostgreSQLUserWatchlistRepository()
        self.user_preference_repo = PostgreSQLUserPreferenceRepository()
        self.user_usage_stats_repo = PostgreSQLUserUsageStatsRepository()

        self.run_signal_cycle = RunSignalCycle(
            market_data=self.market_data,
            signal_repo=self.signal_repo,
            trade_repo=self.trade_repo,
            chart=self.chart,
            ai=self.ai,
            notifier=self.notifier,
            admin_chat_ids=settings.admin_chat_ids,
        )
        self.handle_drawdown = HandleDrawdown(
            drawdown_repo=self.drawdown_repo,
            user_config_repo=self.user_config_repo,
            notifier=self.notifier,
        )
        self.get_signal_analysis = GetSignalAnalysis(
            market_data=self.market_data,
            chart=self.chart,
            ai=self.ai,
        )
        self.get_scenario_analysis = GetScenarioAnalysis(
            market_data=self.market_data,
            ai=self.ai,
        )
        self.manage_journal = ManageJournal(signal_repo=self.signal_repo)
