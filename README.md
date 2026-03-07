# SipSignal Trading Bot

🤖 **Bot de Telegram para Análisis Técnico y Señales de Trading**

Sistema inteligente de señales BTC con análisis técnico automatizado 24/7 y monitoreo de TP/SL en tiempo real.

---

## Características

- 📊 **Análisis Técnico Automatizado** - RSI, MACD, Bollinger Bands, EMA y más
- 🎯 **Señales de Trading** - Oportunidades de entrada con ratio riesgo:beneficio
- 📡 **Monitoreo TP/SL** - WebSocket para seguimiento de take profit y stop loss en tiempo real
- 📈 **Gráficos** - Visualización de datos de mercado con análisis técnico
- 🧠 **IA Integrada** - Contexto de mercado con Groq AI
- 🌐 **Multi-idioma** - Soporte para Español e Inglés
- 💰 **Gestión de Capital** - Control de drawdown y seguimiento de rendimiento

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
| `/ver` | Ver precios de tus monedas configuradas |
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
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp env.example .env
# Editar .env con tus credenciales
```

5. **Ejecutar el bot:**
```bash
python sipsignal.py
```

---

## Estructura del Proyecto

```
sipsignal/
├── sipsignal.py          # Punto de entrada principal
├── requirements.txt      # Dependencias
├── env.example           # Variables de entorno de ejemplo
├── venv/                 # Entorno virtual (ignorado en git)
├── core/                 # Lógica principal
│   ├── config.py         # Configuración
│   ├── loops.py          # Utilidades de logs
│   ├── api_client.py     # Cliente API (CoinMarketCap, etc.)
│   ├── database.py       # Base de datos PostgreSQL
│   ├── scheduler.py      # Programador de señales
│   └── btc_advanced_analysis.py  # Análisis avanzado de BTC
├── handlers/             # Manejadores de comandos
│   ├── general.py        # Comandos básicos (/start, /help, etc.)
│   ├── admin.py          # Comandos de admin
│   ├── trading.py        # Comandos de trading (/p, /mk, /ta)
│   ├── signal_handler.py # Manejador de señales
│   ├── chart_handler.py  # Generación de gráficos
│   ├── capital_handler.py# Gestión de capital y drawdown
│   ├── journal_handler.py# Historial de señales
│   └── user_settings.py  # Configuración de usuario (/lang)
├── trading/              # Módulos de trading
│   ├── signal_builder.py # Constructor de mensajes de señales
│   ├── strategy_engine.py# Motor de estrategias
│   ├── price_monitor.py  # Monitor WebSocket TP/SL
│   ├── drawdown_manager.py# Control de drawdown
│   └── technical_analysis.py # Análisis técnico
├── ai/                   # Integración con IA (Groq)
├── utils/                # Utilidades
│   ├── logger.py         # Logging
│   ├── file_manager.py   # Gestión de archivos JSON
│   └── ads_manager.py    # Gestión de anuncios
├── scheduler.py          # Programador de señales autónomas
├── db/                   # Migraciones y modelos de BD
├── tests/                # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/                 # Documentación
```

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

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | ✅ |
| `ADMIN_CHAT_IDS` | IDs de administradores separados por coma | ✅ |
| `GROQ_API_KEY` | API Key para análisis con IA | ❌ |

---

## Política de Uso

Al usar este bot, aceptas los términos descritos en [POLITICA_DE_USO.md](docs/POLITICA_DE_USO.md).

---

##Soporte

Para soporte o consultas, contacta a los administradores del bot.

---

## 📝 Registro de Cambios

- [CHANGELOG.md](CHANGELOG.md) - Historial completo de cambios

---

## 📊 Métricas del Proyecto

- **⭐ Estrellas en GitHub:** [![GitHub stars](https://img.shields.io/github/stars/mowgliph/sipsignal)](https://github.com/mowgliph/sipsignal)
- **🍴 Forks:** [![GitHub forks](https://img.shields.io/github/forks/mowgliph/sipsignal)](https://github.com/mowgliph/sipsignal)
- **📦 Versión:** ![Version](https://img.shields.io/badge/version-1.0.0-green)
- **🐍 Python:** [![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
- **✅ Tests:** ![Tests](https://img.shields.io/badge/tests-67%2F67-green)
- **📄 Licencia:** [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Estado del Proyecto

**Versión:** 1.0.0 (Production Release)  
**Última actualización:** Marzo 2026  
**Estado:** ✅ En Producción  
**Mantenimiento:** Activo

---

**© 2026 SipSignal Trading Bot. Todos los derechos reservados.**  
**Desarrollado con ❤️ por [mowgliph](https://github.com/mowgliph)**

*Este proyecto es de código abierto y está disponible bajo la Licencia MIT.*
