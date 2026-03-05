import numpy as np
import pandas as pd
import pytest
from trading.technical_analysis import calculate_atr_levels, calculate_all


def _create_test_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 50
    dates = pd.date_range('2024-01-01', periods=n, freq='1h')
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.random.rand(n) * 3
    low = close - np.random.rand(n) * 3
    open_price = low + np.random.rand(n) * (high - low)
    
    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close
    }, index=dates)


class TestCalculateAtrLevels:
    
    def test_rr_ratio_equals_1_when_mult_equal(self):
        df = _create_test_df()
        df = calculate_atr_levels(df, tp_period=14, sl_period=14, tp_mult=1.5, sl_mult=1.5)
        
        valid_rr = df['rr_ratio'].dropna()
        assert len(valid_rr) > 0
        assert np.allclose(valid_rr, 1.0, rtol=1e-9)
    
    def test_long_tp_above_close(self):
        df = _create_test_df()
        df = calculate_atr_levels(df)
        
        valid = df['long_tp'].notna() & df['close'].notna()
        assert (df.loc[valid, 'long_tp'] > df.loc[valid, 'close']).all()
    
    def test_long_sl_below_close(self):
        df = _create_test_df()
        df = calculate_atr_levels(df)
        
        valid = df['long_sl'].notna() & df['close'].notna()
        assert (df.loc[valid, 'long_sl'] < df.loc[valid, 'close']).all()
    
    def test_short_tp_below_close(self):
        df = _create_test_df()
        df = calculate_atr_levels(df)
        
        valid = df['short_tp'].notna() & df['close'].notna()
        assert (df.loc[valid, 'short_tp'] < df.loc[valid, 'close']).all()
    
    def test_short_sl_above_close(self):
        df = _create_test_df()
        df = calculate_atr_levels(df)
        
        valid = df['short_sl'].notna() & df['close'].notna()
        assert (df.loc[valid, 'short_sl'] > df.loc[valid, 'close']).all()
    
    def test_atr_uses_previous_candle(self):
        df = _create_test_df()
        df = calculate_atr_levels(df, tp_period=14, tp_mult=1.5)
        
        atr_col = 'ATRr_14'
        atr_prev = df[atr_col].shift(1)
        
        valid = df['long_tp'].notna() & atr_prev.notna() & df['close'].notna()
        expected_long_tp = df.loc[valid, 'close'] + atr_prev.loc[valid] * 1.5
        assert np.allclose(df.loc[valid, 'long_tp'], expected_long_tp)
    
    def test_rr_ratio_different_when_mult_different(self):
        df = _create_test_df()
        df = calculate_atr_levels(df, tp_mult=2.0, sl_mult=1.0)
        
        valid_rr = df['rr_ratio'].dropna()
        assert len(valid_rr) > 0
        assert (valid_rr > 1.9).all()
    
    def test_columns_exist(self):
        df = _create_test_df()
        df = calculate_atr_levels(df)
        
        expected_cols = ['long_tp', 'long_sl', 'short_tp', 'short_sl', 'rr_ratio']
        for col in expected_cols:
            assert col in df.columns
    
    def test_calculate_all_returns_all_columns(self):
        df = _create_test_df()
        config = {
            'supertrend_period': 14,
            'supertrend_mult': 1.8,
            'ash_length': 14,
            'ash_smooth': 4,
            'tp_period': 14,
            'sl_period': 14,
            'tp_mult': 1.5,
            'sl_mult': 1.5
        }
        df = calculate_all(df, config)
        
        expected_cols = [
            'supertrend_line', 'sup_is_bullish',
            'ash_smth_bulls', 'ash_smth_bears', 'ash_difference',
            'long_tp', 'long_sl', 'short_tp', 'short_sl', 'rr_ratio'
        ]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"
    
    def test_calculate_all_orchestrator_order(self):
        df = _create_test_df()
        config = {'supertrend_period': 14, 'supertrend_mult': 1.8}
        df = calculate_all(df, config)
        
        assert 'sup_is_bullish' in df.columns
        assert 'ash_bullish' in df.columns
        assert 'long_tp' in df.columns
