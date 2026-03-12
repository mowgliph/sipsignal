# core/config.py

import os
import platform
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

# --- Cargar Variables de Entorno ---
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configuración centralizada del sistema con validación."""

    # --- Credenciales y IDs ---
    token_telegram: str
    admin_chat_ids: list[int]

    # --- Claves de API ---
    binance_api_key: str = ""
    binance_api_secret: str = ""
    groq_api_key: str = ""
    groq_endpoint: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama3-70b-8192"
    screenshot_api_key: str = ""
    cmc_api_key_alerta: str = ""
    cmc_api_key_control: str = ""

    # --- Configuración de Base de Datos ---
    database_url: str = ""

    # --- Configuración de la Aplicación ---
    log_level: str = "INFO"
    environment: str = "production"

    @classmethod
    def from_env(cls) -> "Settings":
        """Carga configuración desde variables de entorno con validación."""

        # Variables obligatorias
        token_telegram = os.environ.get("TOKEN_TELEGRAM", "").strip()
        admin_chat_ids_raw = os.environ.get("ADMIN_CHAT_IDS", "").strip()
        database_url = os.environ.get("DATABASE_URL", "").strip()

        # Validación de obligatorias
        missing = []
        if not token_telegram:
            missing.append("TOKEN_TELEGRAM")
        if not admin_chat_ids_raw:
            missing.append("ADMIN_CHAT_IDS")
        if not database_url:
            missing.append("DATABASE_URL")

        if missing:
            raise ValueError(
                f"Variables de entorno obligatorias faltantes: {', '.join(missing)}. "
                f"Por favor, configura el archivo .env basándote en env.example"
            )

        # Parsear ADMIN_CHAT_IDS a list[int]
        try:
            admin_chat_ids = [
                int(id_str.strip()) for id_str in admin_chat_ids_raw.split(",") if id_str.strip()
            ]
        except ValueError as e:
            raise ValueError(
                f"ADMIN_CHAT_IDS debe ser una lista de números separados por coma. Error: {e}"
            ) from e

        if not admin_chat_ids:
            raise ValueError(
                "ADMIN_CHAT_IDS no puede estar vacío. Proporciona al menos un ID de administrador."
            )

        return cls(
            token_telegram=token_telegram,
            admin_chat_ids=admin_chat_ids,
            binance_api_key=os.environ.get("BINANCE_API_KEY", "").strip(),
            binance_api_secret=os.environ.get("BINANCE_API_SECRET", "").strip(),
            groq_api_key=os.environ.get("GROQ_API_KEY", "").strip(),
            groq_endpoint=os.environ.get(
                "GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions"
            ).strip(),
            groq_model=os.environ.get("GROQ_MODEL", "llama3-70b-8192").strip(),
            screenshot_api_key=os.environ.get("SCREENSHOT_API_KEY", "").strip(),
            cmc_api_key_alerta=os.environ.get("CMC_API_KEY_ALERTA", "").strip(),
            cmc_api_key_control=os.environ.get("CMC_API_KEY_CONTROL", "").strip(),
            database_url=database_url,
            log_level=os.environ.get("LOG_LEVEL", "INFO").strip().upper(),
            environment=os.environ.get("ENVIRONMENT", "production").strip().lower(),
        )


# --- Compatibilidad hacia atrás (exports) ---

# --- Instancia global de configuración ---
try:
    settings = Settings.from_env()
except ValueError as e:
    print(f"[ERROR] {e}", file=sys.stderr)
    sys.exit(1)

TOKEN_TELEGRAM = settings.token_telegram
ADMIN_CHAT_IDS = settings.admin_chat_ids
GROQ_API_KEY = settings.groq_api_key
GROQ_ENDPOINT = settings.groq_endpoint
GROQ_MODEL = settings.groq_model
SCREENSHOT_API_KEY = settings.screenshot_api_key
BINANCE_API_KEY = settings.binance_api_key
BINANCE_API_SECRET = settings.binance_api_secret
CMC_API_KEY_ALERTA = settings.cmc_api_key_alerta
CMC_API_KEY_CONTROL = settings.cmc_api_key_control
DATABASE_URL = settings.database_url
LOG_LEVEL = settings.log_level
ENVIRONMENT = settings.environment
PYTHON_VERSION = platform.python_version()

# --- Rutas del proyecto ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- Rutas de archivos de datos ---
# USUARIOS_PATH eliminado: migrado a PostgreSQL (ver scripts/migrate_json_to_postgres.py)
LAST_PRICES_PATH = os.path.join(DATA_DIR, "last_prices.json")
TEMPLATE_PATH = os.path.join(DATA_DIR, "img.jpg")
ADS_PATH = os.path.join(DATA_DIR, "ads.json")
YEAR_QUOTES_PATH = os.path.join(DATA_DIR, "year_quotes.json")
YEAR_SUBS_PATH = os.path.join(DATA_DIR, "year_subs.json")
EVENTS_LOG_PATH = os.path.join(DATA_DIR, "events_log.json")

# --- Configuración del sistema ---
PID = os.getpid()
STATE = "RUNNING"

# --- Versión ---
# Leer versión desde pyproject.toml
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]

try:
    pyproject_path = os.path.join(os.path.dirname(BASE_DIR), "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
        VERSION = pyproject_data.get("project", {}).get("version", "1.0.0-dev")
except Exception:
    VERSION = "1.0.0-dev"
