# core/loops.py

from bot.utils.logger import logger


def get_logs_data() -> list[str]:
    """Devuelve las líneas de log REALES que están en memoria."""
    return logger.get_log_lines()
