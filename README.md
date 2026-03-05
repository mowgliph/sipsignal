# SipSignal Trading Bot

🤖 **Bot de Telegram para Análisis Técnico y Alertas de Criptomonedas**

Sistema inteligente de señales BTC con análisis técnico automatizado 24/7.

---

## Características

- 📊 **Análisis Técnico Automatizado** - Indicadores y señales en tiempo real
- 🔔 **Alertas Inteligentes** - Notificaciones de precios y cruces
- 🦁 **Monitoreo BTC** - Seguimiento continuo de Bitcoin
- 📈 **Gráficos** - Visualización de datos de mercado
- 🌐 **Multi-idioma** - Soporte para Español e Inglés
- 💎 **Sistema VIP** - Suscripciones premium con beneficios exclusivos

---

## Comandos Disponibles

### Comandos Básicos
| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar el bot y registrarse |
| `/help` | Mostrar menú de ayuda |
| `/status` | Ver estado del bot |
| `/myid` | Obtener tu ID de Telegram |

### Comandos de Trading
| Comando | Descripción |
|---------|-------------|
| `/ver` | Ver precios de tus monedas configuradas |
| `/mk` | Ver datos de mercado |
| `/p <símbolo>` | Precio de una criptomoneda específica |
| `/graf <símbolo>` | Generar gráfico de análisis técnico |
| `/ta <símbolo>` | Análisis técnico completo |

### Comandos de Alertas
| Comando | Descripción |
|---------|-------------|
| `/monedas BTC,ETH` | Configurar lista de monedas a monitorear |
| `/mismonedas` | Ver tus monedas configuradas |
| `/alerta <moneda> <condición>` | Crear alerta de precio |
| `/misalertas` | Ver tus alertas activas |
| `/parar` | Detener alertas temporales |
| `/temp <horas>` | Cambiar frecuencia de alertas |

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
├── .env                  # Variables de entorno (no incluir en git)
├── venv/                 # Entorno virtual (ignorado en git)
├── core/                 # Lógica principal
│   ├── config.py         # Configuración
│   ├── loops.py          # Bucles de fondo
│   └── ...
├── handlers/             # Manejadores de comandos
│   ├── general.py        # Comandos básicos
│   ├── admin.py          # Comandos de admin
│   └── ...
├── utils/                # Utilidades
│   ├── logger.py         # Logging
│   └── file_manager.py   # Gestión de archivos
├── trading/              # Módulos de trading
├── ai/                   # Integración con IA
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

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

---

## Política de Uso

Al usar este bot, aceptas los términos descritos en [POLITICA_DE_USO.md](docs/POLITICA_DE_USO.md).

---

## Soporte

Para soporte o consultas, contacta a los administradores del bot.

---

**Versión:** 1.0-dev  
**Última actualización:** Marzo 2026
