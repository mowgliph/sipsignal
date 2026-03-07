"""
Supertrend, ASH, ATR — port desde Pine Script.
"""

import numpy as np
import pandas as pd
import pandas_ta


def _alma(s: pd.Series, length: int, offset: float = 0.85, sigma: float = 6) -> pd.Series:
    """
    Arnaud Legoux Moving Average — fórmula gaussiana.
    """
    if length <= 0:
        return s

    m = offset * (length - 1)
    s_range = np.arange(length)
    gauss_weights = np.exp(-((s_range - m) ** 2) / (2 * sigma**2))
    gauss_weights = gauss_weights / gauss_weights.sum()

    result = s.rolling(window=length, min_periods=length).apply(
        lambda x: np.convolve(x, gauss_weights, mode="valid").sum() if len(x) >= length else np.nan,
        raw=False,
    )

    half_window = length // 2
    for i in range(length - 1):
        if i < len(result):
            result.iloc[i] = s.iloc[: i + 1].mean()

    return result


def _ma(s: pd.Series, length: int, ma_type: str = "EMA", **kw) -> pd.Series:
    """
    Polimórfica: EMA, SMA, WMA, SMMA, HMA, ALMA.
    (Traducción de la función ma() del Pine Script MSATR Strategy del proyecto)
    """
    ma_type = ma_type.upper()

    if length <= 0:
        return s

    if ma_type == "EMA":
        return s.ewm(span=length, adjust=False, min_periods=length).mean()

    elif ma_type == "SMA":
        return s.rolling(window=length, min_periods=length).mean()

    elif ma_type == "WMA":
        weights = np.arange(1, length + 1)
        return s.rolling(window=length, min_periods=length).apply(
            lambda x: np.sum(weights * x) / weights.sum() if len(x) == length else np.nan, raw=True
        )

    elif ma_type == "SMMA":
        return s.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    elif ma_type == "HMA":
        half_length = length // 2
        sqrt_length = int(np.sqrt(length))
        wma1 = _ma(s, half_length, "WMA")
        wma2 = _ma(wma1, sqrt_length, "WMA")
        return 2 * wma2 - _ma(wma2, sqrt_length, "WMA")

    elif ma_type == "ALMA":
        offset = kw.get("offset", 0.85)
        sigma = kw.get("sigma", 6)
        return _alma(s, length, offset, sigma)

    else:
        raise ValueError(f"Unknown ma_type: {ma_type}. Supported: EMA, SMA, WMA, SMMA, HMA, ALMA")


def calculate_supertrend(
    df: pd.DataFrame, period: int = 14, multiplier: float = 1.8
) -> pd.DataFrame:
    """
    Calcula Supertrend y añade columnas al DataFrame.

    Columnas añadidas:
    - sup_is_bullish: True cuando SUPERTd == -1 (pandas-ta: -1 = alcista)
    - sup_cross_bullish: True SOLO en el 1er bar del cruce alcista
    - sup_cross_bearish: True SOLO en el 1er bar del cruce bajista
    - supertrend_line: valor float de la línea
    """
    df = df.copy()

    df.ta.supertrend(length=period, multiplier=multiplier, append=True)

    supertrend_col = df.columns[df.columns.str.contains("SUPERT", case=False)][0]
    supertrend_d_col = df.columns[df.columns.str.contains("SUPERTd", case=False)][0]

    df["supertrend_line"] = df[supertrend_col]
    df["sup_is_bullish"] = (df[supertrend_d_col] == -1).astype(bool)

    shifted = df["sup_is_bullish"].shift(1).fillna(False).astype(bool)
    df["sup_cross_bullish"] = df["sup_is_bullish"] & ~shifted
    df["sup_cross_bearish"] = ~df["sup_is_bullish"] & shifted

    return df


def calculate_ash(
    df: pd.DataFrame,
    length: int = 14,
    smooth: int = 4,
    src_col: str = "close",
    mode: str = "RSI",
    ma_type: str = "EMA",
    **kw,
) -> pd.DataFrame:
    """
    Absolute Strength Histogram (ASH) — port del Pine Script MSATR Strategy.

    Columnas añadidas:
    - ash_smth_bulls: Media suavizada de bulls
    - ash_smth_bears: Media suavizada de bears
    - ash_difference: Diferencia absoluta entre smth_bulls y smth_bears
    - ash_bullish: True cuando difference > SmthBears pero no > SmthBulls
    - ash_bearish: True cuando difference > SmthBulls pero no > SmthBears
    - ash_neutral: True cuando no es ni bullish ni bearish
    - ash_bullish_signal: True SOLO en el cruce de neutral a bullish
    - ash_bearish_signal: True SOLO en el cruce de neutral a bearish
    """
    df = df.copy()

    price1 = df[src_col]
    price2 = df[src_col].shift(1)
    diff = price1 - price2

    bulls = 0.5 * (diff.abs() + diff)
    bears = 0.5 * (diff.abs() - diff)

    avg_bulls = _ma(bulls, length, ma_type, **kw)
    avg_bears = _ma(bears, length, ma_type, **kw)

    smth_bulls = _ma(avg_bulls, smooth, ma_type, **kw)
    smth_bears = _ma(avg_bears, smooth, ma_type, **kw)

    difference = (smth_bulls - smth_bears).abs()

    ash_bullish = (difference > smth_bears) & ~(difference > smth_bulls)
    ash_bearish = (difference > smth_bulls) & ~(difference > smth_bears)
    ash_neutral = ~ash_bullish & ~ash_bearish

    ash_bullish_signal = ash_bullish & ash_neutral.shift(1).fillna(False)
    ash_bearish_signal = ash_bearish & ash_neutral.shift(1).fillna(False)

    df["ash_smth_bulls"] = smth_bulls
    df["ash_smth_bears"] = smth_bears
    df["ash_difference"] = difference
    df["ash_bullish"] = ash_bullish
    df["ash_bearish"] = ash_bearish
    df["ash_neutral"] = ash_neutral
    df["ash_bullish_signal"] = ash_bullish_signal
    df["ash_bearish_signal"] = ash_bearish_signal

    return df


def calculate_atr_levels(
    df: pd.DataFrame,
    tp_period: int = 14,
    sl_period: int = 14,
    tp_mult: float = 1.5,
    sl_mult: float = 1.5,
) -> pd.DataFrame:
    """
    Calcula niveles de TP/SL basados en ATR con shift de vela anterior (como Pine Script).

    Columnas añadidas:
    - ATRr_{tp_period}: ATR calculado por pandas-ta
    - long_tp: close + ATR[1] * tp_mult
    - long_sl: close - ATR[1] * sl_mult
    - short_tp: close - ATR[1] * tp_mult
    - short_sl: close + ATR[1] * sl_mult
    - rr_ratio: (ATR[1] * tp_mult) / (ATR[1] * sl_mult)

    El shift(1) es CRÍTICO para coincidir con el Pine Script que usa ATR de la vela anterior.
    """
    df = df.copy()

    df.ta.atr(length=tp_period, append=True)
    atr_col = f"ATRr_{tp_period}"

    atr_tp = df[atr_col].shift(1)
    atr_sl = df[f"ATRr_{sl_period}"].shift(1) if sl_period != tp_period else atr_tp

    df["long_tp"] = df["close"] + atr_tp * tp_mult
    df["long_sl"] = df["close"] - atr_sl * sl_mult
    df["short_tp"] = df["close"] - atr_tp * tp_mult
    df["short_sl"] = df["close"] + atr_sl * sl_mult
    df["rr_ratio"] = (atr_tp * tp_mult) / (atr_sl * sl_mult)

    return df


def calculate_all(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Orquestador que calcula Supertrend, ASH y ATR Levels en orden.

    Args:
        df: DataFrame con columnas 'open', 'high', 'low', 'close'
        config: dict con keys:
            - supertrend_period: int (default 14)
            - supertrend_mult: float (default 1.8)
            - ash_length: int (default 14)
            - ash_smooth: int (default 4)
            - tp_period: int (default 14)
            - sl_period: int (default 14)
            - tp_mult: float (default 1.5)
            - sl_mult: float (default 1.5)

    Returns:
        DataFrame con todas las columnas calculadas
    """
    df = df.copy()

    df = calculate_supertrend(
        df,
        period=config.get("supertrend_period", 14),
        multiplier=config.get("supertrend_mult", 1.8),
    )

    df = calculate_ash(df, length=config.get("ash_length", 14), smooth=config.get("ash_smooth", 4))

    df = calculate_atr_levels(
        df,
        tp_period=config.get("tp_period", 14),
        sl_period=config.get("sl_period", 14),
        tp_mult=config.get("tp_mult", 1.5),
        sl_mult=config.get("sl_mult", 1.5),
    )

    return df
