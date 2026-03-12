# Plan de Mejoramiento Visual — Gráfico de Velas
## `bot/utils/chart_generator.py` + `bot/trading/chart_capture.py`

> **Problema:** Las velas se renderizan como cruces OHLC flotantes, el gráfico
> aparece recortado en Telegram, y solo muestra 20 velas (3 días de historia).
> **Objetivo:** Velas japonesas con cuerpo relleno, 3 paneles limpios
> (precio / volumen / RSI), header estilo TradingView.

---

## Los 5 bugs raíz

### Bug 1 — Las "velas" son barras OHLC, no velas japonesas

`_draw_candlestick()` dibuja el cuerpo como **dos líneas horizontales** para
open y close. Eso produce una cruz en T, no una vela japonesa con cuerpo relleno.

```python
# CÓDIGO ACTUAL — produce cruz OHLC:
ax.plot([date - 0.4, date + 0.4], [o, o], color=color, linewidth=1.2)  # línea open
ax.plot([date - 0.4, date + 0.4], [c, c], color=color, linewidth=1.2)  # línea close
```

El cuerpo relleno requiere `matplotlib.patches.Rectangle`.

---

### Bug 2 — Ancho de vela fijo `±0.4` ignora el timeframe

En matplotlib, 1 unidad del eje X = 1 día. El gap entre velas depende del
timeframe. Con el offset fijo de `0.4`, las velas se solapan violentamente:

| Timeframe | Gap entre velas | Ancho actual (0.4×2) | Solapamiento |
|-----------|----------------|----------------------|--------------|
| 15m | 0.0104 días | 0.8 | **76×** |
| 1h | 0.0417 días | 0.8 | **19×** |
| 4h | 0.1667 días | 0.8 | **4.8×** |
| 1d | 1.0000 días | 0.8 | ✅ correcto |

El gráfico de la imagen enviada se ve como "estática" porque las 80 velas
se dibujan 4.8× encima unas de otras.

---

### Bug 3 — `add_subplot(111)` para el watermark rompe `tight_layout()`

```python
# CÓDIGO ACTUAL — crea un Axes que cubre toda la figura:
ax_watermark = fig.add_subplot(111, facecolor="none")
# ...
plt.tight_layout()  # ← Warning + márgenes incorrectos → recorte en Telegram
```

`add_subplot(111)` superpone un Axes encima de todos los paneles.
`tight_layout()` detecta la incompatibilidad y deja márgenes corruptos.
Ese es el origen del recorte visible en Telegram.

---

### Bug 4 — Solo 20 velas, cobertura temporal insuficiente

```python
# CÓDIGO ACTUAL en chart_capture.py:
buf = generate_ohlcv_chart(df=df, ..., candles=20)
```

20 velas × 4h = 3.3 días de historia. El gráfico de referencia muestra ~13 días.
Además, `limit=100` en la descarga apenas alcanza cuando EMA200 necesita
200 puntos de calentamiento.

---

### Bug 5 — `savefig` sin `bbox_inches='tight'` recorta el título

```python
# CÓDIGO ACTUAL:
plt.savefig(buf, format="png", facecolor=COLOR_BG, dpi=100)
```

Sin `bbox_inches='tight'`, matplotlib no incluye elementos fuera del bounding
box declarado (título, etiquetas del borde). Resultado: título parcialmente
cortado en la imagen que recibe el usuario.

---

## Archivos a modificar

| Archivo | Cambios |
|---|---|
| `bot/utils/chart_generator.py` | 7 cambios — bugs 1, 2, 3, 5 + mejoras visuales |
| `bot/trading/chart_capture.py` | 2 cambios — bug 4 |

---

## Archivo 1: `bot/utils/chart_generator.py`

### Cambio 1.1 — Imports: agregar `mpatches` y `numpy`

```python
# ANTES:
import io

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# DESPUÉS:
import io

import matplotlib
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
```

---

### Cambio 1.2 — Colores y nuevas constantes de timeframe

**Cambiar** `COLOR_UP` y `COLOR_DOWN` para coincidir con TradingView clásico:

```python
# ANTES:
COLOR_UP = "#089981"
COLOR_DOWN = "#F23645"

# DESPUÉS:
COLOR_UP = "#26A69A"
COLOR_DOWN = "#EF5350"
```

**Agregar** al final del bloque de constantes de color (después de `COLOR_WEBSITE`):

```python
# Timeframe → horas (para calcular ancho de vela dinámico)
_TF_HOURS: dict[str, float] = {
    "1m": 1 / 60, "3m": 3 / 60, "5m": 5 / 60,
    "15m": 0.25,  "30m": 0.5,
    "1h": 1,      "2h": 2,      "4h": 4,
    "6h": 6,      "8h": 8,      "12h": 12,
    "1d": 24,     "3d": 72,     "1w": 168,
}
```

---

### Cambio 1.3 — Nueva función `_infer_candle_width(df)`

Agregar **antes** de `_calculate_ema`. Infiere el ancho correcto de vela
directamente del índice del DataFrame, sin depender del string `timeframe`:

```python
def _infer_candle_width(df: pd.DataFrame) -> float:
    """
    Calcula el ancho de vela en unidades matplotlib.dates (días).
    Usa el índice del DataFrame para ser robusto con cualquier timeframe.
    Retorna 65% del gap entre velas consecutivas.
    """
    if len(df) >= 2:
        dt0 = mdates.date2num(df.index[0].to_pydatetime())
        dt1 = mdates.date2num(df.index[1].to_pydatetime())
        return abs(dt1 - dt0) * 0.65
    return 0.058  # fallback: ~65% del gap de 4h en días
```

---

### Cambio 1.4 — Reescribir `_draw_candlestick()` con `Rectangle`

```python
# ANTES (función completa):
def _draw_candlestick(ax, df, dates):
    """Draw candlestick chart with TradingView style."""
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values

    for _i, (date, o, h, low_price, c) in enumerate(
        zip(dates, opens, highs, lows, closes, strict=False)
    ):
        color = COLOR_UP if c >= o else COLOR_DOWN

        # Wick (thin, subtle)
        ax.plot([date, date], [low_price, h], color=color, linewidth=0.8, alpha=0.8)

        # Body (wider and more visible)
        if abs(c - o) > 0.0001:
            ax.plot([date - 0.4, date + 0.4], [o, o], color=color, linewidth=1.2)
            ax.plot([date - 0.4, date + 0.4], [c, c], color=color, linewidth=1.2)
        else:
            # Doji
            ax.plot([date - 0.5, date + 0.5], [o, o], color=color, linewidth=1.5)


# DESPUÉS (función completa):
def _draw_candlestick(ax, df: pd.DataFrame, dates_num, body_w: float) -> None:
    """
    Dibuja velas japonesas con cuerpo relleno (Rectangle) y mecha (plot).
    body_w: ancho del cuerpo en unidades mdates (días). Ver _infer_candle_width().
    """
    for dt_num, row in zip(dates_num, df.itertuples()):
        o, h, l, c = row.open, row.high, row.low, row.close
        color    = COLOR_UP if c >= o else COLOR_DOWN
        body_bot = min(o, c)
        # Doji: cuerpo mínimo visible (0.5% del rango de la vela)
        body_h   = abs(c - o) if abs(c - o) > 1e-8 else (h - l) * 0.005

        # Mecha (wick)
        ax.plot([dt_num, dt_num], [l, h],
                color=color, linewidth=0.85, zorder=2)
        # Cuerpo relleno
        rect = mpatches.Rectangle(
            (dt_num - body_w / 2, body_bot),
            width=body_w, height=body_h,
            facecolor=color, edgecolor=color,
            linewidth=0, zorder=3,
        )
        ax.add_patch(rect)
```

---

### Cambio 1.5 — Reescribir `_draw_volume()` con `Rectangle` y EMA de volumen

```python
# ANTES (función completa):
def _draw_volume(ax, df, dates):
    """Draw volume bars."""
    volumes = df["volume"].values
    colors = [
        COLOR_UP if df["close"].iloc[i] >= df["open"].iloc[i] else COLOR_DOWN
        for i in range(len(df))
    ]

    for i, (date, vol) in enumerate(zip(dates, volumes, strict=False)):
        ax.bar(date, vol, width=0.6, color=colors[i], alpha=0.7)


# DESPUÉS (función completa):
def _draw_volume(ax, df: pd.DataFrame, dates_num, body_w: float) -> None:
    """
    Dibuja barras de volumen con Rectangle (mismo ancho que las velas)
    y una EMA20 de volumen como línea de referencia.
    """
    vol_ema = df["volume"].ewm(span=20, adjust=False).mean()

    for dt_num, row, ema_v in zip(dates_num, df.itertuples(), vol_ema):
        color = COLOR_UP if row.close >= row.open else COLOR_DOWN
        rect  = mpatches.Rectangle(
            (dt_num - body_w / 2, 0), body_w, row.volume,
            facecolor=color, edgecolor="none", alpha=0.75, zorder=2,
        )
        ax.add_patch(rect)

    ax.plot(df.index, vol_ema,
            color=COLOR_TEXT_SECONDARY, linewidth=0.8, zorder=3)
    ax.set_ylim(0, df["volume"].max() * 1.35)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda x, _: f"{x/1e9:.1f}B" if x >= 1e9 else f"{x/1e6:.0f}M"
        )
    )
```

---

### Cambio 1.6 — Actualizar `_setup_axes()`: eje Y a la derecha

```python
# ANTES (función completa):
def _setup_axes(ax, df, ylabel: str = "Price"):
    """Setup common axis properties with TradingView style."""
    ax.set_facecolor(COLOR_BG)
    ax.tick_params(colors=COLOR_TEXT, labelsize=10)
    ax.spines["bottom"].set_color(COLOR_GRID)
    ax.spines["top"].set_color("none")  # Hide top spine
    ax.spines["left"].set_color(COLOR_GRID)
    ax.spines["right"].set_color("none")  # Hide right spine
    ax.xaxis.label.set_color(COLOR_TEXT)
    ax.yaxis.label.set_color(COLOR_TEXT)
    ax.grid(True, color=COLOR_GRID, alpha=0.15, linewidth=0.8)  # Subtler grid
    ax.set_ylabel(ylabel, color=COLOR_TEXT, fontsize=10)


# DESPUÉS (función completa):
def _setup_axes(ax, ylabel: str = "", hide_xlabels: bool = True) -> None:
    """
    Aplica estilo TradingView oscuro. Eje Y a la derecha.
    hide_xlabels=True oculta etiquetas X en paneles superiores.
    """
    ax.set_facecolor(COLOR_BG)
    for spine in ax.spines.values():
        spine.set_color(COLOR_GRID)
        spine.set_linewidth(0.6)
    ax.tick_params(colors=COLOR_TEXT, labelsize=8.5, length=3)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.set_ylabel(ylabel, color=COLOR_TEXT_SECONDARY, fontsize=8, labelpad=6)
    ax.grid(True, color=COLOR_GRID, alpha=0.35, linewidth=0.5, linestyle="-")
    if hide_xlabels:
        plt.setp(ax.get_xticklabels(), visible=False)
        ax.tick_params(axis="x", length=0)
```

---

### Cambio 1.7 — Reescribir el cuerpo de `generate_ohlcv_chart()`

Cambiar solo el `default` del parámetro `candles` en la firma, y reemplazar
todo el cuerpo `try/except`:

**Firma — cambiar `candles: int = 20` por `candles: int = 80`:**

```python
def generate_ohlcv_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    show_ema: bool = False,
    show_bb: bool = False,
    show_rsi: bool = False,
    show_pivots: bool = False,
    candles: int = 80,          # ← era 20
    signal: str = "NEUTRAL",
    signal_emoji: str = "⚖️",
    pivot: float = 0,
    r1: float = 0,
    s1: float = 0,
) -> io.BytesIO | None:
```

**Reemplazar todo el cuerpo `try/except` por:**

```python
    try:
        if df is None or df.empty:
            logger.warning("Chart generator: empty DataFrame")
            return None

        df = df.copy()

        # Normalizar índice a datetime
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Calcular indicadores ANTES del tail() para warm-up correcto
        if show_ema:
            df = _calculate_ema(df)
        if show_bb:
            df = _calculate_bollinger_bands(df)

        # RSI siempre calculado (panel inferior fijo)
        delta = df["close"].diff()
        gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss  = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
        df["rsi"] = (100 - 100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)

        # Recortar al número de velas a mostrar
        df = df.tail(candles)

        # Ancho de vela dinámico inferido del índice
        body_w     = _infer_candle_width(df)
        candle_gap = body_w / 0.65
        dates_num  = mdates.date2num(df.index.to_pydatetime())

        # ── Figura: 3 paneles fijos (precio / volumen / RSI) ─────────────────
        fig = plt.figure(figsize=(14, 9), facecolor=COLOR_BG)
        gs  = fig.add_gridspec(
            3, 1,
            height_ratios=[6.5, 1.5, 1.5],
            hspace=0.0,
            left=0.04, right=0.95, top=0.91, bottom=0.07,
        )
        ax_price  = fig.add_subplot(gs[0])
        ax_volume = fig.add_subplot(gs[1], sharex=ax_price)
        ax_rsi    = fig.add_subplot(gs[2], sharex=ax_price)

        _setup_axes(ax_price,  ylabel="",    hide_xlabels=True)
        _setup_axes(ax_volume, ylabel="Vol", hide_xlabels=True)
        _setup_axes(ax_rsi,    ylabel="RSI", hide_xlabels=False)

        # ── Panel de precio ───────────────────────────────────────────────────
        _draw_candlestick(ax_price, df, dates_num, body_w)

        if show_ema:
            _draw_ema(ax_price, df)
        if show_bb:
            _draw_bollinger_bands(ax_price, df)
        if show_pivots:
            _draw_pivots(ax_price, df, pivot, r1, s1)

        # Precio actual — línea horizontal punteada + label
        last_price = float(df["close"].iloc[-1])
        ax_price.axhline(
            last_price,
            color=COLOR_TEXT_SECONDARY, linewidth=0.7,
            linestyle="--", alpha=0.6, zorder=1,
        )
        ax_price.text(
            dates_num[-1] + candle_gap * 0.6, last_price,
            f" {last_price:,.2f}",
            color=COLOR_TEXT, fontsize=8, va="center", zorder=10,
        )

        # Watermark — directamente sobre ax_price, SIN add_subplot(111)
        ax_price.text(
            0.5, 0.5, "SipSignal",
            transform=ax_price.transAxes,
            fontsize=52, fontweight="bold",
            color=COLOR_WATERMARK, alpha=0.18,
            ha="center", va="center", zorder=1,
        )

        # ── Panel de volumen ──────────────────────────────────────────────────
        _draw_volume(ax_volume, df, dates_num, body_w)

        # ── Panel RSI ─────────────────────────────────────────────────────────
        ax_rsi.plot(df.index, df["rsi"],
                    color=COLOR_RSI, linewidth=1.1, zorder=3)
        ax_rsi.axhline(70, color=COLOR_RSI_OVERBOUGHT,
                        linewidth=0.7, linestyle="--", alpha=0.6)
        ax_rsi.axhline(30, color=COLOR_RSI_OVERSOLD,
                        linewidth=0.7, linestyle="--", alpha=0.6)
        ax_rsi.axhline(50, color=COLOR_GRID,
                        linewidth=0.5, linestyle="-", alpha=0.4)
        ax_rsi.fill_between(
            df.index, df["rsi"], 70,
            where=(df["rsi"] >= 70),
            color=COLOR_RSI_OVERBOUGHT, alpha=0.12, zorder=2,
        )
        ax_rsi.fill_between(
            df.index, df["rsi"], 30,
            where=(df["rsi"] <= 30),
            color=COLOR_RSI_OVERSOLD, alpha=0.12, zorder=2,
        )
        ax_rsi.set_ylim(10, 90)
        rsi_now = float(df["rsi"].iloc[-1])
        ax_rsi.text(
            df.index[-1], rsi_now, f"  {rsi_now:.1f}",
            color=COLOR_RSI, fontsize=7.5, va="center", zorder=10,
        )

        # ── Eje X — solo en panel RSI ─────────────────────────────────────────
        ax_rsi.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_rsi.tick_params(axis="x", colors=COLOR_TEXT_SECONDARY,
                            labelsize=8, rotation=0)

        # ── Límites X con padding ─────────────────────────────────────────────
        pad = candle_gap * 2
        ax_price.set_xlim(dates_num[0] - pad, dates_num[-1] + pad * 3)

        # ── Header estilo TradingView ─────────────────────────────────────────
        last_open = float(df["open"].iloc[-1])
        chg_pct   = (last_price - last_open) / last_open * 100 if last_open > 0 else 0
        chg_str   = f"+{chg_pct:.2f}%" if chg_pct >= 0 else f"{chg_pct:.2f}%"
        chg_color = COLOR_UP if chg_pct >= 0 else COLOR_DOWN

        fig.text(0.04, 0.955, symbol,
                 fontsize=13, fontweight="bold", color=COLOR_TITLE, va="bottom")
        fig.text(0.04 + len(symbol) * 0.012, 0.955, f"  {timeframe.upper()}",
                 fontsize=10, color=COLOR_TEXT_SECONDARY, va="bottom")
        fig.text(0.50, 0.955, f"{last_price:,.2f}",
                 fontsize=13, fontweight="bold", color=COLOR_TITLE,
                 va="bottom", ha="center")
        fig.text(0.60, 0.955, chg_str,
                 fontsize=10, color=chg_color, va="bottom")
        fig.text(0.95, 0.005, "sipsignal.io",
                 fontsize=8, color=COLOR_TEXT_SECONDARY,
                 alpha=0.6, ha="right", va="bottom")

        # ── Guardar ───────────────────────────────────────────────────────────
        buf = io.BytesIO()
        plt.savefig(
            buf, format="png", facecolor=COLOR_BG,
            dpi=130, bbox_inches="tight", pad_inches=0.15,
        )
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error(f"Chart generator error: {e}")
        plt.close("all")
        return None
```

---

## Archivo 2: `bot/trading/chart_capture.py`

### Cambio 2.1 — `limit=100` → `limit=200`

```python
# ANTES (en _capture_with_matplotlib):
df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)

# DESPUÉS:
df = await self.data_fetcher.get_ohlcv(symbol, timeframe, limit=200)
```

---

### Cambio 2.2 — `candles=20` → dinámico por timeframe

**Agregar** la constante al nivel de módulo, debajo de `CACHE_TTL = 300`:

```python
# Velas a mostrar según timeframe
_CANDLES_BY_TF: dict[str, int] = {
    "1m": 120, "5m": 120, "15m": 96, "30m": 96,
    "1h": 120, "4h": 80,  "1d":  60,
}
```

**Cambiar** en `_generate_candlestick_chart`:

```python
# ANTES:
buf = generate_ohlcv_chart(
    df=df,
    symbol=symbol,
    timeframe=timeframe,
    show_ema=show_ema,
    show_bb=show_bb,
    show_rsi=show_rsi,
    show_pivots=show_pivots,
    candles=20,
)

# DESPUÉS:
n_candles = _CANDLES_BY_TF.get(timeframe, 80)
buf = generate_ohlcv_chart(
    df=df,
    symbol=symbol,
    timeframe=timeframe,
    show_ema=show_ema,
    show_bb=show_bb,
    show_rsi=show_rsi,
    show_pivots=show_pivots,
    candles=n_candles,
)
```

---

## Verificación en VPS

```bash
cd ~/sipsignal

python - <<'EOF'
import asyncio, sys
sys.path.insert(0, '.')

async def test():
    from bot.infrastructure.binance.binance_adapter import BinanceAdapter
    from bot.utils.chart_generator import generate_ohlcv_chart

    adapter = BinanceAdapter()
    df = await adapter.get_ohlcv("BTCUSDT", "4h", limit=200)
    await adapter.close()

    buf = generate_ohlcv_chart(df, "BTCUSDT", "4h",
                               show_ema=True, show_rsi=True, candles=80)
    if buf:
        with open("/tmp/test_chart.png", "wb") as f:
            f.write(buf.read())
        print("✅ OK → /tmp/test_chart.png")
    else:
        print("❌ Error")

asyncio.run(test())
EOF

sudo systemctl restart sipsignal
```

---

## Tabla resumen

| # | Archivo | Cambio exacto | Bug |
|---|---------|---------------|-----|
| 1.1 | `chart_generator.py` | Agregar `import mpatches`, `import numpy as np` | prereq |
| 1.2 | `chart_generator.py` | `COLOR_UP/DOWN` corregidos + constante `_TF_HOURS` | visual |
| 1.3 | `chart_generator.py` | Nueva función `_infer_candle_width()` | Bug 2 |
| 1.4 | `chart_generator.py` | Reescribir `_draw_candlestick()` con `Rectangle` | Bug 1 |
| 1.5 | `chart_generator.py` | Reescribir `_draw_volume()` con `Rectangle` + EMA vol | Bug 1 |
| 1.6 | `chart_generator.py` | Actualizar `_setup_axes()`: eje Y derecho, estilo TV | visual |
| 1.7 | `chart_generator.py` | Reescribir `generate_ohlcv_chart()`: layout, header, savefig | Bugs 2,3,5 |
| 2.1 | `chart_capture.py` | `limit=100` → `limit=200` | Bug 4 |
| 2.2 | `chart_capture.py` | `candles=20` → dinámico + constante `_CANDLES_BY_TF` | Bug 4 |
