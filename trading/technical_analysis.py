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
    gauss_weights = np.exp(-((s_range - m) ** 2) / (2 * sigma ** 2))
    gauss_weights = gauss_weights / gauss_weights.sum()
    
    result = s.rolling(window=length, min_periods=length).apply(
        lambda x: np.convolve(x, gauss_weights, mode='valid').sum() 
        if len(x) >= length else np.nan,
        raw=False
    )
    
    half_window = length // 2
    for i in range(length - 1):
        if i < len(result):
            result.iloc[i] = s.iloc[:i + 1].mean()
    
    return result


def _ma(s: pd.Series, length: int, ma_type: str = 'EMA', **kw) -> pd.Series:
    """
    Polimórfica: EMA, SMA, WMA, SMMA, HMA, ALMA.
    (Traducción de la función ma() del Pine Script MSATR Strategy del proyecto)
    """
    ma_type = ma_type.upper()
    
    if length <= 0:
        return s
    
    if ma_type == 'EMA':
        return s.ewm(span=length, adjust=False, min_periods=length).mean()
    
    elif ma_type == 'SMA':
        return s.rolling(window=length, min_periods=length).mean()
    
    elif ma_type == 'WMA':
        weights = np.arange(1, length + 1)
        return s.rolling(window=length, min_periods=length).apply(
            lambda x: np.sum(weights * x) / weights.sum() if len(x) == length else np.nan,
            raw=True
        )
    
    elif ma_type == 'SMMA':
        return s.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
    
    elif ma_type == 'HMA':
        half_length = length // 2
        sqrt_length = int(np.sqrt(length))
        wma1 = _ma(s, half_length, 'WMA')
        wma2 = _ma(wma1, sqrt_length, 'WMA')
        return 2 * wma2 - _ma(wma2, sqrt_length, 'WMA')
    
    elif ma_type == 'ALMA':
        offset = kw.get('offset', 0.85)
        sigma = kw.get('sigma', 6)
        return _alma(s, length, offset, sigma)
    
    else:
        raise ValueError(f"Unknown ma_type: {ma_type}. Supported: EMA, SMA, WMA, SMMA, HMA, ALMA")


def calculate_supertrend(df: pd.DataFrame, period: int = 14, multiplier: float = 1.8) -> pd.DataFrame:
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
    
    supertrend_col = df.columns[df.columns.str.contains('SUPERT', case=False)][0]
    supertrend_d_col = df.columns[df.columns.str.contains('SUPERTd', case=False)][0]
    
    df['supertrend_line'] = df[supertrend_col]
    df['sup_is_bullish'] = (df[supertrend_d_col] == -1).astype(bool)
    
    shifted = df['sup_is_bullish'].shift(1).fillna(False).astype(bool)
    df['sup_cross_bullish'] = df['sup_is_bullish'] & ~shifted
    df['sup_cross_bearish'] = ~df['sup_is_bullish'] & shifted
    
    return df
