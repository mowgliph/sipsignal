# utils/logger.py

import logging
import os
import sys
import traceback
from datetime import UTC, datetime

# --- 1. CONFIGURACIÓN DE RUTAS (Original de logger.py) ---
# Mantenemos esto idéntico para no romper la estructura de carpetas
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE_NAME = "sipsignal.log"  # Nombre del archivo de log
LOG_FILE_PATH = os.path.join(LOGS_DIR, LOG_FILE_NAME)
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "sipsignal_errors.log")

# Asegurar que la carpeta logs exista (Lógica original mejorada)
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)
    print(f"📁 Carpeta logs creada en: {LOGS_DIR}")

# --- 2. MOTOR DE LOGGING (Loguru con Fallback) ---
try:
    from loguru import logger as _loguru_logger

    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    # Fallback a logging estándar si loguru no está instalado
    # Esto asegura que el bot no crashee si faltan dependencias
    _std_logger = logging.getLogger("sipsignal_fallback")
    _std_logger.setLevel(logging.INFO)
    if not _std_logger.handlers:
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setFormatter(logging.Formatter("[%(asctime)s] | %(levelname)s | %(message)s"))
        _std_logger.addHandler(_handler)

    # Proxy simple para imitar loguru si no está presente
    class _StdLoggerProxy:
        def debug(self, msg, *args, **kwargs):
            _std_logger.debug(msg)

        def info(self, msg, *args, **kwargs):
            _std_logger.info(msg)

        def warning(self, msg, *args, **kwargs):
            _std_logger.warning(msg)

        def error(self, msg, *args, **kwargs):
            _std_logger.error(msg)

        def critical(self, msg, *args, **kwargs):
            _std_logger.critical(msg)

        def remove(self):
            pass

        def add(self, *args, **kwargs):
            pass

    _loguru_logger = _StdLoggerProxy()
    print("⚠️ ADVERTENCIA: 'loguru' no está instalado. Usando logging estándar básico.")


class Logger:
    """
    Sistema de logging unificado. Integra la gestión de rutas de tu logger original
    con la potencia de estructuración del nuevo sistema.
    """

    # Log en memoria para comando /status (máximo 45 líneas)
    LOG_MAX = 45
    LOG_LINES: list[str] = []

    def __init__(self):
        self.monitoring_handler = None
        self.log_file_path = LOG_FILE_PATH

        # Configuración inicial
        self._setup_logger()
        sys.excepthook = self._handle_unhandled_exception

    def add_log_line(self, linea: str) -> None:
        """
        Agrega una línea a los logs en memoria para el comando /status.

        Args:
            linea: El mensaje a registrar.
        """
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] | {linea}"
        self.LOG_LINES.append(log_entry)
        if len(self.LOG_LINES) > self.LOG_MAX:
            del self.LOG_LINES[0]
        print(log_entry)
        self.info(linea)

    def get_log_lines(self, n_lines: int = 15) -> list[str]:
        """
        Obtiene las últimas N líneas de los logs en memoria.

        Args:
            n_lines: Número de líneas a retornar.

        Returns:
            Lista de strings con las últimas líneas de log.
        """
        return self.LOG_LINES[-n_lines:] if self.LOG_LINES else []

    def _setup_logger(self):
        """Configura los handlers (Consola y Archivo)."""
        if not HAS_LOGURU:
            return  # Ya está configurado el fallback arriba

        _loguru_logger.remove()  # Limpiar handlers por defecto

        # 1. Handler de Consola (Colorizado y limpio)
        _loguru_logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True,
        )

        # 2. Handler de Archivo Principal (Rotativo como en tu original)
        # Rotación a 5MB y retención de 5 archivos (similar a tu backupCount=5)
        _loguru_logger.add(
            self.log_file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
            rotation="5 MB",
            retention="10 days",
            compression="zip",  # Comprime logs viejos para ahorrar espacio
            encoding="utf-8",
        )

        # 3. Handler de Errores (Separado para facilitar depuración)
        _loguru_logger.add(
            ERROR_LOG_PATH,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="5 MB",
            retention="30 days",
            encoding="utf-8",
        )

    def _handle_unhandled_exception(self, exc_type, exc_value, exc_traceback):
        """
        Intercepta errores no controlados (los que salen en consola)
        y los registra limpiamente en el log antes de que el bot muera.
        """
        # Ignorar interrupciones de teclado (Ctrl+C) para permitir salir limpiamente
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 1. Extraer la información precisa de dónde ocurrió el error
        # traceback.extract_tb devuelve una lista de 'Frames'. El último es el del error.
        tb_summary = traceback.extract_tb(exc_traceback)

        if tb_summary:
            last_frame = tb_summary[-1]
            file_name = os.path.basename(last_frame.filename)
            line_no = last_frame.lineno
            func_name = last_frame.name
            code_line = last_frame.line
        else:
            file_name = "Desconocido"
            line_no = "?"
            func_name = "?"
            code_line = "No info"

        # 2. Crear un mensaje visualmente limpio para el Log
        header_msg = (
            f"🛑 CRASH NO CONTROLADO DETECTADO\n"
            f"   📂 Archivo: {file_name} | Línea: {line_no}\n"
            f"   ⚙️ Función: {func_name}\n"
            f"   👉 Código:  {code_line}\n"
            f"   ❌ Error:   {exc_type.__name__}: {str(exc_value)}"
        )

        # 3. Registrar usando tu método existente (que ya adjunta el traceback completo al final)
        # Pasamos 'exc_value' (la excepción real) para que se guarde el stack trace completo en el archivo
        self.error(header_msg, error=exc_value)

    def _format_clean_traceback(self, error: Exception) -> str:
        """Limpia el traceback para mostrar solo lo relevante de TU código."""
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        # Aquí podrías filtrar líneas de librerías externas si quisieras
        tb_str = "".join(tb_lines).strip()
        if len(tb_str) > 2000:
            tb_str = tb_str[:2000] + "\n... (traceback truncado)"
        return tb_str

    def set_monitoring_handler(self, monitoring_handler):
        """Para integrar con sistemas de monitoreo en tiempo real si los tienes."""
        self.monitoring_handler = monitoring_handler

    # --- MÉTODOS GENÉRICOS ---

    def info(self, message: str, *args, **kwargs):
        _loguru_logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        _loguru_logger.warning(message, *args, **kwargs)

    def error(self, message: str | Exception, error: Exception | None = None, *args, **kwargs):
        """Log de error inteligente. Acepta (mensaje) o (mensaje, excepcion) o (excepcion)."""
        if isinstance(message, Exception) and error is None:
            error = message
            message = str(message)

        if error:
            tb_str = self._format_clean_traceback(error)
            message = f"{message}\n  ╚══ 💥 Detalles:\n{tb_str}"

        _loguru_logger.error(message, *args, **kwargs)

    # --- MÉTODOS ESPECÍFICOS DEL BOT (Integrados del código nuevo) ---

    def log_bot_event(self, level: str, message: str, user_id: int | None = None, **kwargs):
        """Registra un evento específico del bot."""
        log_method = getattr(_loguru_logger, level.lower(), _loguru_logger.info)
        extra_info = f"[User:{user_id}]" if user_id else ""
        full_msg = f"{extra_info} {message}".strip()

        log_method(full_msg, **kwargs)

        if self.monitoring_handler:
            self.monitoring_handler.add_log(level.upper(), full_msg, user_id)

    def log_user_action(self, action: str, user_id: int, details: str | None = None):
        """Ej: logger.log_user_action('start_bot', 123456)"""
        msg = f"User Action: {action}"
        if details:
            msg += f" - {details}"
        self.log_bot_event("INFO", msg, user_id)

    # --- UTILIDADES DE LECTURA ---
    def get_last_logs(self, lines: int = 15) -> str:
        """Devuelve las últimas líneas del archivo de log."""
        if not os.path.exists(self.log_file_path):
            return "📂 El archivo de log aún no existe."
        try:
            with open(self.log_file_path, encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"❌ Error leyendo logs: {str(e)}"

    def get_log_lines_formatted(self, lines: int = 15) -> list[str]:
        """
        Obtiene las últimas líneas de log en memoria con formato para /status.

        Args:
            lines: Número de líneas a retornar.

        Returns:
            Lista de strings formateados con emojis según nivel de log.
        """
        log_lines = self.get_log_lines(lines)
        formatted_lines = []

        for line in log_lines:
            line_upper = line.upper()
            if "ERROR" in line_upper:
                emoji = "🔴"
            elif "WARNING" in line_upper:
                emoji = "🟡"
            elif "INFO" in line_upper:
                emoji = "🟢"
            elif "DEBUG" in line_upper:
                emoji = "🔵"
            elif "CRITICAL" in line_upper:
                emoji = "🔥"
            else:
                emoji = "⚪"

            formatted_lines.append(f"{emoji} {line}")

        return formatted_lines


# --- INSTANCIA GLOBAL ---
logger = Logger()


# --- COMPATIBILIDAD RETROACTIVA (CRUCIAL PARA TU PROYECTO ACTUAL) ---
def save_log_to_disk(mensaje: str):
    """
    Función wrapper para mantener compatibilidad con archivos antiguos
    que importan 'save_log_to_disk' directamente.
    """
    # Redirigimos la llamada a la nueva instancia de logger
    logger.info(mensaje)
