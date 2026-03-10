# GitHub Issues — SipSignal Auditoría de Código
# Repositorio: mowgliph/sipsignal
# Ejecutar en orden: primero labels, luego issues

---

## PASO 1 — Crear Labels

```bash
# Severidad
gh label create "critical" \
  --repo mowgliph/sipsignal \
  --description "Riesgo inmediato en producción" \
  --color "B60205"

gh label create "high" \
  --repo mowgliph/sipsignal \
  --description "Debe resolverse en el próximo sprint" \
  --color "E36209"

gh label create "medium" \
  --repo mowgliph/sipsignal \
  --description "Mejora importante a planificar" \
  --color "FBCA04"

gh label create "low" \
  --repo mowgliph/sipsignal \
  --description "Nice-to-have o deuda técnica menor" \
  --color "0E8A16"

# Área técnica
gh label create "architecture" \
  --repo mowgliph/sipsignal \
  --description "Diseño y estructura del sistema" \
  --color "1D76DB"

gh label create "data-integrity" \
  --repo mowgliph/sipsignal \
  --description "Consistencia y persistencia de datos" \
  --color "5319E7"

gh label create "bug" \
  --repo mowgliph/sipsignal \
  --description "Comportamiento incorrecto confirmado" \
  --color "D93F0B"

gh label create "refactor" \
  --repo mowgliph/sipsignal \
  --description "Reestructuración sin cambio de comportamiento" \
  --color "C5DEF5"

gh label create "testing" \
  --repo mowgliph/sipsignal \
  --description "Cobertura y calidad de tests" \
  --color "BFD4F2"

gh label create "dependencies" \
  --repo mowgliph/sipsignal \
  --description "Gestión de librerías y versiones" \
  --color "E4E669"

gh label create "security" \
  --repo mowgliph/sipsignal \
  --description "Seguridad y control de acceso" \
  --color "EE0701"

gh label create "performance" \
  --repo mowgliph/sipsignal \
  --description "Rendimiento y uso de recursos" \
  --color "84B6EB"

gh label create "tech-debt" \
  --repo mowgliph/sipsignal \
  --description "Deuda técnica acumulada" \
  --color "CCCCCC"

gh label create "audit" \
  --repo mowgliph/sipsignal \
  --description "Hallazgo de auditoría de código" \
  --color "0075CA"
```

---

## PASO 2 — Crear Issues

> Los issues están ordenados de mayor a menor severidad.
> Ejecutar cada bloque `gh issue create` de forma independiente.

---

### ISSUE 01 — [CRÍTICO] Mock Database activo emite señales duplicadas

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "critical,bug,data-integrity,audit" \
  --title "[CRÍTICO] Mock Database en strategy_engine.py emite señales duplicadas" \
  --body "## 🔴 Descripción del problema

En \`bot/trading/strategy_engine.py\` existe una clase \`Database\` local con un método \`fetch_active_trade()\` que **siempre retorna \`None\`**, sin importar el estado real de la base de datos:

\`\`\`python
class Database:
    \"\"\"Mock database para operaciones de trade.\"\"\"

    @staticmethod
    async def fetch_active_trade() -> dict | None:
        \"\"\"
        Implementación placeholder - debe integrarse con PostgreSQL.
        \"\"\"
        return None  # ← SIEMPRE None
\`\`\`

Esto provoca que el ciclo de análisis en \`run_cycle()\` **nunca detecte un trade abierto**, por lo que puede emitir una nueva señal mientras ya hay una operación activa en \`active_trades\` en PostgreSQL.

## 💥 Impacto

- El usuario puede recibir señales LONG/SHORT simultáneas o superpuestas.
- El sistema de drawdown puede contabilizar trades que no fueron registrados correctamente.
- La lógica \`if active: return None\` no tiene ningún efecto real en producción.

## ✅ Solución propuesta

1. Eliminar la clase \`Database\` mock de \`strategy_engine.py\`.
2. Reemplazar la llamada \`await Database.fetch_active_trade()\` por el repositorio real:

\`\`\`python
# Antes (mock — NO funciona)
active = await Database.fetch_active_trade()

# Después (repositorio real vía puerto del dominio)
active = await trade_repo.get_active()
\`\`\`

3. Asegurarse de que \`run_cycle()\` reciba el \`ActiveTradeRepository\` como dependencia inyectada, igual que hace \`RunSignalCycle\` en \`bot/application/run_signal_cycle.py\`.
4. Añadir un test que verifique que \`run_cycle()\` retorna \`None\` cuando \`trade_repo.get_active()\` devuelve un trade real.

## 📁 Archivos afectados

- \`bot/trading/strategy_engine.py\` (líneas 43–52)
- \`bot/application/run_signal_cycle.py\` (referencia de implementación correcta)

## 🔗 Referencia de auditoría

Hallazgo **§3.3** del informe de auditoría — Severidad CRÍTICA."
```

---

### ISSUE 02 — [CRÍTICO] Doble almacenamiento activo: JSON y PostgreSQL en paralelo

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "critical,data-integrity,architecture,tech-debt,audit" \
  --title "[CRÍTICO] Doble fuente de verdad: JSON legacy y PostgreSQL activos simultáneamente" \
  --body "## 🔴 Descripción del problema

El sistema mantiene **dos mecanismos de persistencia activos en paralelo** para datos de usuario:

| Capa | Archivo | Datos que gestiona |
|------|---------|-------------------|
| JSON (legacy) | \`bot/utils/file_manager.py\` | Usuarios, preferencias, logs, subscripciones, métricas |
| PostgreSQL | \`bot/db/users.py\` + \`bot/infrastructure/database/\` | Usuarios, configuración, señales, trades, drawdown |

Los handlers de Telegram mezclan ambas fuentes en el mismo flujo de negocio. Por ejemplo, un handler puede leer la configuración del usuario desde el JSON pero registrar el trade en PostgreSQL, generando **estados divergentes e inconsistentes**.

## 💥 Impacto

- Un usuario aprobado en PostgreSQL puede tener datos de configuración desactualizados en el JSON.
- El drawdown puede calcularse con capital diferente al configurado realmente.
- Imposible garantizar integridad transaccional entre ambas capas.
- El JSON no es thread-safe: escrituras concurrentes desde múltiples callbacks pueden corromper el archivo.

## ✅ Solución propuesta

1. **Auditar todos los handlers** para identificar qué llamadas van a \`file_manager\` y cuáles a la capa de base de datos.
2. **Crear equivalentes PostgreSQL** para toda la funcionalidad restante en \`file_manager.py\` que aún no tenga contraparte en la BD (métricas de uso, registro de comandos, etc.).
3. **Migrar datos existentes**: ejecutar un script de migración one-shot que vuelque \`users.json\` a la tabla \`users\` y \`user_config\` de PostgreSQL.
4. **Eliminar progresivamente** las llamadas a \`cargar_usuarios()\` / \`guardar_usuarios()\` de los handlers, sustituyéndolas por llamadas al repositorio.
5. Una vez todos los handlers estén migrados, **deprecar y eliminar** \`file_manager.py\` o reducirlo solo a utilidades de archivos no relacionadas con usuarios.

## 📁 Archivos afectados

- \`bot/utils/file_manager.py\` (~25 llamadas externas a \`cargar_usuarios\`/\`guardar_usuarios\`)
- \`bot/handlers/admin.py\`
- \`bot/handlers/trading.py\`
- \`bot/handlers/user_settings.py\`
- \`bot/db/users.py\`
- \`bot/infrastructure/database/user_repositories.py\`

## 🔗 Referencia de auditoría

Hallazgo **§3.2** del informe de auditoría — Severidad CRÍTICA."
```

---

### ISSUE 03 — [CRÍTICO] BinanceDataFetcher duplica BinanceAdapter (~80% código idéntico)

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "critical,refactor,architecture,tech-debt,audit" \
  --title "[CRÍTICO] Duplicación de BinanceDataFetcher y BinanceAdapter — consolidar en un único adaptador" \
  --body "## 🔴 Descripción del problema

Existen dos implementaciones prácticamente idénticas del cliente HTTP de Binance:

| Clase | Archivo | Hereda de |
|-------|---------|-----------|
| \`BinanceDataFetcher\` | \`bot/trading/data_fetcher.py\` | — (clase independiente) |
| \`BinanceAdapter\` | \`bot/infrastructure/binance/binance_adapter.py\` | \`MarketDataPort\` ✅ |

Ambas clases comparten más del **80% del código**: lógica de reintentos con backoff, manejo del código 429 (rate limit), parsing de respuestas OHLCV, exclusión de vela abierta y gestión de sesión \`aiohttp\`.

La diferencia es únicamente que \`BinanceAdapter\` implementa el puerto del dominio (\`MarketDataPort\`), mientras que \`BinanceDataFetcher\` opera fuera de la arquitectura hexagonal.

## 💥 Impacto

- Cualquier corrección de bugs (e.g., manejo de errores de red) debe aplicarse en **dos sitios** o se crea una regresión silenciosa.
- Los módulos en \`bot/trading/\` consumen \`BinanceDataFetcher\` directamente, bypasseando los puertos del dominio y haciendo imposible mockearlos en tests.
- \`asyncio.get_event_loop().time()\` deprecado está duplicado en **ambas** implementaciones (ver Issue #05).

## ✅ Solución propuesta

1. Hacer que \`BinanceDataFetcher\` sea un alias o subclase de \`BinanceAdapter\`, o bien eliminarlo y reemplazar todas sus referencias.
2. Modificar los módulos en \`bot/trading/\` (\`strategy_engine.py\`, \`drawdown_manager.py\`) para recibir el adaptador como dependencia inyectada en lugar de instanciarlo directamente.
3. Verificar que todos los tests que mockean \`BinanceDataFetcher\` se actualicen para usar \`BinanceAdapter\` / \`MarketDataPort\`.

\`\`\`python
# Antes — instanciación directa (acoplado)
from bot.trading.data_fetcher import BinanceDataFetcher
fetcher = BinanceDataFetcher()

# Después — inyección de dependencia (desacoplado)
from bot.domain.ports import MarketDataPort
async def run_cycle(market_data: MarketDataPort, ...):
    df = await market_data.get_ohlcv(\"BTCUSDT\", timeframe, 200)
\`\`\`

## 📁 Archivos afectados

- \`bot/trading/data_fetcher.py\` (candidato a eliminar)
- \`bot/infrastructure/binance/binance_adapter.py\` (mantener y extender)
- \`bot/trading/strategy_engine.py\`

## 🔗 Referencia de auditoría

Hallazgo **§3.5** del informe de auditoría — Severidad CRÍTICA."
```

---

### ISSUE 04 — [ALTO] Naive datetimes sin UTC causan errores de tipo con PostgreSQL

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "high,bug,data-integrity,audit" \
  --title "[ALTO] 20+ naive datetimes sin timezone causan TypeError contra TIMESTAMPTZ de PostgreSQL" \
  --body "## 🟠 Descripción del problema

El proyecto usa \`datetime.now()\` sin argumento de timezone en más de 20 sitios. PostgreSQL almacena todos los timestamps como \`TIMESTAMPTZ\` (con zona horaria), y Python lanza \`TypeError\` al comparar un datetime naive con uno aware:

\`\`\`
TypeError: can't compare offset-naive and offset-aware datetimes
\`\`\`

### Sitios identificados

| Archivo | Instancias | Contexto |
|---------|-----------|----------|
| \`bot/utils/file_manager.py\` | 8 | migrate_user_timestamps, guardar_usuarios, registrar_uso |
| \`bot/utils/telemetry.py\` | 9 | cálculos de períodos de 30 días, estadísticas |
| \`bot/handlers/admin.py\` | 2 | generación de reportes |
| \`bot/handlers/general.py\` | 1 | fecha_actual en respuestas |
| \`bot/infrastructure/database/user_repositories.py\` | 1 | creación de usuario (now = datetime.now()) |

## 💥 Impacto

- Crash en runtime al comparar \`requested_at\` (TIMESTAMPTZ de la BD) con \`datetime.now()\` (naive).
- Cálculos de estadísticas de 30 días incorrectos según la zona horaria del servidor.
- El método \`_is_request_expired()\` en \`AccessManager\` ya usa \`UTC\` correctamente — el resto no.

## ✅ Solución propuesta

Reemplazar **todas** las ocurrencias de \`datetime.now()\` por \`datetime.now(UTC)\`:

\`\`\`python
# Antes — naive (sin timezone)
from datetime import datetime
now = datetime.now()

# Después — aware (con UTC explícito)
from datetime import UTC, datetime
now = datetime.now(UTC)
\`\`\`

Adicionalmente, añadir una regla de linting en \`pyproject.toml\` con \`ruff\` para detectar regresiones:

\`\`\`toml
[tool.ruff.lint]
select = [\"DTZ\"]  # flake8-datetimez: detecta datetime.now() sin tz
\`\`\`

## 📁 Archivos afectados

- \`bot/utils/file_manager.py\`
- \`bot/utils/telemetry.py\`
- \`bot/handlers/admin.py\`
- \`bot/handlers/general.py\`
- \`bot/infrastructure/database/user_repositories.py\`

## 🔗 Referencia de auditoría

Hallazgo **§3.4** del informe de auditoría — Severidad ALTA."
```

---

### ISSUE 05 — [ALTO] asyncio.get_event_loop() deprecado desde Python 3.10

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "high,bug,performance,audit" \
  --title "[ALTO] asyncio.get_event_loop() deprecado — reemplazar por get_running_loop()" \
  --body "## 🟠 Descripción del problema

Se usa \`asyncio.get_event_loop().time()\` en 4 sitios del código para medir latencia de llamadas HTTP. Este método está **deprecado desde Python 3.10** y emite \`DeprecationWarning\` en Python 3.12+. En Python 3.13 (versión requerida por el proyecto) puede lanzar un error si no hay un loop activo en el hilo actual.

### Ocurrencias

\`\`\`
bot/infrastructure/binance/binance_adapter.py  — líneas 39, 44
bot/trading/data_fetcher.py                    — líneas 41, 46
\`\`\`

\`\`\`python
# Código actual — DEPRECADO
start_time = asyncio.get_event_loop().time()
# ...
latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
\`\`\`

## 💥 Impacto

- \`DeprecationWarning\` continuo en los logs que enmascara advertencias reales.
- En entornos con múltiples hilos o loops, puede lanzar \`RuntimeError: no running event loop\`.
- El proyecto requiere Python 3.13 donde este comportamiento es más estricto.

## ✅ Solución propuesta

\`\`\`python
# Antes — deprecado
start_time = asyncio.get_event_loop().time()

# Después — correcto para código async
start_time = asyncio.get_running_loop().time()
\`\`\`

\`get_running_loop()\` es seguro porque estas llamadas ocurren siempre dentro de corutinas async, garantizando que hay un loop activo.

## 📁 Archivos afectados

- \`bot/infrastructure/binance/binance_adapter.py\` (2 líneas)
- \`bot/trading/data_fetcher.py\` (2 líneas) — se eliminará al resolver Issue #03

## 🔗 Referencia de auditoría

Hallazgo **§3.1** del informe de auditoría — Severidad ALTA."
```

---

### ISSUE 06 — [ALTO] admin.py de 980 líneas viola el principio de responsabilidad única

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "high,refactor,tech-debt,audit" \
  --title "[ALTO] Refactorizar admin.py (980 líneas) — dividir en módulos por responsabilidad" \
  --body "## 🟠 Descripción del problema

El archivo \`bot/handlers/admin.py\` tiene **980 líneas** y concentra responsabilidades completamente distintas en un solo módulo:

- Gestión y visualización de logs del sistema
- Dashboard de usuarios (listado, estadísticas, actividad)
- Envío masivo de mensajes (\`/ms\` broadcast)
- Gestión de anuncios (\`/ad\`)
- Reportes de métricas y telemetría
- Utilidades de administración general

Esto viola el **Principio de Responsabilidad Única (SRP)** y hace que el archivo sea difícil de leer, testear y mantener. Cualquier cambio en el broadcast afecta el mismo archivo que gestiona los logs.

## 💥 Impacto

- Imposible escribir tests unitarios focalizados para cada funcionalidad.
- Conflictos de merge frecuentes si varios desarrolladores trabajan en distintas features de admin.
- Alto acoplamiento implícito entre funciones no relacionadas.

## ✅ Solución propuesta

Dividir \`admin.py\` en los siguientes módulos dentro de \`bot/handlers/\`:

| Módulo nuevo | Responsabilidad | Comandos |
|-------------|-----------------|----------|
| \`admin_users.py\` | Dashboard y gestión de usuarios | \`/users\` |
| \`admin_logs.py\` | Visualización y gestión de logs | \`/logs\` |
| \`admin_broadcast.py\` | Mensajes masivos | \`/ms\` |
| \`admin_ads.py\` | Gestión de anuncios | \`/ad\` |
| \`admin_metrics.py\` | Telemetría y reportes | métricas internas |

Pasos de implementación:

1. Crear los nuevos archivos con las funciones extraídas.
2. Actualizar \`bot/main.py\` para importar desde los nuevos módulos.
3. Verificar que todos los \`ConversationHandler\` y \`CallbackQueryHandler\` se registren correctamente.
4. Eliminar \`admin.py\` una vez migrado todo.

## 📁 Archivos afectados

- \`bot/handlers/admin.py\` (refactorizar y eliminar)
- \`bot/main.py\` (actualizar imports)

## 🔗 Referencia de auditoría

Hallazgo **§3.7** del informe de auditoría — Severidad ALTA."
```

---

### ISSUE 07 — [MEDIO] 93 bloques except Exception genéricos silencian errores críticos

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "medium,bug,tech-debt,audit" \
  --title "[MEDIO] 93 bloques except Exception genéricos — especializar captura de errores" \
  --body "## 🟡 Descripción del problema

Se detectaron **93 bloques \`except Exception\`** en todo el codebase. Esta práctica suprime silenciosamente errores que deberían propagarse o al menos registrarse con su tipo específico.

### Casos de mayor riesgo identificados

\`\`\`python
# bot/handlers/admin.py — Error en cálculo de drawdown ignorado
try:
    result = await update_drawdown(user_id, pnl)
except Exception:
    pass  # ← El sistema no pausa aunque debería
\`\`\`

\`\`\`python
# bot/utils/logger.py — Error de logger suprimido
except Exception:
    pass  # ← Ni siquiera se imprime por stdout
\`\`\`

## 💥 Impacto

- **Crítico para trading**: si el cálculo de drawdown falla silenciosamente, el bot no pausa aunque el usuario haya alcanzado su límite de pérdidas.
- Los errores de conexión a la BD se tragan sin reintentar ni alertar al administrador.
- El debugging en producción es extremadamente difícil: los logs no muestran qué falló ni dónde.

## ✅ Solución propuesta

Reemplazar los \`except Exception\` por tipos específicos según el contexto:

\`\`\`python
# Para errores de base de datos
import asyncpg
except asyncpg.PostgresError as e:
    logger.error(f\"DB error en update_drawdown: {e}\")
    raise  # propagar si es crítico

# Para errores de red (Binance, Groq, CMC)
import aiohttp
except aiohttp.ClientError as e:
    logger.warning(f\"Error de red: {e}\")

# Para errores de Telegram
from telegram.error import TelegramError
except TelegramError as e:
    logger.error(f\"Error Telegram: {e}\")
\`\`\`

### Prioridad de revisión (mayor riesgo primero)

1. Bloques en \`drawdown_manager.py\` — afectan la seguridad del capital
2. Bloques en \`handlers/admin.py\` — ocultan errores de operación
3. Bloques en \`utils/logger.py\` — impiden ver otros errores
4. Resto del codebase

## 📁 Archivos afectados

- \`bot/trading/drawdown_manager.py\`
- \`bot/handlers/admin.py\`
- \`bot/utils/logger.py\`
- \`bot/core/api_client.py\`
- (y ~89 sitios más en el codebase)

## 🔗 Referencia de auditoría

Hallazgo **§3.6** del informe de auditoría — Severidad MEDIA."
```

---

### ISSUE 08 — [MEDIO] Tests de integración ausentes — tests/integration/ vacío

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "medium,testing,audit" \
  --title "[MEDIO] Implementar tests de integración — carpeta tests/integration/ vacía" \
  --body "## 🟡 Descripción del problema

Las carpetas \`tests/integration/\` y \`tests/e2e/\` existen en el repositorio pero están **completamente vacías**. Los handlers de Telegram tampoco tienen cobertura de tests unitarios.

### Estado actual de cobertura

| Capa | Cobertura | Estado |
|------|-----------|--------|
| Dominio (Signal, UserConfig, DrawdownState) | Alta | ✅ |
| Casos de uso (RunSignalCycle, HandleDrawdown) | Media-alta | ✅ |
| Adaptadores de infraestructura | Parcial | ⚠️ |
| Handlers de Telegram (13 archivos) | Nula | ❌ |
| Tests de integración con BD real | Nula | ❌ |
| Tests E2E | Nula | ❌ |

## 💥 Impacto

- Los bugs de integración entre la capa de aplicación y PostgreSQL solo se descubren en producción.
- No hay validación de que las migraciones SQL (\`001_initial.sql\`) producen el schema correcto.
- Cambios en handlers pueden romper flujos de conversación sin que ningún test lo detecte.

## ✅ Solución propuesta

### Tests de integración (prioridad alta)

Usar una base de datos PostgreSQL de test con \`pytest-asyncio\` y fixtures:

\`\`\`python
# tests/integration/conftest.py
import pytest
import asyncpg

@pytest.fixture(scope=\"session\")
async def db_pool():
    pool = await asyncpg.create_pool(\"postgresql://test:test@localhost/sipsignal_test\")
    # Aplicar schema
    await pool.execute(open(\"bot/db/migrations/001_initial.sql\").read())
    yield pool
    await pool.close()
\`\`\`

### Tests de handlers (usar python-telegram-bot test utilities)

\`\`\`python
# tests/unit/test_handlers_general.py
from unittest.mock import AsyncMock
from bot.handlers.general import start

async def test_start_command_sends_welcome():
    update = AsyncMock()
    context = AsyncMock()
    await start(update, context)
    update.message.reply_text.assert_called_once()
\`\`\`

### Cobertura mínima objetivo

- \`tests/integration/test_signal_repository.py\` — CRUD de señales contra BD real
- \`tests/integration/test_user_flow.py\` — registro y aprobación de usuario
- \`tests/integration/test_drawdown_flow.py\` — flujo completo de drawdown
- \`tests/unit/test_handlers_general.py\` — comandos básicos (/start, /help)
- \`tests/unit/test_handlers_capital.py\` — flujo /capital y /setup

## 📁 Archivos a crear

- \`tests/integration/conftest.py\`
- \`tests/integration/test_signal_repository.py\`
- \`tests/integration/test_user_flow.py\`
- \`tests/integration/test_drawdown_flow.py\`
- \`tests/unit/test_handlers_general.py\`
- \`tests/unit/test_handlers_capital.py\`

## 🔗 Referencia de auditoría

Hallazgo **§3.7** del informe de auditoría — Severidad MEDIA."
```

---

### ISSUE 09 — [MEDIO] requirements.txt y pyproject.toml con versiones inconsistentes

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "medium,dependencies,tech-debt,audit" \
  --title "[MEDIO] Unificar dependencias — requirements.txt y pyproject.toml tienen versiones contradictorias" \
  --body "## 🟡 Descripción del problema

El proyecto define dependencias en **dos archivos con criterios distintos**, lo que puede causar instalaciones inconsistentes entre entornos:

### Conflictos detectados

| Paquete | pyproject.toml | requirements.txt |
|---------|---------------|-----------------|
| \`pandas\` | \`>=2.0.0\` | \`==3.0.1\` (pinned) |
| \`pytest-asyncio\` | \`>=0.23.0\` | \`==1.3.0\` (versión no existe) |
| \`groq\` | \`>=0.4.0\` | sin versión especificada |
| \`alembic\` | \`>=1.12.0\` | \`>=1.13.0\` (rango diferente) |

Adicionalmente, \`requirements.txt\` incluye dependencias **transitivas** que no deberían estar pinned directamente (e.g., \`aiohappyeyeballs==2.6.1\`, \`frozenlist==1.8.0\`, \`propcache==0.4.1\`).

## 💥 Impacto

- \`pip install -r requirements.txt\` puede instalar una versión de \`pytest-asyncio\` inexistente y fallar el CI.
- Entornos de desarrollo vs. producción pueden tener versiones distintas de \`pandas\` con APIs diferentes.
- Las dependencias transitivas pinned romperán la instalación cuando sus padres actualicen sus rangos.

## ✅ Solución propuesta

1. Designar \`pyproject.toml\` como la **única fuente de verdad** para dependencias directas.
2. Generar \`requirements.txt\` automáticamente con \`pip-compile\` (del paquete \`pip-tools\`):

\`\`\`bash
# Instalar pip-tools
pip install pip-tools

# Generar requirements.txt desde pyproject.toml
pip-compile pyproject.toml --output-file requirements.txt

# Para dependencias de desarrollo
pip-compile pyproject.toml --extra dev --output-file requirements-dev.txt
\`\`\`

3. Añadir al \`Makefile\` o al CI un comando \`make deps\` para regenerar el lockfile.
4. Documentar el flujo en el \`README.md\`.

## 📁 Archivos afectados

- \`requirements.txt\` (regenerar)
- \`pyproject.toml\` (revisar rangos de versión)

## 🔗 Referencia de auditoría

Hallazgo **§3.8** del informe de auditoría — Severidad MEDIA."
```

---

### ISSUE 10 — [MEDIO] Pool de base de datos inicializado de forma lazy con variable global mutable

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "medium,bug,architecture,audit" \
  --title "[MEDIO] Pool de BD inicializado lazy con global mutable — riesgo de condición de carrera" \
  --body "## 🟡 Descripción del problema

El módulo \`bot/core/database.py\` gestiona el pool de conexiones mediante una **variable global mutable** con inicialización lazy:

\`\`\`python
_pool: asyncpg.Pool | None = None

async def execute(query, *args):
    if _pool is None:
        await connect()  # Se inicializa en la primera llamada
    async with _pool.acquire() as conn:
        ...
\`\`\`

En un entorno async con múltiples corutinas arrancando simultáneamente (como el arranque del bot de Telegram), **dos corutinas pueden entrar al \`if _pool is None\`** antes de que la primera termine de inicializar el pool, creando dos pools distintos o provocando una condición de carrera.

## 💥 Impacto

- En el arranque del bot, si varios handlers se ejecutan antes de que el pool esté listo, pueden crearse conexiones duplicadas.
- El pool no se cierra correctamente si \`close()\` no es llamado explícitamente en el shutdown del bot.
- Dificulta el testing: el estado global se filtra entre tests si no se limpia manualmente.

## ✅ Solución propuesta

1. **Inicializar el pool explícitamente** en el arranque del bot, antes de registrar los handlers:

\`\`\`python
# bot/main.py — en la función main() o post_init
async def post_init(application):
    await database.connect()
    logger.info(\"Pool de base de datos inicializado\")

application = ApplicationBuilder().token(...).post_init(post_init).build()
\`\`\`

2. **Cerrar el pool** en el shutdown del bot:

\`\`\`python
async def post_shutdown(application):
    await database.close()
    logger.info(\"Pool de base de datos cerrado\")
\`\`\`

3. Para tests, usar un fixture que inicialice y cierre el pool por sesión.

## 📁 Archivos afectados

- \`bot/core/database.py\`
- \`bot/main.py\`

## 🔗 Referencia de auditoría

Hallazgo **§3.8** del informe de auditoría — Severidad MEDIA."
```

---

### ISSUE 11 — [BAJO] Sistema de logging dual: loguru vs logger propio inconsistentes

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "low,refactor,tech-debt,audit" \
  --title "[BAJO] Logging dual inconsistente — unificar loguru y utils/logger.py" \
  --body "## 🟢 Descripción del problema

El proyecto usa **dos sistemas de logging en paralelo**:

1. **loguru** — importado directamente en módulos de infraestructura y aplicación:
   \`\`\`python
   from loguru import logger  # usado en binance_adapter.py, run_signal_cycle.py, etc.
   \`\`\`

2. **Logger propio** — clase personalizada en \`bot/utils/logger.py\` con métodos específicos del bot:
   \`\`\`python
   from bot.utils.logger import logger  # usado en handlers y core
   \`\`\`

Esto genera inconsistencia en el formato de los logs, duplicación de registros en algunos módulos, y confusión sobre qué logger usar en módulos nuevos.

## 💥 Impacto

- Los logs de infraestructura (Binance, Groq) tienen formato diferente al del resto del bot.
- Si el logger propio añade contexto adicional (chat_id, user_id), los módulos que usan loguru directamente no lo incluyen.
- Dificulta la correlación de logs en producción.

## ✅ Solución propuesta

**Opción A (recomendada):** Hacer que \`bot/utils/logger.py\` exporte el logger de \`loguru\` configurado, y usar ese logger en todo el proyecto:

\`\`\`python
# bot/utils/logger.py
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, format=\"{time} | {level} | {name} | {message}\", level=\"INFO\")

__all__ = [\"logger\"]
\`\`\`

\`\`\`python
# En todos los módulos — import unificado
from bot.utils.logger import logger
\`\`\`

**Opción B:** Eliminar loguru como dependencia directa y extender el logger propio con los métodos que falten.

## 📁 Archivos afectados

- \`bot/utils/logger.py\`
- \`bot/infrastructure/binance/binance_adapter.py\`
- \`bot/application/run_signal_cycle.py\`
- \`bot/application/handle_drawdown.py\`
- (y demás módulos que importan loguru directamente)

## 🔗 Referencia de auditoría

Hallazgo **§3.8** del informe de auditoría — Severidad BAJA."
```

---

### ISSUE 12 — [BAJO] i18n incompleto — sistema multiidioma parcialmente implementado

```bash
gh issue create \
  --repo mowgliph/sipsignal \
  --assignee mowgliph \
  --label "low,tech-debt,audit" \
  --title "[BAJO] Sistema i18n incompleto — internacionalización solo parcialmente implementada" \
  --body "## 🟢 Descripción del problema

El bot declara soporte para **Español e Inglés** en el README y tiene un comando \`/lang\` para cambiar el idioma. Sin embargo, la implementación es incompleta:

- \`bot/handlers/trading.py\` contiene un comentario explícito:
  \`\`\`python
  # from core.i18n import _  # TODO: Implementar i18n en el futuro
  \`\`\`
- Los textos en \`AccessManager\`, mensajes de señales, respuestas de handlers y notificaciones de admin están **hardcodeados en español**.
- El campo \`language\` existe en la tabla \`users\` pero no se usa para traducir los mensajes de respuesta.

## 💥 Impacto

- Usuarios con idioma configurado en inglés reciben respuestas en español.
- La promesa del README de soporte multiidioma no está cumplida.
- Añadir un tercer idioma en el futuro requeriría buscar strings por todo el código.

## ✅ Solución propuesta

1. Definir un sistema de traducción simple basado en diccionarios por módulo, o usar \`gettext\`/\`Babel\` para proyectos más grandes.
2. Crear archivos de traducción en \`bot/locales/es.py\` y \`bot/locales/en.py\`.
3. Implementar una función \`_(key, lang)\` que resuelva el string correcto según el idioma del usuario.
4. Migrar progresivamente los textos hardcodeados, empezando por los mensajes más frecuentes (\`/start\`, \`/help\`, señales de trading).

\`\`\`python
# bot/locales/es.py
MESSAGES = {
    \"welcome\": \"¡Bienvenido a SipSignal! 🚀\",
    \"access_pending\": \"⏳ Su solicitud está siendo procesada.\",
}

# bot/locales/en.py
MESSAGES = {
    \"welcome\": \"Welcome to SipSignal! 🚀\",
    \"access_pending\": \"⏳ Your request is being processed.\",
}

# bot/utils/i18n.py
def _(key: str, lang: str = \"es\") -> str:
    from bot.locales import es, en
    catalog = en.MESSAGES if lang == \"en\" else es.MESSAGES
    return catalog.get(key, es.MESSAGES.get(key, key))
\`\`\`

## 📁 Archivos a crear / modificar

- \`bot/locales/es.py\` (nuevo)
- \`bot/locales/en.py\` (nuevo)
- \`bot/utils/i18n.py\` (nuevo)
- \`bot/core/access_manager.py\` (usar \`_()\`)
- \`bot/handlers/\` — todos los handlers con textos hardcodeados

## 🔗 Referencia de auditoría

Hallazgo **§3.8** del informe de auditoría — Severidad BAJA."
```

---

## Resumen de ejecución

| # | Título corto | Severidad | Labels |
|---|-------------|-----------|--------|
| 01 | Mock Database emite señales duplicadas | 🔴 CRÍTICO | critical, bug, data-integrity |
| 02 | Doble almacenamiento JSON + PostgreSQL | 🔴 CRÍTICO | critical, data-integrity, architecture |
| 03 | BinanceDataFetcher duplicado | 🔴 CRÍTICO | critical, refactor, architecture |
| 04 | Naive datetimes sin UTC | 🟠 ALTO | high, bug, data-integrity |
| 05 | asyncio.get_event_loop() deprecado | 🟠 ALTO | high, bug, performance |
| 06 | admin.py de 980 líneas | 🟠 ALTO | high, refactor, tech-debt |
| 07 | 93 except Exception genéricos | 🟡 MEDIO | medium, bug, tech-debt |
| 08 | tests/integration/ vacío | 🟡 MEDIO | medium, testing |
| 09 | requirements.txt vs pyproject.toml | 🟡 MEDIO | medium, dependencies |
| 10 | Pool BD lazy con global mutable | 🟡 MEDIO | medium, bug, architecture |
| 11 | Logging dual inconsistente | 🟢 BAJO | low, refactor, tech-debt |
| 12 | i18n incompleto | 🟢 BAJO | low, tech-debt |

> **Nota:** Ejecutar los issues en el orden indicado ya que algunos (e.g. #03, #05) tienen dependencia lógica entre sí.
