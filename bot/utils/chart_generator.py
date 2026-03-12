"""
Chart generator with optional technical indicators.

Generates candlestick charts with toggleable indicators (EMA, Bollinger Bands, RSI, Pivots).
All indicators are disabled by default for clean price action visualization.
"""

import io

import matplotlib
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bot.utils.logger import logger

matplotlib.use("Agg")

# Color scheme - TradingView Pro Style (dark theme)
# Background and base
COLOR_BG = "#131722"  # Very dark blue (TradingView style)
COLOR_BG_SECONDARY = "#1E222D"  # For panels
COLOR_GRID = "#2A2E39"  # Subtle grid lines

# Candlesticks
COLOR_UP = "#26A69A"  # TradingView classic green
COLOR_DOWN = "#EF5350"  # Vibrant red

# Indicators
COLOR_EMA20 = "#2962FF"  # Bright blue
COLOR_EMA50 = "#FF6D00"  # Orange
COLOR_EMA200 = "#9C27B0"  # Purple
COLOR_BB_UPPER = "#2962FF"
COLOR_BB_LOWER = "#2962FF"
COLOR_BB_FILL = "#2962FF"  # Blue with low opacity

# RSI
COLOR_RSI = "#FF9800"  # Golden orange
COLOR_RSI_OVERBOUGHT = "#ef5350"
COLOR_RSI_OVERSOLD = "#26a69a"

# Pivots
COLOR_PIVOT = "#FFEB3B"  # Yellow
COLOR_R = "#4CAF50"  # Green (resistance)
COLOR_S = "#F44336"  # Red (support)

# Text
COLOR_TEXT = "#D1D4DC"  # Light gray (primary)
COLOR_TEXT_SECONDARY = "#787B86"  # Medium gray (secondary)
COLOR_TITLE = "#FFFFFF"  # Pure white

# Branding
COLOR_BRAND = "#2962FF"  # Professional blue
COLOR_WATERMARK = "#787B86"  # Medium gray
COLOR_WEBSITE = "#787B86"  # Subtle gray

# Timeframe → horas (para calcular ancho de vela dinámico)
_TF_HOURS: dict[str, float] = {
    "1m": 1 / 60,
    "3m": 3 / 60,
    "5m": 5 / 60,
    "15m": 0.25,
    "30m": 0.5,
    "1h": 1,
    "2h": 2,
    "4h": 4,
    "6h": 6,
    "8h": 8,
    "12h": 12,
    "1d": 24,
    "3d": 72,
    "1w": 168,
}


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


def _calculate_ema(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate EMA 20, 50, and 200."""
    df = df.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    return df


def _calculate_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Bollinger Bands (20, 2)."""
    df = df.copy()
    df["bb_middle"] = df["close"].rolling(window=20).mean()
    bb_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
    df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
    return df


def _calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    """Calculate RSI."""
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df


def _draw_candlestick(ax, df: pd.DataFrame, dates_num, body_w: float) -> None:
    """
    Dibuja velas japonesas con cuerpo relleno (Rectangle) y mecha (plot).
    body_w: ancho del cuerpo en unidades mdates (días). Ver _infer_candle_width().
    """
    for dt_num, row in zip(dates_num, df.itertuples(), strict=False):
        o, h, low_price, c = row.open, row.high, row.low, row.close
        color = COLOR_UP if c >= o else COLOR_DOWN
        body_bot = min(o, c)
        # Doji: cuerpo mínimo visible (0.5% del rango de la vela)
        body_h = abs(c - o) if abs(c - o) > 1e-8 else (h - low_price) * 0.005

        # Mecha (wick)
        ax.plot([dt_num, dt_num], [low_price, h], color=color, linewidth=0.85, zorder=2)
        # Cuerpo relleno
        rect = mpatches.Rectangle(
            (dt_num - body_w / 2, body_bot),
            width=body_w,
            height=body_h,
            facecolor=color,
            edgecolor=color,
            linewidth=0,
            zorder=3,
        )
        ax.add_patch(rect)


def _draw_volume(ax, df: pd.DataFrame, dates_num, body_w: float) -> None:
    """
    Dibuja barras de volumen con Rectangle (mismo ancho que las velas)
    y una EMA20 de volumen como línea de referencia.
    """
    vol_ema = df["volume"].ewm(span=20, adjust=False).mean()

    for dt_num, row, _ema_v in zip(dates_num, df.itertuples(), vol_ema, strict=False):
        color = COLOR_UP if row.close >= row.open else COLOR_DOWN
        rect = mpatches.Rectangle(
            (dt_num - body_w / 2, 0),
            body_w,
            row.volume,
            facecolor=color,
            edgecolor="none",
            alpha=0.75,
            zorder=2,
        )
        ax.add_patch(rect)

    ax.plot(df.index, vol_ema, color=COLOR_TEXT_SECONDARY, linewidth=0.8, zorder=3)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x / 1e9:.1f}B" if x >= 1e9 else f"{x / 1e6:.0f}M")
    )


def _draw_ema(ax, df):
    """Draw EMA lines."""
    if "ema20" in df.columns:
        ax.plot(df.index, df["ema20"], color=COLOR_EMA20, linewidth=1.2, label="EMA20")
    if "ema50" in df.columns:
        ax.plot(df.index, df["ema50"], color=COLOR_EMA50, linewidth=1.2, label="EMA50")
    if "ema200" in df.columns:
        ax.plot(df.index, df["ema200"], color=COLOR_EMA200, linewidth=1.2, label="EMA200")


def _draw_bollinger_bands(ax, df):
    """Draw Bollinger Bands."""
    if "bb_upper" in df.columns and "bb_lower" in df.columns:
        ax.fill_between(
            df.index,
            df["bb_upper"],
            df["bb_lower"],
            color=COLOR_BB_FILL,
            alpha=0.1,
        )
        ax.plot(df.index, df["bb_upper"], color=COLOR_BB_UPPER, linewidth=1, linestyle="--")
        ax.plot(df.index, df["bb_lower"], color=COLOR_BB_LOWER, linewidth=1, linestyle="--")


def _draw_pivots(ax, df, pivot: float, r1: float, s1: float):
    """Draw pivot lines."""
    if pivot > 0:
        ax.axhline(y=pivot, color=COLOR_PIVOT, linewidth=1, linestyle="-.", label="Pivot")
    if r1 > 0:
        ax.axhline(y=r1, color=COLOR_R, linewidth=1, linestyle="--", label="R1")
    if s1 > 0:
        ax.axhline(y=s1, color=COLOR_S, linewidth=1, linestyle="--", label="S1")


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


def generate_ohlcv_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    show_ema: bool = False,
    show_bb: bool = False,
    show_rsi: bool = False,
    show_pivots: bool = False,
    candles: int = 80,  # ← era 20
    signal: str = "NEUTRAL",
    signal_emoji: str = "⚖️",
    pivot: float = 0,
    r1: float = 0,
    s1: float = 0,
) -> io.BytesIO | None:
    """
    Generate OHLCV chart with optional technical indicators.

    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        timeframe: Timeframe string (e.g., "4h", "1d")
        show_ema: Show EMA 20/50/200 lines (default: False)
        show_bb: Show Bollinger Bands (default: False)
        show_rsi: Show RSI panel (default: False)
        show_pivots: Show pivot lines (default: False)
        candles: Number of candles to display (default: 80)
        signal: Signal text for title (default: "NEUTRAL")
        signal_emoji: Signal emoji for title (default: "⚖️")
        pivot: Pivot level price (default: 0, not shown)
        r1: Resistance 1 level (default: 0, not shown)
        s1: Support 1 level (default: 0, not shown)

    Returns:
        BytesIO buffer with PNG image or None on error
    """
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
        gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
        df["rsi"] = (100 - 100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)

        # Recortar al número de velas a mostrar
        df = df.tail(candles)

        # Ancho de vela dinámico inferido del índice
        body_w = _infer_candle_width(df)
        candle_gap = body_w / 0.65
        dates_num = mdates.date2num(df.index.to_pydatetime())

        # ── Figura: 3 paneles fijos (precio / volumen / RSI) ─────────────────
        fig = plt.figure(figsize=(14, 9), facecolor=COLOR_BG)
        gs = fig.add_gridspec(
            3,
            1,
            height_ratios=[6.5, 1.5, 1.5],
            hspace=0.0,
            left=0.04,
            right=0.95,
            top=0.91,
            bottom=0.07,
        )
        ax_price = fig.add_subplot(gs[0])
        ax_volume = fig.add_subplot(gs[1], sharex=ax_price)
        ax_rsi = fig.add_subplot(gs[2], sharex=ax_price)

        _setup_axes(ax_price, ylabel="", hide_xlabels=True)
        _setup_axes(ax_volume, ylabel="Vol", hide_xlabels=True)
        _setup_axes(ax_rsi, ylabel="RSI", hide_xlabels=False)

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
            color=COLOR_TEXT_SECONDARY,
            linewidth=0.7,
            linestyle="--",
            alpha=0.6,
            zorder=1,
        )
        ax_price.text(
            dates_num[-1] + candle_gap * 0.6,
            last_price,
            f" {last_price:,.2f}",
            color=COLOR_TEXT,
            fontsize=8,
            va="center",
            zorder=10,
        )

        # Watermark — directamente sobre ax_price, SIN add_subplot(111)
        ax_price.text(
            0.5,
            0.5,
            "SipSignal",
            transform=ax_price.transAxes,
            fontsize=52,
            fontweight="bold",
            color=COLOR_WATERMARK,
            alpha=0.18,
            ha="center",
            va="center",
            zorder=1,
        )

        # ── Panel de volumen ──────────────────────────────────────────────────
        _draw_volume(ax_volume, df, dates_num, body_w)

        # ── Panel RSI ─────────────────────────────────────────────────────────
        ax_rsi.plot(df.index, df["rsi"], color=COLOR_RSI, linewidth=1.1, zorder=3)
        ax_rsi.axhline(70, color=COLOR_RSI_OVERBOUGHT, linewidth=0.7, linestyle="--", alpha=0.6)
        ax_rsi.axhline(30, color=COLOR_RSI_OVERSOLD, linewidth=0.7, linestyle="--", alpha=0.6)
        ax_rsi.axhline(50, color=COLOR_GRID, linewidth=0.5, linestyle="-", alpha=0.4)
        ax_rsi.fill_between(
            df.index,
            df["rsi"],
            70,
            where=(df["rsi"] >= 70),
            color=COLOR_RSI_OVERBOUGHT,
            alpha=0.12,
            zorder=2,
        )
        ax_rsi.fill_between(
            df.index,
            df["rsi"],
            30,
            where=(df["rsi"] <= 30),
            color=COLOR_RSI_OVERSOLD,
            alpha=0.12,
            zorder=2,
        )
        ax_rsi.set_ylim(10, 90)
        rsi_now = float(df["rsi"].iloc[-1])
        ax_rsi.text(
            df.index[-1],
            rsi_now,
            f"  {rsi_now:.1f}",
            color=COLOR_RSI,
            fontsize=7.5,
            va="center",
            zorder=10,
        )

        # ── Eje X — solo en panel RSI ─────────────────────────────────────────
        ax_rsi.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_rsi.tick_params(axis="x", colors=COLOR_TEXT_SECONDARY, labelsize=8, rotation=0)

        # ── Límites X con padding ─────────────────────────────────────────────
        pad = candle_gap * 2
        ax_price.set_xlim(dates_num[0] - pad, dates_num[-1] + pad * 3)

        # ── Header estilo TradingView ─────────────────────────────────────────
        last_open = float(df["open"].iloc[-1])
        chg_pct = (last_price - last_open) / last_open * 100 if last_open > 0 else 0
        chg_str = f"+{chg_pct:.2f}%" if chg_pct >= 0 else f"{chg_pct:.2f}%"
        chg_color = COLOR_UP if chg_pct >= 0 else COLOR_DOWN

        fig.text(
            0.04, 0.955, symbol, fontsize=13, fontweight="bold", color=COLOR_TITLE, va="bottom"
        )
        fig.text(
            0.04 + len(symbol) * 0.012,
            0.955,
            f"  {timeframe.upper()}",
            fontsize=10,
            color=COLOR_TEXT_SECONDARY,
            va="bottom",
        )
        fig.text(
            0.50,
            0.955,
            f"{last_price:,.2f}",
            fontsize=13,
            fontweight="bold",
            color=COLOR_TITLE,
            va="bottom",
            ha="center",
        )
        fig.text(0.60, 0.955, chg_str, fontsize=10, color=chg_color, va="bottom")
        fig.text(
            0.95,
            0.005,
            "sipsignal.io",
            fontsize=8,
            color=COLOR_TEXT_SECONDARY,
            alpha=0.6,
            ha="right",
            va="bottom",
        )

        # ── Guardar ───────────────────────────────────────────────────────────
        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            facecolor=COLOR_BG,
            dpi=130,
            bbox_inches="tight",
            pad_inches=0.15,
        )
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error(f"Chart generator error: {e}")
        plt.close("all")
        return None
