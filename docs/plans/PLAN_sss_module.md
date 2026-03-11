# Plan de Implementación: Módulo SSS para sipsignal

> **Qué es SSS:** SmartSignals Strategy — permite que cada usuario active una
> estrategia de trading personalizada (definida en JSON) que se aplica sobre
> las señales del bot, enriqueciéndolas con TP1/TP2/TP3, SL dinámico y
> apalancamiento calculado. Incluye backtest histórico sobre Binance y subida
> de estrategias propias en `.json`.

---

## Diagnóstico: diferencias clave entre bbalert y sipsignal

Antes de copiar, hay que entender qué cambia entre los dos proyectos:

| Aspecto | bbalert | sipsignal |
|---|---|---|
| Control de acceso | `check_feature_access(user_id, 'sp_signals')` → devuelve tier | `@admin_only` / `@permitted_only` desde `decorators.py` |
| Logger | `logging.getLogger(__name__)` | `from bot.utils.logger import logger` (loguru) |
| Config paths | `from core.config import DATA_DIR, ADMIN_CHAT_IDS` | `from bot.core.config import DATA_DIR, ADMIN_IDS` |
| Señal base | `SPSignalEngine.analyze(df)` → dict con `direction/score/atr/rsi` | `Signal` dataclass + `calculate_all()` desde `technical_analysis.py` |
| Handlers | `from handlers.sp_handlers import ...` | `from bot.handlers.signal_handler import ...` |
| pandas_ta | `import pandas_ta as pta` (mismo) | `import pandas_ta` (ya instalado) |
| Rutas de módulo | `utils/sss_manager.py` | `bot/utils/sss_manager.py` |

El módulo SSS de bbalert **no tiene dependencias circulares** respecto a sipsignal
porque el motor de señales del backtest está inlinado. La única adaptación real
es en los imports y en el sistema de tiers.

---

## Arquitectura del módulo SSS en sipsignal

```
bot/
├── utils/
│   └── sss_manager.py          ← NUEVO (portado de bbalert + adaptado)
├── handlers/
│   └── sss_handler.py          ← NUEVO (callbacks de UI y upload de JSON)
└── data/
    └── sss/
        ├── strategies/          ← NUEVO directorio (creado en runtime)
        │   ├── sasas_pro.json   ← NUEVO estrategia base 1
        │   ├── momentum.json    ← NUEVO estrategia base 2
        │   └── swing_wave.json  ← NUEVO estrategia base 3
        └── user_prefs.json      ← NUEVO generado en runtime (gitignored)
```

**Archivos modificados:**
- `bot/core/config.py` — agregar rutas SSS
- `bot/handlers/signal_handler.py` — integrar enriquecimiento SSS en `/signal`
- `bot/main.py` — registrar handlers SSS

---

## Fase 1 — Adaptar y crear `bot/utils/sss_manager.py`

Copiar `bbalert/utils/sss_manager.py` con los siguientes cambios de adaptación.

### 1.1 Cambiar los imports del bloque superior

**bbalert (original):**
```python
from core.config import DATA_DIR, ADMIN_CHAT_IDS
from utils.file_manager import check_feature_access
```

**sipsignal (nuevo):**
```python
from bot.core.config import DATA_DIR, ADMIN_CHAT_IDS
# check_feature_access NO existe en sipsignal — se implementa inline (ver 1.2)
```

### 1.2 Reemplazar el sistema de tiers

En bbalert, `_user_tier()` llama a `check_feature_access()` para saber si un
usuario es premium. En sipsignal no existe ese concepto — el control de acceso
es binario: `admin` o `approved`. Se simplifica así:

**bbalert (original):**
```python
def _user_tier(user_id: int) -> str:
    if user_id in ADMIN_CHAT_IDS:
        return 'admin'
    ok, _ = check_feature_access(user_id, 'sp_signals')
    return 'premium' if ok else 'base'
```

**sipsignal (nuevo) — reemplazar completamente:**
```python
# En sipsignal todos los usuarios approved tienen acceso 'base'.
# Solo los admins tienen 'admin'. No hay tier 'premium' por ahora.

def _user_tier(user_id: int) -> str:
    """Devuelve 'admin' o 'base'. En sipsignal no hay tier premium."""
    if user_id in ADMIN_CHAT_IDS:
        return 'admin'
    return 'base'
```

> **Nota:** Esto significa que todos los usuarios con acceso verán las
> estrategias de tier `base` y `premium` (ya que base ≥ base y base no
> bloquea premium). Si en el futuro se quiere restringir estrategias premium,
> se cambia esta función para consultar la BD.
>
> Para que las estrategias base sean accesibles a todos los approved, cambiar
> también `_tier_allows`:
> ```python
> # Asegurarse de que 'base' >= 'base' y 'base' >= 'premium' para sipsignal
> # dado que todos los approved son tratados igual:
> _TIER_RANK = {'base': 1, 'premium': 1, 'admin': 2}
> ```

### 1.3 Cambiar el logger

**bbalert:**
```python
logger = logging.getLogger(__name__)
```

**sipsignal:**
```python
from bot.utils.logger import logger
# Eliminar: import logging
```

### 1.4 Ajustar las rutas SSS

Las rutas `SSS_DIR`, `SSS_STRAT_DIR`, `SSS_PREFS_PATH` ya funcionan porque
usan `DATA_DIR` de config, que en sipsignal apunta a `bot/data/`. No cambia nada.

### 1.5 El resto del archivo — sin cambios

Todo lo demás (`_load_from_disk`, `get_available_strategies`, `get_user_strategy`,
`set_user_strategy`, `_compute_supertrend`, `_compute_ash`, `_compute_adx`,
`compute_extended_indicators`, `apply_strategy_filter`, `enrich_signal`,
`build_strategy_signal_block`, `format_strategy_detail`, `validate_strategy_json`,
`save_user_strategy_file`, `run_strategy_backtest`, `format_backtest_result`,
`init_sss`) se copia **sin modificar**.

---

## Fase 2 — Agregar rutas SSS a `bot/core/config.py`

Agregar las 3 constantes de ruta al final del bloque de paths existente:

```python
# --- Rutas SSS (SmartSignals Strategy) ---
SSS_DIR        = os.path.join(DATA_DIR, "sss")
SSS_STRAT_DIR  = os.path.join(SSS_DIR, "strategies")
SSS_PREFS_PATH = os.path.join(SSS_DIR, "user_prefs.json")
```

> `sss_manager.py` construye estas rutas internamente también, pero
> exportarlas desde config permite importarlas en los handlers para
> validaciones de seguridad (ej: check `SSS_STRAT_DIR` en el handler de upload).

---

## Fase 3 — Crear las estrategias base en JSON

Crear el directorio `bot/data/sss/strategies/` y las 3 estrategias incluidas.
Estas son las mismas que bbalert usa internamente pero como archivos `.json`
portables.

### `bot/data/sss/strategies/sasas_pro.json`
```json
{
  "id": "sasas_pro",
  "name": "SASAS Pro",
  "version": "2.0.0",
  "author": "SipSignal",
  "tier": "base",
  "style": "swing",
  "emoji": "🔬",
  "description": "Estrategia de swing con Supertrend + ASH para confirmar la dirección. Diseñada para mercados con tendencia definida.",
  "timeframes": ["1h", "4h"],
  "entry_filter": {
    "min_score": 5.0,
    "supertrend_align": true,
    "ash_signal": true,
    "volume_spike": false,
    "adx_min": 0,
    "adx_di_confirm": false,
    "macd_cross_required": false
  },
  "risk": {
    "sl_type": "atr",
    "sl_atr_mult": 1.5,
    "tp1_atr_mult": 2.0,  "tp1_close_pct": 50,
    "tp2_atr_mult": 3.5,  "tp2_close_pct": 30,
    "tp3_atr_mult": 5.5,  "tp3_close_pct": 20,
    "trailing_after_tp1": true,
    "trailing_type": "supertrend"
  },
  "leverage": {
    "default": 5,
    "max": 20,
    "volatile_reduce": true,
    "volatile_threshold": 0.03,
    "volatile_max": 10
  },
  "capital": {
    "small_threshold": 22,
    "small_exit": "full_tp1",
    "large_exit": "partial_trail"
  },
  "meta": {
    "win_rate_est": "58-65%",
    "rr_ratio": "1:1.3 / 1:2.3",
    "best_markets": "Tendencia clara BTC/ETH con volumen sostenido",
    "avoid_markets": "Rango lateral, alta volatilidad sin dirección"
  }
}
```

### `bot/data/sss/strategies/momentum_scalper.json`
```json
{
  "id": "momentum_scalper",
  "name": "Momentum Scalper",
  "version": "1.5.0",
  "author": "SipSignal",
  "tier": "base",
  "style": "scalping",
  "emoji": "⚡",
  "description": "Scalping agresivo con MACD cross y volumen. Entradas rápidas en movimientos de impulso con TPs ajustados.",
  "timeframes": ["1m", "5m", "15m"],
  "entry_filter": {
    "min_score": 4.5,
    "supertrend_align": false,
    "ash_signal": false,
    "volume_spike": true,
    "volume_spike_mult": 1.5,
    "adx_min": 20,
    "adx_di_confirm": true,
    "macd_cross_required": true
  },
  "risk": {
    "sl_type": "atr",
    "sl_atr_mult": 1.2,
    "tp1_atr_mult": 1.5,  "tp1_close_pct": 60,
    "tp2_atr_mult": 2.5,  "tp2_close_pct": 30,
    "tp3_atr_mult": 4.0,  "tp3_close_pct": 10,
    "trailing_after_tp1": false,
    "trailing_type": null
  },
  "leverage": {
    "default": 10,
    "max": 25,
    "volatile_reduce": true,
    "volatile_threshold": 0.025,
    "volatile_max": 8
  },
  "capital": {
    "small_threshold": 22,
    "small_exit": "full_tp1",
    "large_exit": "partial_trail"
  },
  "meta": {
    "win_rate_est": "52-60%",
    "rr_ratio": "1:1.25 / 1:2.1",
    "best_markets": "Ruptura de nivel con spike de volumen, primeras horas NYC/London",
    "avoid_markets": "Horas de baja liquidez, fins de semana"
  }
}
```

### `bot/data/sss/strategies/swing_wave.json`
```json
{
  "id": "swing_wave",
  "name": "Swing Wave",
  "version": "1.2.0",
  "author": "SipSignal",
  "tier": "base",
  "style": "position",
  "emoji": "🌊",
  "description": "Posiciones de mediano plazo basadas en ADX fuerte y confirmación DI. Ideada para capitalizar grandes movimientos.",
  "timeframes": ["4h", "1d"],
  "entry_filter": {
    "min_score": 6.0,
    "supertrend_align": false,
    "ash_signal": false,
    "volume_spike": false,
    "adx_min": 25,
    "adx_di_confirm": true,
    "macd_cross_required": false
  },
  "risk": {
    "sl_type": "atr",
    "sl_atr_mult": 2.0,
    "tp1_atr_mult": 3.0,  "tp1_close_pct": 40,
    "tp2_atr_mult": 5.0,  "tp2_close_pct": 35,
    "tp3_atr_mult": 8.0,  "tp3_close_pct": 25,
    "trailing_after_tp1": true,
    "trailing_type": "ema"
  },
  "leverage": {
    "default": 3,
    "max": 10,
    "volatile_reduce": true,
    "volatile_threshold": 0.04,
    "volatile_max": 5
  },
  "capital": {
    "small_threshold": 50,
    "small_exit": "full_tp1",
    "large_exit": "partial_trail"
  },
  "meta": {
    "win_rate_est": "55-62%",
    "rr_ratio": "1:1.5 / 1:2.5",
    "best_markets": "Ciclos alcistas/bajistas sostenidos de BTC, post-halving",
    "avoid_markets": "Mercado en consolidación, score < 6"
  }
}
```

---

## Fase 4 — Crear `bot/handlers/sss_handler.py`

Este es el handler principal de la UI SSS. En bbalert toda la lógica SSS está
en `sp_handlers.py`. En sipsignal se extrae a su propio archivo para mantener
la arquitectura limpia.

### Estructura del archivo:

```python
# bot/handlers/sss_handler.py
# SSS — SmartSignals Strategy: UI de selección, activación, backtest y upload.

import json

from telegram import Document, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.core.config import ADMIN_CHAT_IDS
from bot.utils import permitted_only
from bot.utils.logger import logger

# Import SSS con degradación graceful
try:
    from bot.utils.sss_manager import (
        SSS_STRAT_DIR,
        build_strategy_signal_block,
        format_backtest_result,
        format_strategy_detail,
        get_available_strategies,
        get_strategy_by_id,
        get_user_strategy,
        run_strategy_backtest,
        save_user_strategy_file,
        set_user_strategy,
        validate_strategy_json,
    )
    _SSS_OK = True
except ImportError:
    _SSS_OK = False
    run_strategy_backtest = None
    format_backtest_result = None
```

### Función `_build_strategies_text()` y `_build_strategies_keyboard()`

Son helpers de UI idénticos a bbalert. Se copian sin cambios excepto los
callback_data que siguen el patrón `sss_*` en lugar de `sp_strat_*` para
no colisionar con handlers futuros de `sp`:

```python
# PATRÓN DE CALLBACKS (adaptar de bbalert):
# sp_strategies      → sss_menu
# sp_strat_detail|X  → sss_detail|X
# sp_strat_activate|X→ sss_activate|X
# sp_strat_deactivate→ sss_deactivate
# sp_strat_test|X|SYM→ sss_test|X|SYM
# sp_strat_upload    → sss_upload
```

### Comando `/sss`

Punto de entrada por comando directo (además del botón inline desde `/signal`):

```python
@permitted_only
async def sss_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abre el menú de estrategias SSS."""
    user_id = update.effective_user.id
    # ... misma lógica que sp_strategies_callback de bbalert
```

### Callbacks de la UI

Copiar los siguientes callbacks de `bbalert/handlers/sp_handlers.py`,
renombrando prefijos `sp_strat_` → `sss_` en los nombres de función y
`callback_data`:

| bbalert (función) | sipsignal (función) | callback_data |
|---|---|---|
| `sp_strategies_callback` | `sss_menu_callback` | `sss_menu` |
| `sp_strat_detail_callback` | `sss_detail_callback` | `sss_detail\|ID` |
| `sp_strat_activate_callback` | `sss_activate_callback` | `sss_activate\|ID` |
| `sp_strat_deactivate_callback` | `sss_deactivate_callback` | `sss_deactivate` |
| `sp_strat_test_callback` | `sss_test_callback` | `sss_test\|ID\|SYM` |
| `sp_strat_upload_callback` | `sss_upload_callback` | `sss_upload` |
| `sp_strategy_document_handler` | `sss_document_handler` | (MessageHandler) |

### Adaptaciones en los callbacks

**Control de acceso:** bbalert usa `_check_sp_access(user_id)`. En sipsignal
se reemplaza por la verificación de BD directa:

```python
# bbalert:
has_access, _ = _check_sp_access(user_id)
if not has_access:
    await query.answer("❌ Necesitas SmartSignals Pro.", show_alert=True)
    return

# sipsignal — reemplazar por:
from bot.db.users import get_user
user = await get_user(user_id)
if not user or user.get("status") not in ("approved", "admin"):
    await query.answer("❌ Necesitas acceso aprobado.", show_alert=True)
    return
```

**`_best_test_symbol()`:** En bbalert obtiene el mejor símbolo de la lista de
suscripciones del usuario. En sipsignal simplificar a `"BTCUSDT"` por ahora:

```python
def _best_test_symbol(user_id: int) -> str:
    return "BTCUSDT"
```

**`add_log_line()`:** En bbalert es una función del sistema de logs del bot.
En sipsignal usar directamente el logger:

```python
# bbalert:
add_log_line(f"[SSS] user {user_id} activó estrategia {strat_id}")

# sipsignal:
logger.info(f"[SSS] user {user_id} activó estrategia {strat_id}")
```

**`_safe_nav()`:** Helper de bbalert para editar mensajes inline con fallback.
Se puede copiar directamente o simplificar:

```python
async def _safe_nav(query, text: str, markup: InlineKeyboardMarkup):
    """Edita el mensaje inline con manejo de errores."""
    try:
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup
        )
    except Exception:
        try:
            await query.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup
            )
        except Exception:
            pass
```

### Callback de backtest `sss_test_callback`

Este callback es CPU-intensivo (descarga 500 velas y simula operaciones).
Debe ejecutarse en executor exactamente como en bbalert:

```python
async def sss_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user_id = query.from_user.id
    # ...
    if not _SSS_OK or run_strategy_backtest is None:
        await query.answer("⚠️ Módulo SSS no disponible.", show_alert=True)
        return

    await query.answer()
    msg = await query.message.reply_text(
        f"⏳ *Ejecutando backtest {strat_id} en {symbol}...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        loop = asyncio.get_event_loop()
        from functools import partial
        result = await loop.run_in_executor(
            None,
            partial(run_strategy_backtest, strat, symbol, 500)
        )
        text = format_backtest_result(result, strat)
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"[SSS Test] Excepción en backtest {strat_id}/{symbol}: {e}")
        await msg.edit_text(f"❌ Error en backtest: `{e}`", parse_mode=ParseMode.MARKDOWN)
```

### Registro de handlers al final del archivo

```python
sss_handlers_list = [
    CommandHandler("sss", sss_command),
    # Menú y navegación
    CallbackQueryHandler(sss_menu_callback,       pattern=r"^sss_menu$"),
    CallbackQueryHandler(sss_detail_callback,     pattern=r"^sss_detail\|"),
    CallbackQueryHandler(sss_activate_callback,   pattern=r"^sss_activate\|"),
    CallbackQueryHandler(sss_deactivate_callback, pattern=r"^sss_deactivate$"),
    CallbackQueryHandler(sss_test_callback,       pattern=r"^sss_test\|"),
    CallbackQueryHandler(sss_upload_callback,     pattern=r"^sss_upload$"),
    # Upload de estrategia JSON
    MessageHandler(
        filters.Document.MimeType("application/json") | filters.Document.FileExtension("json"),
        sss_document_handler,
    ),
]
```

---

## Fase 5 — Integrar SSS en `bot/handlers/signal_handler.py`

El punto de integración principal: cuando el usuario ejecuta `/signal`, si
tiene una estrategia activa, el mensaje de señal se enriquece con TP/SL/leverage.

### Estado actual de `signal_handler.py`

```python
# Actualmente el handler construye el mensaje así:
message = (
    f"📊 *BTC/USDT — Análisis 4H*\n"
    f"💰 *Precio:* `${signal.entry_price:,.2f}`\n"
    # ...
)
if signal_active:
    message += (
        f"├ TP: `${signal.tp1_level:,.2f}`\n"
        f"├ SL: `${signal.sl_level:,.2f}`\n"
        # ...
    )
```

### Qué agregar

Al inicio del archivo, después de los imports existentes:

```python
# SSS: estrategias personalizadas por usuario
try:
    from bot.utils.sss_manager import (
        apply_strategy_filter,
        build_strategy_signal_block,
        compute_extended_indicators,
        enrich_signal,
        get_user_strategy,
    )
    _SSS_OK = True
except ImportError:
    _SSS_OK = False
```

Dentro de `signal_command()`, antes de enviar el mensaje, agregar el bloque
de enriquecimiento SSS:

```python
# Convertir Signal dataclass a dict compatible con sss_manager
sig_dict = {
    'direction':  'BUY' if signal.direction == 'LONG' else ('SELL' if signal.direction == 'SHORT' else 'NEUTRAL'),
    'price':      signal.entry_price,
    'atr':        signal.atr_value,
    'rsi':        50.0,           # Si no se calcula en sipsignal, valor neutro
    'score_abs':  6.0,            # Idem — o extraerlo del análisis si está disponible
    'score':      6.0,
    'reasons':    [],
    'stop':       signal.sl_level,
    'target1':    signal.tp1_level,
    'target2':    signal.tp1_level,
    'open_time':  0,
}

strat_block = ""
if _SSS_OK and signal_active:
    try:
        strat = get_user_strategy(update.effective_user.id)
        if strat and timeframe in strat.get('timeframes', []):
            loop = asyncio.get_event_loop()
            df_ext = await loop.run_in_executor(
                None, compute_extended_indicators, df, strat
            )
            passes, reason = apply_strategy_filter(strat, sig_dict, df_ext)
            if passes:
                sig_e = enrich_signal(strat, sig_dict, df_ext)
                strat_block = "\n" + build_strategy_signal_block(sig_e)
            else:
                name = strat.get('name', '')[:20]
                strat_block = (
                    f"\n\n────────────────────\n"
                    f"🧠 *{name}* — filtro activo\n"
                    f"⚠️ _{reason}_\n"
                    f"────────────────────"
                )
    except Exception as e:
        logger.warning(f"[SSS] Error enriqueciendo señal: {e}")

# Agregar strat_block al mensaje antes de enviarlo:
message += strat_block
```

> **Sobre `df`:** El `df` del que se necesita DataFrame es el mismo que ya
> se obtiene en `GetSignalAnalysis.execute()`. Hay que asegurarse de que
> sea accesible en el scope del handler, o pasarlo como parte del `result`
> del use case. Si no está disponible directamente, se puede obtener con
> `BinanceAdapter().get_ohlcv("BTCUSDT", timeframe, 200)` en el handler.

### Botón SSS en el teclado inline de `/signal`

Agregar un botón al keyboard que muestra `/signal` para que el usuario pueda
ir directamente al menú de estrategias:

```python
# Teclado inline bajo la señal
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🧠 Estrategia SSS", callback_data="sss_menu")],
])
# Usar reply_markup=keyboard en reply_photo() o edit_text()
```

---

## Fase 6 — Registrar handlers en `bot/main.py`

### 6.1 Import

```python
from bot.handlers.sss_handler import sss_handlers_list
```

### 6.2 Agregar al bloque de registro (después de `signal_handlers_list`)

```python
# SSS — Estrategias personalizadas
for handler in sss_handlers_list:
    app.add_handler(handler)
```

### 6.3 Inicializar SSS en `post_init`

En la función `post_init` (que corre al arrancar el bot) agregar:

```python
# Inicializar módulo SSS (crea directorios si no existen)
try:
    from bot.utils.sss_manager import init_sss
    init_sss()
    logger.info("✅ Módulo SSS inicializado")
except Exception as e:
    logger.warning(f"⚠️ SSS no disponible: {e}")
```

---

## Fase 7 — Actualizar `.gitignore`

El archivo `user_prefs.json` contiene preferencias de usuarios y no debe
subirse al repo:

```
# Datos SSS de usuario
bot/data/sss/user_prefs.json
bot/data/sss/strategies/user_*.json
```

---

## Resumen de archivos

| Archivo | Acción | Descripción |
|---|---|---|
| `bot/utils/sss_manager.py` | **Crear** | Motor SSS portado de bbalert, con imports adaptados |
| `bot/handlers/sss_handler.py` | **Crear** | UI completa: menú, detalle, activar, backtest, upload |
| `bot/data/sss/strategies/sasas_pro.json` | **Crear** | Estrategia base 1 |
| `bot/data/sss/strategies/momentum_scalper.json` | **Crear** | Estrategia base 2 |
| `bot/data/sss/strategies/swing_wave.json` | **Crear** | Estrategia base 3 |
| `bot/core/config.py` | **Modificar** | Agregar `SSS_DIR`, `SSS_STRAT_DIR`, `SSS_PREFS_PATH` |
| `bot/handlers/signal_handler.py` | **Modificar** | Integrar bloque SSS + botón inline |
| `bot/main.py` | **Modificar** | Importar y registrar `sss_handlers_list` + `init_sss()` |
| `.gitignore` | **Modificar** | Ignorar `user_prefs.json` y estrategias de usuario |

---

## Flujo de usuario final

```
Usuario: /signal
Bot: ⏳ Analizando mercado...
     [foto + mensaje de señal BTC 4h]
     [botón: 🧠 Estrategia SSS]

Usuario: [toca 🧠 Estrategia SSS]
Bot: 🧠 SmartSignals Strategy (SSS)
     Activa: Ninguna
     [🔬 SASAS Pro] [⚡ Momentum Scalper]
     [🌊 Swing Wave]
     [📤 Mi Estrategia] [🔙 Volver]

Usuario: [toca 🔬 SASAS Pro]
Bot: 🔬 SASAS Pro v2.0.0
     ... detalles de la estrategia ...
     [✅ Activar] [🧪 Test]

Usuario: [toca ✅ Activar]
Bot: ✅ 'SASAS Pro' activada.

Usuario: /signal (segunda vez)
Bot: [señal enriquecida con TP1/TP2/TP3, SL, leverage calculado por SASAS Pro]
```

---

## Verificación en VPS

```bash
# 1. Verificar que pandas_ta está instalado (ya está en requirements.txt)
python -c "import pandas_ta; print('pandas_ta OK')"

# 2. Probar el manager en aislado
python - <<'EOF'
import sys
sys.path.insert(0, '.')
from bot.utils.sss_manager import get_available_strategies, init_sss
init_sss()
strats = get_available_strategies(999999)  # user_id ficticio
print(f"Estrategias cargadas: {[s['name'] for s in strats]}")
EOF

# 3. Probar el backtest
python - <<'EOF'
import sys
sys.path.insert(0, '.')
from bot.utils.sss_manager import get_strategy_by_id, run_strategy_backtest, format_backtest_result
strat = get_strategy_by_id('momentum_scalper')
result = run_strategy_backtest(strat, 'BTCUSDT', 300)
print(format_backtest_result(result, strat))
EOF

# 4. Reiniciar el bot
sudo systemctl restart sipsignal
```
