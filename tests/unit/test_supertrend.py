import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.trading.technical_analysis import _ma, calculate_supertrend


class TestSupertrend:
    @pytest.fixture
    def sample_df(self):
        np.random.seed(42)
        pd.date_range("2024-01-01", periods=200, freq="1h")
        df = pd.DataFrame(
            {
                "High": 100 + np.random.randn(200).cumsum() + 10,
                "Low": 100 + np.random.randn(200).cumsum() - 10,
                "Close": 100 + np.random.randn(200).cumsum(),
                "Open": 100 + np.random.randn(200).cumsum(),
            }
        )
        df["Low"] = df[["Open", "Close"]].min(axis=1) - np.abs(np.random.randn(200))
        df["High"] = df[["Open", "Close"]].max(axis=1) + np.abs(np.random.randn(200))
        return df

    def test_sup_is_bullish_is_bool(self, sample_df):
        result = calculate_supertrend(sample_df)
        assert result["sup_is_bullish"].dtype == bool

    def test_sup_cross_only_on_first_bar(self, sample_df):
        result = calculate_supertrend(sample_df)

        is_bullish = result["sup_is_bullish"].values
        valid_start = 15

        for i in range(valid_start + 1, len(is_bullish)):
            if is_bullish[i] == is_bullish[i - 1]:
                assert not (
                    result["sup_cross_bullish"].iloc[i] or result["sup_cross_bearish"].iloc[i]
                ), f"Cross should be False when trend unchanged at index {i}"

    def test_no_crash_on_200_candles(self, sample_df):
        result = calculate_supertrend(sample_df, period=14, multiplier=1.8)
        assert len(result) == 200
        assert "sup_is_bullish" in result.columns
        assert "sup_cross_bullish" in result.columns
        assert "sup_cross_bearish" in result.columns
        assert "supertrend_line" in result.columns
        assert result["supertrend_line"].notna().sum() > 0


class TestMA:
    def test_sma(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = _ma(s, 3, "SMA")
        assert result.iloc[2] == 2.0

    def test_ema(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = _ma(s, 3, "EMA")
        assert not pd.isna(result.iloc[-1])

    def test_wma(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = _ma(s, 3, "WMA")
        assert not pd.isna(result.iloc[-1])

    def test_smma(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = _ma(s, 3, "SMMA")
        assert not pd.isna(result.iloc[-1])

    def test_alma(self):
        s = pd.Series([1.0] * 20)
        result = _ma(s, 10, "ALMA")
        assert not pd.isna(result.iloc[-1])

    def test_invalid_ma_type(self):
        s = pd.Series([1, 2, 3, 4, 5])
        with pytest.raises(ValueError):
            _ma(s, 3, "INVALID")
