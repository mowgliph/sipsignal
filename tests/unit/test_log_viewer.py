"""
Tests para el comando /logs.
"""

from bot.utils.logger import Logger


class TestLogViewer:
    """Tests para funcionalidad de visualización de logs."""

    def test_get_log_lines_formatted_returns_correct_count(self):
        """Test que get_log_lines_formatted devuelve la cantidad correcta de líneas."""
        logger_instance = Logger()
        logger_instance.LOG_LINES = []

        # Add 15 lines
        for i in range(15):
            logger_instance.info(f"Line {i}")

        # Request 10 lines
        formatted = logger_instance.get_log_lines_formatted(10)

        assert len(formatted) == 10
        # Should return the last 10 lines (Line 5 to Line 14)
        assert "Line 5" in formatted[0]
        assert "Line 14" in formatted[-1]

    def test_get_log_lines_formatted_with_emojis(self):
        """Test que las líneas formateadas incluyen emojis según el nivel."""
        logger_instance = Logger()
        logger_instance.LOG_LINES = []

        logger_instance.info("Info message")
        logger_instance.warning("Warning message")
        logger_instance.error("Error message")
        logger_instance.debug("Debug message")
        logger_instance.critical("Critical message")

        formatted = logger_instance.get_log_lines_formatted(5)

        assert len(formatted) == 5
        assert "🟢" in formatted[0]  # INFO
        assert "🟡" in formatted[1]  # WARNING
        assert "🔴" in formatted[2]  # ERROR
        assert "🔵" in formatted[3]  # DEBUG
        assert "🔥" in formatted[4]  # CRITICAL

    def test_get_log_lines_formatted_empty(self):
        """Test que get_log_lines_formatted maneja lista vacía."""
        logger_instance = Logger()
        logger_instance.LOG_LINES = []

        formatted = logger_instance.get_log_lines_formatted(10)

        assert formatted == []

    def test_get_log_lines_formatted_less_than_requested(self):
        """Test que get_log_lines_formatted devuelve menos si no hay suficientes."""
        logger_instance = Logger()
        logger_instance.LOG_LINES = []

        # Add only 3 lines
        logger_instance.info("Line 1")
        logger_instance.warning("Line 2")

        # Request 10 lines
        formatted = logger_instance.get_log_lines_formatted(10)

        # Should return only 2 lines
        assert len(formatted) == 2

    def test_log_lines_have_timestamp_format(self):
        """Test que las líneas de log tienen formato de timestamp correcto."""
        logger_instance = Logger()
        logger_instance.LOG_LINES = []

        logger_instance.info("Test message")

        formatted = logger_instance.get_log_lines_formatted(1)

        # Format: 🟢 [YYYY-MM-DD HH:MM:SS] | LEVEL | Message
        assert len(formatted) == 1
        line = formatted[0]
        assert "🟢" in line  # INFO emoji
        assert "] | INFO |" in line
        assert "Test message" in line
