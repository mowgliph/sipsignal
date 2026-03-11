# SipSignal Trading Bot

🤖 **Bot de Telegram para Análisis Técnico y Señales de Trading**

Sistema inteligente de señales BTC con análisis técnico automatizado 24/7 y monitoreo de TP/SL en tiempo real.

---

## Características

- 📊 **Análisis Técnico Automatizado** - RSI, MACD, Bollinger Bands, EMA, Supertrend
- 🎯 **Señales de Trading** - Oportunidades de entrada con ratio riesgo:beneficio
- 📡 **Monitoreo TP/SL** - WebSocket para seguimiento de take profit y stop loss en tiempo real
- 📈 **Gráficos** - Visualización de datos de mercado con análisis técnico
- 🧠 **IA Integrada** - Contexto de mercado con Groq AI (Llama 3)
- 🌐 **Multi-idioma** - Soporte para Español e Inglés
- 💰 **Gestión de Capital** - Control de drawdown y seguimiento de rendimiento
- 🏗️ **Arquitectura Hexagonal** - Código modular y mantenible

---

## Comandos Disponibles

### Comandos Básicos
| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar el bot y registrarse |
| `/help` | Mostrar menú de ayuda |
| `/status` | Ver estado del bot y último análisis |
| `/myid` | Obtener tu ID de Telegram |
| `/lang` | Cambiar idioma (Español/Inglés) |

### Comandos de Trading y Señales
| Comando | Descripción |
|---------|-------------|
| `/signal` | Análisis técnico instantáneo de BTC |
| `/chart [tf]` | Ver gráfico (5m, 15m, 1h, 4h, 1D) |
| `/ta <símbolo>` | Análisis técnico completo |
| `/mk` | Ver datos de mercado |
| `/p <símbolo>` | Precio de una criptomoneda específica |
| `/journal` | Historial de señales emitidas |
| `/capital` | Gestión de capital y control de drawdown |
| `/risk [entrada] [sl] [tp]` | Calcular ratio riesgo:beneficio |

### Comandos de Administrador
| Comando | Descripción |
|---------|-------------|
| `/users` | Dashboard de administración |
| `/logs` | Ver logs del sistema |
| `/ms` | Mensaje masivo a usuarios |
| `/ad` | Gestión de anuncios |

---

## Instalación

### Requisitos
- Python 3.13+
- PostgreSQL
- pip
- Git

### Setup

1. **Clonar el repositorio:**
```bash
git clone https://github.com/mowgliph/sipsignal.git
cd sipsignal
```

2. **Crear entorno virtual:**
```bash
python3.13 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -e ".[dev]"
```

4. **Configurar variables de entorno:**
```bash
cp env.example .env
# Editar .env con tus credenciales
```

5. **Ejecutar migraciones de base de datos:**
```bash
alembic upgrade head
```

6. **Ejecutar el bot:**
```bash
python bot/main.py
```

---

## Gestión de Dependencias

Este proyecto usa `pyproject.toml` como fuente de verdad para las dependencias. El archivo `requirements.txt` se genera automáticamente con [pip-tools](https://github.com/jazzband/pip-tools).

### Instalación

```bash
# Desde pyproject.toml (desarrollo)
pip install -e ".[dev]"

# Desde lockfile (producción)
pip sync requirements.txt
```

### Actualizar dependencias

```bash
# Añadir nueva dependencia a pyproject.toml
# Luego regenerar lockfile
pip-compile pyproject.toml --output-file=requirements.txt

# Actualizar todas las dependencias
pip-compile pyproject.toml --output-file=requirements.txt --upgrade
```

### Verificar dependencias instaladas

```bash
pip list
pip freeze
```

---

## Estructura del Proyecto

```
sipsignal/
├── bot/                        # Código principal del bot
│   ├── main.py                 # Punto de entrada
│   ├── container.py            # Inyección de dependencias
│   ├── scheduler.py            # Programador de señales
│   ├── application/            # Casos de uso
│   │   ├── run_signal_cycle.py
│   │   ├── get_signal_analysis.py
│   │   ├── handle_drawdown.py
│   │   └── manage_journal.py
│   ├── domain/                 # Entidades de negocio
│   │   ├── ports/              # Interfaces (repositories, services)
│   │   ├── signal.py
│   │   ├── user_config.py
│   │   └── drawdown_state.py
│   ├── infrastructure/         # Adaptadores externos
│   │   ├── binance/            # Binance API
│   │   ├── groq/               # Groq AI
│   │   ├── telegram/           # Telegram Bot
│   │   └── database/           # Repositorios PostgreSQL
│   ├── handlers/               # Manejadores de comandos
│   │   ├── general.py
│   │   ├── admin.py
│   │   ├── trading.py
│   │   ├── signal_handler.py
│   │   └── capital_handler.py
│   ├── trading/                # Lógica de trading
│   │   ├── technical_analysis.py
│   │   ├── strategy_engine.py
│   │   ├── price_monitor.py
│   │   └── drawdown_manager.py
│   ├── ai/                     # Integración con IA
│   ├── core/                   # Configuración y utilidades
│   ├── db/                     # Modelos y migraciones
│   └── utils/                  # Utilidades generales
├── tests/                      # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                       # Documentación
├── scripts/                    # Scripts de utilidad
├── pyproject.toml              # Configuración del proyecto
├── requirements.txt            # Dependencias
├── alembic.ini                 # Migraciones de BD
└── env.example                 # Variables de entorno
```

---

## Arquitectura

El proyecto sigue una **Arquitectura Hexagonal (Clean Architecture)**:

- **Domain Layer** (`bot/domain/`): Entidades de negocio y puertos (interfaces)
- **Application Layer** (`bot/application/`): Casos de uso que orquestan la lógica
- **Infrastructure Layer** (`bot/infrastructure/`): Implementaciones concretas de puertos
- **Handlers Layer** (`bot/handlers/`): Manejadores de comandos de Telegram
- **Trading Layer** (`bot/trading/`): Lógica específica de trading

### Inyección de Dependencias

El contenedor DI está centralizado en `bot/container.py`, facilitando el testing y la mantenibilidad.

---

## Testing

Ejecutar todas las pruebas:
```bash
source venv/bin/activate
pytest tests/ -v
```

Ejecutar tests específicos:
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

---

## Pre-commit Hooks

SipSignal utiliza pre-commit hooks para asegurar calidad de código antes de cada commit.

### Instalación

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Instalar hooks
pre-commit install
```

### Hooks configurados

| Hook | Descripción |
|------|-------------|
| ruff | Lint con auto-fix |
| ruff-format | Formato de código |
| trailing-whitespace | Elimina espacios extra |
| end-of-file-fixer | Newline al final |
| check-yaml | Valida YAML |
| check-added-large-files | Previene archivos >1MB |
| check-merge-conflict | Detecta conflictos |
| validate-tests | Valida tests asociados (warning) |

Ver [docs/pre-commit-hooks.md](docs/pre-commit-hooks.md) para más detalles.

---

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | ✅ |
| `ADMIN_CHAT_IDS` | IDs de administradores (comma-separated) | ✅ |
| `DATABASE_URL` | Connection string de PostgreSQL | ✅ |
| `GROQ_API_KEY` | API Key para análisis con IA | ❌ |

---

## Gestión del Bot

El proyecto incluye un script de gestión `bot/botctl.sh`:

```bash
./bot/botctl.sh start    # Iniciar el bot
./bot/botctl.sh stop     # Detener el bot
./bot/botctl.sh status   # Ver estado
./bot/botctl.sh logs     # Ver logs en tiempo real
./bot/botctl.sh health   # Chequeo completo del sistema
```

---

## Migraciones de Base de Datos

```bash
# Generar nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head
```

---

## Política de Uso

Al usar este bot, aceptas los términos descritos en [docs/POLITICA_DE_USO.md](docs/POLITICA_DE_USO.md).

---

## Soporte

Para soporte o consultas, contacta a los administradores del bot.

---

## 📝 Registro de Cambios

- [CHANGELOG.md](CHANGELOG.md) - Historial completo de cambios

---

## 📊 Métricas del Proyecto

- **⭐ Estrellas en GitHub:** [![GitHub stars](https://img.shields.io/github/stars/mowgliph/sipsignal)](https://github.com/mowgliph/sipsignal)
- **🍴 Forks:** [![GitHub forks](https://img.shields.io/github/forks/mowgliph/sipsignal)](https://github.com/mowgliph/sipsignal)
- **📦 Versión:** ![GitHub release (by tag)](https://img.shields.io/github/v/release/mowgliph/sipsignal?label=version&color=green)
- **🐍 Python:** [![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
- **✅ Tests:** ![Tests](https://img.shields.io/badge/tests-67%2F67-green)
- **📄 Licencia:** [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Estado del Proyecto

![GitHub release (by tag)](https://img.shields.io/github/v/release/mowgliph/sipsignal?label=Versión&color=green)
**Última actualización:** Marzo 2026
**Estado:** ✅ En Producción
**Mantenimiento:** Activo

---

**© 2026 SipSignal Trading Bot. Todos los derechos reservados.**
**Desarrollado con ❤️ por [mowgliph](https://github.com/mowgliph)**

*Este proyecto es de código abierto y está disponible bajo la Licencia MIT.*
