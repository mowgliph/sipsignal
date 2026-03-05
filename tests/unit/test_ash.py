import numpy as np
import pandas as pd
import pytest
from trading.technical_analysis import calculate_ash


def _create_sample_df(n_candles: int = 200, start_price: float = 100.0) -> pd.DataFrame:
    np.random.seed(42)
    returns = np.random.randn(n_candles) * 0.02
    prices = start_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'close': prices,
        'open': prices * (1 + np.random.randn(n_candles) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(n_candles) * 0.01)),
        'low': prices * (1 - np.abs(np.random.randn(n_candles) * 0.01)),
        'volume': np.random.randint(1000, 10000, n_candles)
    })
    
    return df


def test_ash_signal_is_transition():
    df = _create_sample_df(50)
    
    df = calculate_ash(df, length=5, smooth=2)
    
    bullish_signals = df[df['ash_bullish_signal'] == True].index.tolist()
    
    for idx in bullish_signals:
        assert df.loc[idx, 'ash_bullish'] == True
        
        if idx > 0:
            assert df.loc[idx - 1, 'ash_bullish'] == False or df.loc[idx - 1, 'ash_neutral'] == True
    
    bearish_signals = df[df['ash_bearish_signal'] == True].index.tolist()
    
    for idx in bearish_signals:
        assert df.loc[idx, 'ash_bearish'] == True
        
        if idx > 0:
            assert df.loc[idx - 1, 'ash_bearish'] == False or df.loc[idx - 1, 'ash_neutral'] == True


def test_ash_neutral_when_balanced():
    df = pd.DataFrame({
        'close': [100, 101, 100, 101, 100, 101, 100, 101, 100, 101,
                  100, 101, 100, 101, 100, 101, 100, 101, 100, 101]
    })
    
    df = calculate_ash(df, length=3, smooth=2, ma_type='SMA')
    
    assert 'ash_neutral' in df.columns
    assert 'ash_bullish' in df.columns
    assert 'ash_bearish' in df.columns
    
    assert df['ash_neutral'].dtype == bool
    assert df['ash_bullish'].dtype == bool
    assert df['ash_bearish'].dtype == bool
    
    states = df[['ash_bullish', 'ash_bearish', 'ash_neutral']].sum(axis=1)
    assert (states == 1).all(), "Cada barra debe tener exactamente un estado"


def test_ash_no_crash_200_candles():
    df = _create_sample_df(200)
    
    result = calculate_ash(df, length=14, smooth=4)
    
    expected_cols = [
        'ash_smth_bulls', 'ash_smth_bears', 'ash_difference',
        'ash_bullish', 'ash_bearish', 'ash_neutral',
        'ash_bullish_signal', 'ash_bearish_signal'
    ]
    
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
    
    assert len(result) == 200
    
    assert result['ash_smth_bulls'].notna().sum() > 0
    assert result['ash_smth_bears'].notna().sum() > 0


def test_ash_default_parameters():
    df = _create_sample_df(50)
    
    result = calculate_ash(df)
    
    assert 'ash_bullish_signal' in result.columns
    assert 'ash_bearish_signal' in result.columns
    
    assert result['ash_bullish_signal'].dtype == bool
    assert result['ash_bearish_signal'].dtype == bool
