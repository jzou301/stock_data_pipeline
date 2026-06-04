"""
Unit tests for technical indicators module.
"""

import pytest
import pandas as pd
import numpy as np
import QuantLib as ql

from src.data_loaders.technicals import TechnicalIndicatorsLoader
from src.utils.date_utils import DateUtils


@pytest.fixture
def date_utils():
    return DateUtils()


@pytest.fixture
def tech_loader(date_utils):
    return TechnicalIndicatorsLoader(date_utils)


@pytest.fixture
def sample_price_data():
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    data = {
        'Close': np.random.uniform(100, 200, 100),
        'Open': np.random.uniform(100, 200, 100),
        'High': np.random.uniform(150, 250, 100),
        'Low': np.random.uniform(50, 150, 100),
        'Volume': np.random.randint(1000000, 10000000, 100)
    }
    return pd.DataFrame(data, index=dates)


class TestMovingAverages:
    """Test moving average calculations"""
    
    def test_sma_calculation(self, tech_loader, sample_price_data):
        df = tech_loader.calculate_moving_averages(sample_price_data.copy())
        assert 'SMA_50D' in df.columns
        assert 'SMA_200D' in df.columns
        assert not df['SMA_50D'].iloc[50:].isna().all()
        valid_sma = df['SMA_50D'].dropna()
        assert (valid_sma >= df['Close'].min() * 0.8).all()
        assert (valid_sma <= df['Close'].max() * 1.2).all()
    
    def test_ema_calculation(self, tech_loader, sample_price_data):
        df = tech_loader.calculate_moving_averages(sample_price_data.copy())
        assert 'EMA_12D' in df.columns
        assert 'EMA_26D' in df.columns
        assert df['EMA_12D'].notna().sum() > df['SMA_50D'].notna().sum()


class TestMomentumIndicators:
    """Test momentum indicator calculations"""
    
    def test_rsi_calculation(self, tech_loader, sample_price_data):
        df = tech_loader.calculate_moving_averages(sample_price_data.copy())
        df = tech_loader.calculate_momentum_indicators(df)
        assert 'RSI_14D' in df.columns
        valid_rsi = df['RSI_14D'].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_macd_calculation(self, tech_loader, sample_price_data):
        df = tech_loader.calculate_moving_averages(sample_price_data.copy())
        df = tech_loader.calculate_momentum_indicators(df)
        assert 'MACD_12D_26D' in df.columns
        macd = df['MACD_12D_26D'].iloc[-1]
        ema_diff = df['EMA_12D'].iloc[-1] - df['EMA_26D'].iloc[-1]
        assert abs(macd - ema_diff) < 0.01