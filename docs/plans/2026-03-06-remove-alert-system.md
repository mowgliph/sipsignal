# Eliminación del Sistema de Alertas — Plan de Implementación

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminar definitivamente todo el sistema de alertas del proyecto SipSignal, conservando únicamente el sistema de trading (señales, TP/SL, análisis técnico manual).

**Architecture:** Eliminación limpia de 7 archivos completos + modificación profunda de 7 archivos compartidos + eliminación de 9 archivos de ejemplo de datos. Se mantiene intacto el sistema de señales de trading, monitoreo TP/SL por WebSocket, análisis técnico manual, y scheduler de señales autónomas.

**Tech Stack:** Python 3, python-telegram-bot, asyncio, PostgreSQL

---

## 🔴 QUÉ SE ELIMINA (Sistema de Alertas)

### 1. Sistema de Alertas HBD (Hive Backed Dollar)
- Loop automático que monitorea precio de HBD y envía alertas al cruzar umbrales
- Comandos: `/hbdalerts` (gestión), botón toggle activar/desactivar
- Archivos de datos: `hbd_price_history.json`, `hbd_thresholds.json`

### 2. Sistema de Alertas de Precio Personalizadas (/alerta)
- Alertas de cruce de precio definidas por el usuario
- Comandos: `/alerta`, `/misalertas`
- Callbacks: `borrar_alerta_callback`, `borrar_todas_alertas_callback`
- Archivo de datos: `price_alerts.json`, `custom_alert_history.json`

### 3. Sistema de Alertas Periódicas de Monedas
- Loop automático que envía precios cada X horas según configuración del usuario
- Comandos: `/temp` (frecuencia), `/parar` (detener), `/monedas` (configurar lista), `/mismonedas` (ver lista)
- JobQueue de telegram para programar envíos periódicos
- Archivo de datos: `last_prices.json`

### 4. Sistema VALERTS (Monitor de Volatilidad Multi-Moneda)
- Loop automático que monitorea soportes/resistencias de múltiples monedas
- Envía alertas al cruzar niveles S1-S3, R1-R3, Pivot, Golden Pocket
- Comandos: `/valerts`, suscripciones por timeframe
- Archivos de datos: `valerts_subs.json`, `valerts_state.json`

### 5. Sistema de Alertas BTC (Monitor BTC PRO)
- Loop automático que monitorea niveles técnicos de BTC en múltiples timeframes
- Envía alertas al cruzar niveles de soporte/resistencia
- Comandos: `/btcalerts`, suscripciones multi-timeframe
- Archivos de datos: `btc_subs.json`, `btc_alert_state.json`

---

## 🟢 QUÉ SE CONSERVA (Sistema de Trading)

| Componente | Archivo(s) | Razón |
|---|---|---|
| Señales de Trading | `handlers/signal_handler.py`, `trading/signal_builder.py`, `trading/strategy_engine.py` | Sistema de señales con entry/TP/SL |
| Respuestas de Señales | `handlers/signal_response_handler.py` | Manejo de taken/skipped/detail |
| Monitor TP/SL WebSocket | `trading/price_monitor.py` | Notificaciones de TP/SL de trades activos |
| Scheduler de Señales | `scheduler.py` | Análisis autónomo de señales |
| Análisis Técnico Manual | `handlers/ta.py`, `core/btc_advanced_analysis.py` | Comando `/ta` (bajo demanda) |
| Gráficos y Precios | `handlers/trading.py` (`/graf`, `/p`, `/mk`), `handlers/chart_handler.py` | Herramientas manuales de trading |
| Drawdown y Capital | `trading/drawdown_manager.py`, `handlers/capital_handler.py` | Gestión de riesgo |
| Journal | `handlers/journal_handler.py` | Historial de señales |
| Setup/Onboarding | `handlers/setup_handler.py` | Configuración inicial |
| Consulta de Precios | `/ver` en `handlers/general.py` | Consulta manual (no automática) |
| IA (Groq) | `ai/groq_client.py`, `core/ai_logic.py` | Análisis con IA |
| Data Fetcher | `trading/data_fetcher.py` | Obtención de datos |
| Chart Capture | `trading/chart_capture.py` | Captura de gráficos |
| Base de Datos | `core/database.py`, `db/` | Persistencia |
| Admin | `handlers/admin.py` | Gestión administrativa |
| Idioma | `handlers/user_settings.py` (solo `/lang`) | Selección de idioma |
| Utilidades | `utils/ads_manager.py`, `utils/tv_helper.py`, `utils/logger.py`, `utils/telemetry.py`, `utils/image_generator.py` | Soporte general |

---

## 📋 TAREAS DE IMPLEMENTACIÓN

### Task 1: Eliminar archivos completos (7 archivos)

**Archivos a ELIMINAR:**
- `core/valerts_loop.py`
- `core/btc_loop.py`
- `handlers/alerts.py`
- `handlers/btc_handlers.py`
- `handlers/valerts_handlers.py`
- `utils/valerts_manager.py`
- `utils/btc_manager.py`

**Step 1: Eliminar archivos**
```bash
rm core/valerts_loop.py
rm core/btc_loop.py
rm handlers/alerts.py
rm handlers/btc_handlers.py
rm handlers/valerts_handlers.py
rm utils/valerts_manager.py
rm utils/btc_manager.py
```

**Step 2: Commit**
```bash
git add -A
git commit -m "refactor: remove alert system files (valerts, btc, hbd, custom alerts)"
```

---

### Task 2: Eliminar archivos de ejemplo de datos (9+ archivos)

**Archivos a ELIMINAR de `data-example/`:**
- `btc_alert_state.json.example`
- `btc_subs.json.example`
- `custom_alert_history.json.example`
- `eltoque_history.json.example`
- `hbd_price_history.json.example`
- `hbd_thresholds.json.example`
- `price_alerts.json.example`
- `weather_last_alerts.json.example`
- `weather_subs.json.example`

**Step 1: Eliminar archivos**
```bash
rm data-example/btc_alert_state.json.example
rm data-example/btc_subs.json.example
rm data-example/custom_alert_history.json.example
rm data-example/eltoque_history.json.example
rm data-example/hbd_price_history.json.example
rm data-example/hbd_thresholds.json.example
rm data-example/price_alerts.json.example
rm data-example/weather_last_alerts.json.example
rm data-example/weather_subs.json.example
```

**Step 2: Commit**
```bash
git add -A
git commit -m "refactor: remove alert data example files"
```

---

### Task 3: Limpiar `sipsignal.py` (punto de entrada)

**Archivo:** `sipsignal.py`

**Imports a ELIMINAR:**
```python
from core.btc_loop import btc_monitor_loop, set_btc_sender
from handlers.btc_handlers import btc_handlers_list
from core.loops import (
    alerta_loop,
    check_custom_price_alerts,
    programar_alerta_usuario,
    set_enviar_mensaje_telegram_async,
)
# Solo conservar: get_logs_data de core.loops
from handlers.user_settings import (
    mismonedas, parar, cmd_temp, set_monedas_command,
    set_reprogramar_alerta_util, toggle_hbd_alerts_callback,
    hbd_alerts_command,
)
# Solo conservar: lang_command, set_language_callback
from handlers.alerts import (
    alerta_command, misalertas,
    borrar_alerta_callback, borrar_todas_alertas_callback,
)
from handlers.valerts_handlers import valerts_handlers_list
from core.valerts_loop import valerts_monitor_loop, set_valerts_sender
```

**Código a ELIMINAR en `post_init()`:**
- `asyncio.create_task(alerta_loop(app.bot))`
- `asyncio.create_task(check_custom_price_alerts(app.bot))`
- Bloque de programación de alertas para usuarios existentes (el for loop con `programar_alerta_usuario`)
- `asyncio.create_task(btc_monitor_loop(app.bot))`
- `asyncio.create_task(valerts_monitor_loop(app.bot))`

**Dependency injection a ELIMINAR en `main()`:**
- `set_reprogramar_alerta_util(programar_alerta_usuario)`
- `set_enviar_mensaje_telegram_async(enviar_mensajes, app)`
- `set_btc_sender(enviar_mensajes)`
- `set_valerts_sender(enviar_mensajes)`

**Handler registrations a ELIMINAR en `main()`:**
- `CommandHandler("mismonedas", mismonedas)`
- `CommandHandler("monedas", set_monedas_command)`
- `CommandHandler("parar", parar)`
- `CommandHandler("temp", cmd_temp)`
- `CommandHandler("hbdalerts", hbd_alerts_command)`
- `CommandHandler("alerta", alerta_command)`
- `CommandHandler("misalertas", misalertas)`
- `for handler in btc_handlers_list: app.add_handler(handler)`
- `app.add_handlers(valerts_handlers_list)`
- `CallbackQueryHandler(borrar_alerta_callback, ...)`
- `CallbackQueryHandler(borrar_todas_alertas_callback, ...)`
- `CallbackQueryHandler(toggle_hbd_alerts_callback, ...)`

**Secciones de comentarios a actualizar:**
- Eliminar sección "Comandos de Alertas"
- Eliminar sección "Handlers de BTC y VALERTS"
- Eliminar sección "Callbacks de Alertas" y "Callbacks de Configuración" (toggle_hbd)

**NOTA:** Mantener `enviar_mensajes()` ya que puede ser utilizada por el sistema de admin (`set_admin_util`).

---

### Task 4: Limpiar `core/loops.py`

**Archivo:** `core/loops.py`

**ELIMINAR FUNCIONES:**
- `set_enviar_mensaje_telegram_async()`
- `obtener_indicador()`
- `set_custom_alert_history_util()`
- `programar_alerta_usuario()`
- `check_custom_price_alerts()` (loop completo)
- `alerta_loop()` (loop completo)
- `alerta_trabajo_callback()` (callback completo)

**ELIMINAR VARIABLES GLOBALES:**
- `_enviar_mensaje_telegram_async_ref`
- `_app_ref`
- `PRECIOS_CONTROL_ANTERIORES`
- `CUSTOM_ALERT_HISTORY`

**ELIMINAR IMPORTS no usados:**
- `InlineKeyboardButton`, `InlineKeyboardMarkup` (si ya no se usan)
- `ParseMode`, `Bot`, `Update`, `ContextTypes`, `Application`
- `get_random_ad_text`
- Múltiples imports de `core.config` (INTERVALO_ALERTA, INTERVALO_CONTROL, CUSTOM_ALERT_HISTORY_PATH, PRICE_ALERTS_PATH, HBD_HISTORY_PATH, etc.)
- Múltiples imports de `utils.file_manager`
- `core.api_client` imports

**CONSERVAR:**
- `get_logs_data()` (usado por admin)
- `add_log_line` import (si se usa)
- `LOG_LINES` import

**RESULTADO FINAL:** El archivo quedará muy reducido, solo con `get_logs_data()`.

---

### Task 5: Limpiar `core/config.py`

**Archivo:** `core/config.py`

**ELIMINAR paths:**
```python
HBD_HISTORY_PATH = ...
CUSTOM_ALERT_HISTORY_PATH = ...
PRICE_ALERTS_PATH = ...
HBD_THRESHOLDS_PATH = ...
```

**ELIMINAR constantes:**
```python
INTERVALO_ALERTA = 300
INTERVALO_CONTROL = 480
```

**ELIMINAR API keys (si solo las usan alertas HBD):**
- `cmc_api_key_alerta` — EVALUAR: si `obtener_precios_control` usa `CMC_API_KEY_CONTROL` (sí), esta key de alerta se puede eliminar.
- `CMC_API_KEY_ALERTA` export

**CONSERVAR:**
- `LAST_PRICES_PATH` (usado por /ver)
- `CMC_API_KEY_CONTROL` (usado por /ver y /p)
- Todas las demás configuraciones

---

### Task 6: Limpiar `utils/file_manager.py`

**Archivo:** `utils/file_manager.py`

**ELIMINAR FUNCIONES (~20):**

*HBD:*
- `load_hbd_history()`
- `save_hbd_history()`
- `leer_precio_anterior_alerta()`
- `guardar_precios_alerta()`
- `load_hbd_thresholds()`
- `save_hbd_thresholds()`
- `modify_hbd_threshold()`
- `toggle_hbd_alert_status()`
- `get_hbd_alert_recipients()`

*Custom Alerts:*
- `cargar_custom_alert_history()`
- `guardar_custom_alert_history()`
- `load_price_alerts()`
- `save_price_alerts()`
- `add_price_alert()`
- `get_user_alerts()`
- `delete_price_alert()`
- `update_alert_status()`
- `delete_all_alerts()`

*Alert Timing:*
- `actualizar_intervalo_alerta()`
- `update_last_alert_timestamp()`

**MODIFICAR:**
- `inicializar_archivos()` — Eliminar inicialización de `CUSTOM_ALERT_HISTORY_PATH` y `HBD_THRESHOLDS_PATH`
- `registrar_usuario()` — Eliminar campo `hbd_alerts` del default. Eliminar `intervalo_alerta_h`.
- `check_feature_access()` — Eliminar reglas `alerts_capacity` y `temp_change_limit` y `temp_min_val`
- Imports de config: eliminar `CUSTOM_ALERT_HISTORY_PATH`, `PRICE_ALERTS_PATH`, `HBD_HISTORY_PATH`, `HBD_THRESHOLDS_PATH`

**CONSERVAR:**
- `cargar_usuarios()`, `guardar_usuarios()` — Gestión de usuarios general
- `registrar_usuario()` — (modificado)
- `obtener_monedas_usuario()`, `actualizar_monedas()` — Usado por /ver
- `obtener_datos_usuario()` — General
- `load_last_prices_status()`, `save_last_prices_status()` — Usado por /ver
- `add_log_line()` — Logging
- `check_feature_access()` — (modificado, mantener reglas de ver_limit, ta_limit, coins_capacity)
- `registrar_uso_comando()` — Tracking
- `set_user_language()`, `get_user_language()` — Idioma
- `add_subscription_days()` — Subscripciones
- `obtener_datos_usuario_seguro()` — (modificado)
- `migrate_user_timestamps()` — Migración

---

### Task 7: Limpiar `core/api_client.py`

**Archivo:** `core/api_client.py`

**ELIMINAR:**
- `generar_alerta()` — Generación de alertas HBD
- `obtener_precios_alerta()` — Obtención de precios para alertas HBD
- Imports de `file_manager.load_hbd_thresholds`

**CONSERVAR:**
- `obtener_precios_control()` — Usado por /ver, /monedas, /p
- `obtener_datos_moneda()` — Usado por /p
- `obtener_high_low_24h()` — Usado por /p
- `_obtener_precios()` — Helper genérico
- `_obtener_datos_cryptocompare()` — Fallback

---

### Task 8: Limpiar `handlers/user_settings.py`

**Archivo:** `handlers/user_settings.py`

**ELIMINAR FUNCIONES:**
- `hbd_alerts_command()`
- `toggle_hbd_alerts_callback()`
- `mismonedas()`
- `parar()`
- `cmd_temp()`
- `set_monedas_command()`
- `manejar_texto()`
- `set_reprogramar_alerta_util()` y variable `_reprogramar_alerta_ref`

**ELIMINAR IMPORTS no usados:**
- `toggle_hbd_alert_status`, `modify_hbd_threshold`, `load_hbd_thresholds` de file_manager
- `add_price_alert`, `get_user_alerts`, `delete_price_alert`, `delete_all_alerts` de file_manager
- `actualizar_monedas`, `obtener_monedas_usuario`, `actualizar_intervalo_alerta` de file_manager
- `set_custom_alert_history_util` de core.loops
- `obtener_precios_control` de core.api_client
- `ADMIN_CHAT_IDS` (si ya no se usa)
- Muchos imports de config que ya no se necesitan

**CONSERVAR:**
- `lang_command()`
- `set_language_callback()`
- Imports necesarios para idioma

---

### Task 9: Actualizar mensajes en `handlers/general.py`

**Archivo:** `handlers/general.py`

**MODIFICAR:**
- `HELP_MSG` — Eliminar sección "Comandos de Alertas" que menciona `/monedas`, `/mismonedas`, `/alerta`, `/misalertas`, `/parar`, `/temp`
- Mensaje de `/start` — Actualizar para no mencionar alertas, solo trading signals

**ELIMINAR imports no usados:**
- `obtener_monedas_usuario` (si /ver aún lo usa, mantener)
- `load_last_prices_status` (si /ver aún lo usa, mantener)

**NOTA:** Mantener `/ver` ya que es consulta manual de precios (no es alerta automática). Pero evaluar si tiene sentido sin el sistema de monedas configuradas — SI se mantiene /monedas, /ver sigue funcionando.

**DECISIÓN:** Mantener `/ver` y la funcionalidad de `/monedas` en `handlers/general.py` (solo la consulta de precios, no las alertas periódicas).

---

### Task 10: Verificación y testing

**Step 1: Verificar sintaxis Python**
```bash
python -m py_compile sipsignal.py
python -m py_compile core/loops.py
python -m py_compile core/config.py
python -m py_compile core/api_client.py
python -m py_compile utils/file_manager.py
python -m py_compile handlers/user_settings.py
python -m py_compile handlers/general.py
```

**Step 2: Ejecutar tests existentes**
```bash
python -m pytest tests/ -v
```

**Step 3: Verificar imports no rotos**
```bash
grep -rn "from handlers.alerts" --include="*.py" .
grep -rn "from handlers.btc_handlers" --include="*.py" .
grep -rn "from handlers.valerts_handlers" --include="*.py" .
grep -rn "from core.btc_loop" --include="*.py" .
grep -rn "from core.valerts_loop" --include="*.py" .
grep -rn "from utils.btc_manager" --include="*.py" .
grep -rn "from utils.valerts_manager" --include="*.py" .
grep -rn "alerta_loop" --include="*.py" .
grep -rn "check_custom_price_alerts" --include="*.py" .
grep -rn "programar_alerta_usuario" --include="*.py" .
grep -rn "hbd_alerts" --include="*.py" .
grep -rn "valerts" --include="*.py" .
```

**Step 4: Commit final**
```bash
git add -A
git commit -m "refactor: clean up shared modules after alert system removal"
```

---

## 📊 RESUMEN DE IMPACTO

| Métrica | Cantidad |
|---|---|
| Archivos eliminados | 16 (7 código + 9 data-example) |
| Archivos modificados | 7 |
| Funciones eliminadas | ~35 |
| Comandos eliminados | 8 (/alerta, /misalertas, /btcalerts, /valerts, /hbdalerts, /temp, /parar, /mismonedas) |
| Loops de fondo eliminados | 4 (alerta_loop, check_custom_price_alerts, btc_monitor_loop, valerts_monitor_loop) |
| Archivos intactos | 18+ |
| Comandos conservados | /start, /help, /ver, /myid, /mk, /graf, /p, /ta, /signal, /chart, /journal, /capital, /setup, /users, /logs, /ad, /lang, /monedas |

---

## ⚠️ NOTAS IMPORTANTES

1. **`/monedas` se mantiene** — La configuración de lista de monedas se conserva porque alimenta a `/ver` (consulta manual de precios). Solo se elimina el envío AUTOMÁTICO periódico.

2. **`core/btc_advanced_analysis.py` se mantiene** — Aunque era usado por btc_loop y valerts_loop (eliminados), también es importado por `handlers/ta.py` para análisis técnico manual.

3. **`utils/tv_helper.py` se mantiene** — Usado por `handlers/ta.py` para datos de TradingView en análisis técnico manual.

4. **`enviar_mensajes()` en sipsignal.py se mantiene** — Sigue siendo necesaria para el sistema de admin (`set_admin_util`) y potencialmente para señales.

5. **La función `set_enviar_mensaje_telegram_async` en loops.py se elimina** — Ya no hay loops que la necesiten.

6. **Datos existentes en `data/`** — Los archivos JSON de datos de alertas existentes en el servidor no se borran automáticamente, pero ya no serán leídos por ningún código.
