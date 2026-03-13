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
        assert user_context.get() == ""

    def test_context_isolation(self):
        """Test que el contexto se aísla entre tareas."""
        token1 = user_context.set("[Chat:111] ")
        assert user_context.get() == "[Chat:111] "

        token2 = user_context.set("[Chat:222] ")
        assert user_context.get() == "[Chat:222] "

        user_context.reset(token2)
        assert user_context.get() == "[Chat:111] "

        user_context.reset(token1)
        assert user_context.get() == ""

    def test_context_empty_by_default(self):
        """Test que el contexto está vacío por defecto."""
        assert user_context.get() == ""


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


class TestLoggerMemorySync:
    """Tests para sincronización de memoria y archivo."""

    def test_info_adds_to_memory(self):
        """Test que info() agrega a memoria."""
        logger_instance = Logger()
        initial_count = len(logger_instance.LOG_LINES)

        logger_instance.info("Test info message")

        assert len(logger_instance.LOG_LINES) == initial_count + 1
        assert "INFO" in logger_instance.LOG_LINES[-1]
        assert "Test info message" in logger_instance.LOG_LINES[-1]

    def test_warning_adds_to_memory(self):
        """Test que warning() agrega a memoria."""
        logger_instance = Logger()
        initial_count = len(logger_instance.LOG_LINES)

        logger_instance.warning("Test warning message")

        assert len(logger_instance.LOG_LINES) == initial_count + 1
        assert "WARNING" in logger_instance.LOG_LINES[-1]

    def test_error_adds_to_memory(self):
        """Test que error() agrega a memoria."""
        logger_instance = Logger()
        initial_count = len(logger_instance.LOG_LINES)

        logger_instance.error("Test error message")

        assert len(logger_instance.LOG_LINES) == initial_count + 1
        assert "ERROR" in logger_instance.LOG_LINES[-1]

    def test_get_log_lines_formatted(self):
        """Test que get_log_lines_formatted devuelve líneas con emojis."""
        logger_instance = Logger()
        logger_instance.info("Info test")
        logger_instance.warning("Warning test")
        logger_instance.error("Error test")

        formatted = logger_instance.get_log_lines_formatted(3)

        assert len(formatted) == 3
        assert "🟢" in formatted[0]  # INFO
        assert "🟡" in formatted[1]  # WARNING
        assert "🔴" in formatted[2]  # ERROR

    def test_memory_buffer_max(self):
        """Test que el buffer de memoria respeta el máximo."""
        logger_instance = Logger()
        # Clear existing lines
        logger_instance.LOG_LINES = []

        # Add more than LOG_MAX lines
        for i in range(Logger.LOG_MAX + 20):
            logger_instance.info(f"Line {i}")

        # Should have exactly LOG_MAX lines
        assert len(logger_instance.LOG_LINES) == Logger.LOG_MAX
        # Oldest lines should be removed (Line 20 should be first, not Line 0)
        assert "Line 20" in logger_instance.LOG_LINES[0]
