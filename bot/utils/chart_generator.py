"""
Chart generator with optional technical indicators.

Generates candlestick charts with toggleable indicators (EMA, Bollinger Bands, RSI, Pivots).
All indicators are disabled by default for clean price action visualization.
"""

import io

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from bot.utils.logger import logger

matplotlib.use("Agg")

# Color scheme - TradingView Pro Style (dark theme)
# Background and base
COLOR_BG = "#131722"  # Very dark blue (TradingView style)
COLOR_BG_SECONDARY = "#1E222D"  # For panels
COLOR_GRID = "#2A2E39"  # Subtle grid lines

# Candlesticks
COLOR_UP = "#089981"  # TradingView classic green
COLOR_DOWN = "#F23645"  # Vibrant red

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


def _draw_volume(ax, df, dates):
    """Draw volume bars."""
    volumes = df["volume"].values
    colors = [
        COLOR_UP if df["close"].iloc[i] >= df["open"].iloc[i] else COLOR_DOWN
        for i in range(len(df))
    ]

    for i, (date, vol) in enumerate(zip(dates, volumes, strict=False)):
        ax.bar(date, vol, width=0.6, color=colors[i], alpha=0.7)


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


def generate_ohlcv_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    show_ema: bool = False,
    show_bb: bool = False,
    show_rsi: bool = False,
    show_pivots: bool = False,
    candles: int = 20,
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
        candles: Number of candles to display (default: 20)
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

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)

        df = df.tail(candles)

        if show_ema:
            df = _calculate_ema(df)

        if show_bb:
            df = _calculate_bollinger_bands(df)

        if show_rsi:
            df = _calculate_rsi(df)

        dates = mdates.date2num(df.index.to_pydatetime())

        # Improved layout: 70% price, 15% volume, 15% RSI
        if show_rsi:
            fig = plt.figure(figsize=(14, 10), facecolor=COLOR_BG, edgecolor=COLOR_BG)
            gs = fig.add_gridspec(3, 1, height_ratios=[7, 1.5, 1.5], hspace=0.08)
            ax_price = fig.add_subplot(gs[0])
            ax_volume = fig.add_subplot(gs[1], sharex=ax_price)
            ax_rsi = fig.add_subplot(gs[2], sharex=ax_price)
        else:
            fig = plt.figure(figsize=(14, 8), facecolor=COLOR_BG, edgecolor=COLOR_BG)
            gs = fig.add_gridspec(2, 1, height_ratios=[7, 2], hspace=0.08)
            ax_price = fig.add_subplot(gs[0])
            ax_volume = fig.add_subplot(gs[1], sharex=ax_price)
            ax_rsi = None

        _setup_axes(ax_price, df)
        _setup_axes(ax_volume, df, ylabel="Volume")

        _draw_candlestick(ax_price, df, dates)
        _draw_volume(ax_volume, df, dates)

        if show_ema:
            _draw_ema(ax_price, df)

        if show_bb:
            _draw_bollinger_bands(ax_price, df)

        if show_pivots:
            _draw_pivots(ax_price, df, pivot, r1, s1)

        # Branding: Watermark in center (behind candles)
        ax_watermark = fig.add_subplot(111, facecolor="none")
        ax_watermark.text(
            0.5,
            0.5,
            "SipSignal",
            transform=ax_watermark.transAxes,
            fontsize=48,
            fontweight="bold",
            color=COLOR_WATERMARK,
            alpha=0.10,
            ha="center",
            va="center",
            rotation=0,
            zorder=0,
        )
        ax_watermark.axis("off")

        # Branding: Logo + name in top-left corner
        ax_price.text(
            0.02,
            0.98,
            "🟡 SipSignal",
            transform=ax_price.transAxes,
            fontsize=11,
            fontweight="bold",
            color=COLOR_TITLE,
            alpha=0.9,
            ha="left",
            va="top",
            zorder=10,
        )

        # Branding: Website in bottom-right corner
        fig.text(
            0.98,
            0.02,
            "sipsignal.io",
            fontsize=9,
            color=COLOR_WEBSITE,
            alpha=0.7,
            ha="right",
            va="bottom",
        )

        if ax_rsi is not None and show_rsi and "rsi" in df.columns:
            _setup_axes(ax_rsi, df, ylabel="RSI")
            ax_rsi.plot(df.index, df["rsi"], color=COLOR_RSI, linewidth=1.5)
            ax_rsi.axhline(
                y=70, color=COLOR_RSI_OVERBOUGHT, linewidth=0.8, linestyle="--", alpha=0.7
            )
            ax_rsi.axhline(y=30, color=COLOR_RSI_OVERSOLD, linewidth=0.8, linestyle="--", alpha=0.7)
            ax_rsi.fill_between(df.index, 30, 70, alpha=0.1, color=COLOR_RSI)
            ax_rsi.set_ylim(0, 100)

        ax_price.set_xlabel("")
        ax_volume.set_xlabel("")

        # Show fewer date labels (every 3-4 candles)
        ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax_volume.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax_price.tick_params(axis="x", rotation=45)
        ax_volume.tick_params(axis="x", rotation=45)

        if ax_rsi is not None:
            ax_rsi.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
            ax_rsi.tick_params(axis="x", rotation=45)
            ax_rsi.set_xlabel("Date", color=COLOR_TEXT)

        # Title with TradingView style
        title = f"{symbol} | {timeframe.upper()} | {signal_emoji} {signal}"
        ax_price.set_title(title, color=COLOR_TITLE, fontsize=11, pad=8, fontweight="bold")

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor=COLOR_BG, dpi=100)
        plt.close(fig)
        buf.seek(0)

        return buf

    except Exception as e:
        logger.error(f"Chart generator error: {e}")
        return None
