# Plan de Implementación: Gráficas Locales con `/chart`

> **Contexto:** Migrar el comando `/chart` de `sipsignal` para generar gráficos OHLCV
> localmente con `matplotlib` (estilo del motor de `bbalert`), eliminando la dependencia
> del `SCREENSHOT_API_KEY` externo. Los datos siguen viniendo de la API pública de Binance.

---

## Diagnóstico del estado actual

### Cómo funciona `/chart` hoy en sipsignal

```
/chart [timeframe]
    → chart_handler.py
        → ChartCapture.capture()
            → Intento 1: _capture_with_matplotlib()   ← ya existe, pero básico
            → Intento 2: _capture_with_api()          ← screenshot-api.org (externo, de pago)
```

El método `_capture_with_matplotlib()` ya existe en `bot/trading/chart_capture.py`, pero
su implementación es mínima: dibuja velas con líneas horizontales en vez de rectángulos,
no tiene indicadores (EMA, RSI, BB), no tiene tema TradingView y el layout es de dos paneles
simples sin identidad visual.

### Qué aporta el motor de bbalert

`bbalert/utils/chart_generator.py` tiene:
- Tema oscuro completo (`TV_THEME`) que replica TradingView
- Velas con `plt.Rectangle` (cuerpos) + `ax.plot` (mechas)
- EMA 20/50/200, Bollinger Bands y RSI calculados internamente con pandas/numpy
- Layout con `GridSpec` (3 paneles: precio, volumen, RSI)
- Niveles de Pivote/R1/S1, etiquetas flotantes, precio actual marcado
- Leyenda de indicadores, cabecera con símbolo + timeframe + variación %
- Exportación a `io.BytesIO` (sin tocar disco)
- Backend `Agg` para servidores headless

---

## Arquitectura objetivo

```
/chart BTCUSDT 4h
    → chart_handler.py         (mejorado: acepta símbolo + timeframe)
        → ChartCapture.capture()
            → BinanceAdapter.get_ohlcv()   (sin cambios)
            → LocalChartGenerator.generate()   ← NUEVO, motor de bbalert portado
                → io.BytesIO (PNG)
        → reply_photo(photo=buf)
```

No se elimina el fallback a la API de screenshot — se deja como opción desactivada por
defecto, útil si en el futuro se quiere activar con `SCREENSHOT_API_KEY`.

---

## Fases de implementación

---

### Fase 1 — Copiar e integrar el motor visual de bbalert

**Archivo a crear:** `bot/utils/chart_generator.py`

Este archivo es prácticamente una copia directa de `bbalert/utils/chart_generator.py`
con ajustes menores para adaptarlo a la estructura de sipsignal.

**Pasos:**

1. Copiar `bbalert/utils/chart_generator.py` a `bot/utils/chart_generator.py`.

2. Verificar que los imports no traigan dependencias que no existan en `requirements.txt`
   de sipsignal. Los que usa el motor son:
   - `io` — stdlib
   - `pandas` ✅ ya en requirements
   - `numpy` ✅ ya en requirements
   - `matplotlib` ✅ ya en requirements
   - `datetime` — stdlib

   No se necesita instalar nada nuevo.

3. Ajustar el watermark de la línea final:
   ```python
   # Cambiar:
   fig.text(0.03, 0.015, 'BitBreadAlert', ...)
   # Por:
   fig.text(0.03, 0.015, 'SipSignal', ...)
   ```

4. La firma de la función principal queda así (sin cambios sustanciales):
   ```python
   def generate_ohlcv_chart(
       df: pd.DataFrame,
       symbol: str,
       timeframe: str,
       show_ema: bool = True,
       show_bb: bool = False,
       show_rsi: bool = True,
       candles: int = 80,
       signal: str = "NEUTRAL",
       signal_emoji: str = "⚖️",
       pivot: float = 0,
       r1: float = 0,
       s1: float = 0,
   ) -> io.BytesIO | None:
   ```

---

### Fase 2 — Refactorizar `ChartCapture` para usar el motor local

**Archivo a modificar:** `bot/trading/chart_capture.py`

El objetivo es reemplazar `_generate_candlestick_chart()` con una llamada al nuevo
`generate_ohlcv_chart()` y simplificar la clase.

**Estado actual del método a reemplazar:**

```python
# ACTUAL — a reemplazar completamente
def _generate_candlestick_chart(self, df) -> bytes:
    fig, (ax_price, ax_volume) = plt.subplots(...)
    # ... lógica básica con líneas horizontales ...
    buf = io.BytesIO()
    plt.savefig(buf, format="png", ...)
    return buf.getvalue()
```

**Nuevo método:**

```python
# NUEVO
from bot.utils.chart_generator import generate_ohlcv_chart

def _generate_candlestick_chart(self, df: pd.DataFrame, symbol: str, timeframe: str) -> bytes | None:
    buf = generate_ohlcv_chart(
        df=df,
        symbol=symbol,
        timeframe=timeframe,
        show_ema=True,
        show_bb=False,
        show_rsi=True,
        candles=80,
    )
    if buf is None:
        return None
    return buf.getvalue()
```

**Ajuste en `_capture_with_matplotlib()`** — pasar `symbol` y `timeframe` al método:

```python
async def _capture_with_matplotlib(self, symbol: str, timeframe: str) -> bytes | None:
    try:
        df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
        if df is None or df.empty:
            logger.warning(f"No se pudieron obtener datos OHLCV para {symbol}")
            return None
        return self._generate_candlestick_chart(df, symbol, timeframe)
    except Exception as e:
        logger.warning(f"Error generando gráfico con matplotlib: {e}")
        return None
```

El resto de la clase (`capture()`, caché, `close()`, `_capture_with_api()`) no cambia.

---

### Fase 3 — Mejorar `chart_handler.py` para aceptar símbolo dinámico

**Archivo a modificar:** `bot/handlers/chart_handler.py`

El handler actual solo acepta timeframe como argumento y siempre usa `BTCUSDT`. Se mejora
para aceptar también el símbolo.

**Uso objetivo:**
```
/chart            → BTCUSDT 4h (defaults)
/chart 1h         → BTCUSDT 1h
/chart ETHUSDT    → ETHUSDT 4h
/chart ETHUSDT 1h → ETHUSDT 1h
```

**Lógica de parseo de argumentos:**

```python
VALID_TIMEFRAMES = ["1d", "4h", "1h", "15m", "30m"]
DEFAULT_TIMEFRAME = "4h"
DEFAULT_SYMBOL = "BTCUSDT"

@admin_only
async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    symbol = DEFAULT_SYMBOL
    timeframe = DEFAULT_TIMEFRAME

    for arg in args:
        arg_lower = arg.lower()
        arg_upper = arg.upper()
        if arg_lower in VALID_TIMEFRAMES:
            timeframe = arg_lower
        elif arg_upper.endswith("USDT") or arg_upper.endswith("BTC"):
            symbol = arg_upper
        else:
            await update.message.reply_text(
                f"⚠️ Argumento inválido: `{arg}`\n"
                f"Timeframes: `{', '.join(VALID_TIMEFRAMES)}`\n"
                f"Ejemplo: `/chart ETHUSDT 1h`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
```

**Flujo completo del handler:**

```python
    msg = await update.message.reply_text(
        f"⏳ *Generando gráfico {symbol} {timeframe.upper()}...*",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        chart_capture = ChartCapture()
        chart_bytes = await chart_capture.capture(symbol, timeframe)
        await chart_capture.close()

        now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        if chart_bytes:
            await msg.delete()
            await update.message.reply_photo(
                photo=chart_bytes,
                caption=f"📊 {symbol} {timeframe.upper()} — {now_utc}",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await msg.edit_text(
                "⚠️ *Error generando gráfico.*\nIntenta de nuevo en unos segundos.",
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        await msg.edit_text(f"⚠️ *Error:*\n_{str(e)}_", parse_mode=ParseMode.MARKDOWN)
```

---

### Fase 4 — Ejecutar en executor para no bloquear asyncio

El render de matplotlib es **CPU-bound y síncrono**. Llamarlo directamente en el handler
bloquea el event loop del bot durante el tiempo de generación (~0.5–2 segundos en un VPS
con RAM limitada).

La solución es usar `loop.run_in_executor()` exactamente como lo hace `bbalert/handlers/trading.py`.

**Dónde aplicarlo — en `_capture_with_matplotlib`:**

```python
import asyncio
from functools import partial

async def _capture_with_matplotlib(self, symbol: str, timeframe: str) -> bytes | None:
    try:
        df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
        if df is None or df.empty:
            return None

        loop = asyncio.get_event_loop()
        # Ejecutar render en thread pool para no bloquear el event loop
        data = await loop.run_in_executor(
            None,
            partial(self._generate_candlestick_chart, df, symbol, timeframe)
        )
        return data

    except Exception as e:
        logger.warning(f"Error generando gráfico con matplotlib: {e}")
        return None
```

---

### Fase 5 — Verificar dependencias en requirements

Confirmar que `matplotlib`, `numpy` y `pandas` están en `requirements.txt` (sí están).
No se necesita instalar nada extra.

Si el VPS tiene RAM muy limitada, considerar bajar el DPI del gráfico de `dpi=130` a
`dpi=100` en `generate_ohlcv_chart()` para reducir consumo de memoria durante el render.

**Línea a ajustar en `bot/utils/chart_generator.py`:**

```python
# Para VPS con RAM limitada (< 1GB):
fig.savefig(buf, format='png', dpi=100,   # ← bajar de 130 a 100
            facecolor=TV_THEME['bg'],
            bbox_inches='tight')
```

---

### Fase 6 — Prueba manual en VPS

Secuencia de verificación tras el deploy:

```bash
# 1. Activar venv y confirmar que matplotlib está disponible
source venv/bin/activate
python -c "import matplotlib; print(matplotlib.__version__)"

# 2. Test rápido del motor en aislado (sin bot corriendo)
python - <<'EOF'
import asyncio
import sys
sys.path.insert(0, '.')

from bot.infrastructure.binance.binance_adapter import BinanceAdapter
from bot.utils.chart_generator import generate_ohlcv_chart

async def test():
    adapter = BinanceAdapter()
    df = await adapter.get_ohlcv("BTCUSDT", "4h", limit=100)
    await adapter.close()
    buf = generate_ohlcv_chart(df, "BTCUSDT", "4h")
    if buf:
        with open("/tmp/test_chart.png", "wb") as f:
            f.write(buf.read())
        print("✅ Gráfico generado: /tmp/test_chart.png")
    else:
        print("❌ Error generando gráfico")

asyncio.run(test())
EOF

# 3. Copiar el PNG al local para verificar visualmente (opcional)
scp mowgli@<vps-ip>:/tmp/test_chart.png ~/Desktop/

# 4. Reiniciar el bot y probar el comando
/chart
/chart 1h
/chart ETHUSDT 4h
```

---

## Resumen de archivos modificados

| Archivo | Acción | Descripción |
|---|---|---|
| `bot/utils/chart_generator.py` | **Crear** | Motor visual portado de bbalert |
| `bot/trading/chart_capture.py` | **Modificar** | Reemplazar `_generate_candlestick_chart()` y ajustar `_capture_with_matplotlib()` |
| `bot/handlers/chart_handler.py` | **Modificar** | Aceptar símbolo dinámico + timeframe como argumentos |

Sin cambios en: `BinanceAdapter`, `main.py`, `requirements.txt`, base de datos, ni ningún
otro handler.

---

## Comportamiento esperado tras la implementación

```
Usuario: /chart
Bot: ⏳ Generando gráfico BTCUSDT 4H...
     [imagen PNG: gráfico oscuro estilo TradingView con velas, EMA 20/50/200,
      RSI, volumen, precio actual marcado, watermark "SipSignal"]

Usuario: /chart ETHUSDT 1h
Bot: ⏳ Generando gráfico ETHUSDT 1H...
     [imagen PNG: mismo estilo, datos de ETHUSDT en 1h]
```

Tiempo estimado de generación en el VPS: **1–3 segundos** (red Binance + render matplotlib).

Sin dependencia de APIs externas. Sin costos adicionales. Sin `SCREENSHOT_API_KEY`.
