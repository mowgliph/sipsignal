"""
Tests para sistema de logging unificado.
"""

from bot.utils.logger import Logger, user_context
from bot.utils.logger import logger as unified_logger


class TestLoggerContext:
    """Tests para inyección de contexto."""

    def test_context_injection(self):
        """Test que el contexto se inyecta correctamente."""
        token = user_context.set("[Chat:123] [User:456] ")
        assert user_context.get() == "[Chat:123] [User:456] "
        user_context.reset(token)
        assert user_context.get() is None

    def test_context_isolation(self):
        """Test que el contexto se aísla entre tareas."""
        token1 = user_context.set("[Chat:111] ")
        assert user_context.get() == "[Chat:111] "

        token2 = user_context.set("[Chat:222] ")
        assert user_context.get() == "[Chat:222] "

        user_context.reset(token2)
        assert user_context.get() == "[Chat:111] "

        user_context.reset(token1)
        assert user_context.get() is None

    def test_context_empty_by_default(self):
        """Test que el contexto está vacío por defecto."""
        assert user_context.get() is None


class TestLoggerClass:
    """Tests para Logger class."""

    def test_logger_instance_creation(self):
        """Test que se puede crear instancia de Logger."""
        logger_instance = Logger()
        assert logger_instance is not None

    def test_log_user_action(self):
        """Test método log_user_action."""
        logger_instance = Logger()
        # Should not raise
        logger_instance.log_user_action("test_action", user_id=123)

    def test_add_log_line(self):
        """Test método add_log_line."""
        logger_instance = Logger()
        initial_count = len(logger_instance.LOG_LINES)

        logger_instance.add_log_line("Test message")

        assert len(logger_instance.LOG_LINES) == initial_count + 1

    def test_get_log_lines(self):
        """Test método get_log_lines."""
        logger_instance = Logger()
        logger_instance.add_log_line("Line 1")
        logger_instance.add_log_line("Line 2")
        logger_instance.add_log_line("Line 3")

        lines = logger_instance.get_log_lines(2)
        assert len(lines) == 2
        assert "Line 2" in lines[0]
        assert "Line 3" in lines[1]

    def test_inject_context(self):
        """Test método inject_context."""
        logger_instance = Logger()
        token = logger_instance.inject_context(chat_id=123, user_id=456)
        assert user_context.get() == "[Chat:123, User:456] "
        user_context.reset(token)

    def test_inject_context_chat_only(self):
        """Test inject_context con solo chat_id."""
        logger_instance = Logger()
        token = logger_instance.inject_context(chat_id=789)
        assert user_context.get() == "[Chat:789] "
        user_context.reset(token)

    def test_inject_context_user_only(self):
        """Test inject_context con solo user_id."""
        logger_instance = Logger()
        token = logger_instance.inject_context(user_id=999)
        assert user_context.get() == "[User:999] "
        user_context.reset(token)

    def test_inject_context_empty(self):
        """Test inject_context sin parámetros."""
        logger_instance = Logger()
        token = logger_instance.inject_context()
        assert user_context.get() == ""
        user_context.reset(token)


class TestLoggerConfiguration:
    """Tests para configuración del logger."""

    def test_logger_exports_exist(self):
        """Test que las exportaciones existen."""
        from bot.utils.logger import Logger, bot_logger, logger, user_context

        assert logger is not None
        assert Logger is not None
        assert user_context is not None
        assert bot_logger is not None

    def test_logger_is_loguru_instance(self):
        """Test que logger es instancia de loguru."""
        # Should have loguru methods
        assert hasattr(unified_logger, "info")
        assert hasattr(unified_logger, "error")
        assert hasattr(unified_logger, "warning")
        assert hasattr(unified_logger, "debug")
