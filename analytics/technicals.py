from functools import wraps
from utils.date_utils import DateUtils
import logging

logger = logging.getLogger(__name__)


class TechnicalsMetricsCalculator:

    @staticmethod
    def calculate_moving_averages(df):
        """
        Calculate Simple Moving Averages and Exponetial Moving Averages
        SMA Periods: 50D, 200D
        EMA Periods: 12D, 26D, 50D, 200D
        """
        df['SMA_50D'] = df['Close'].rolling(window=50).mean()
        df['SMA_200D'] = df['Close'].rolling(window=200).mean()
        df['EMA_12D'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26D'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['EMA_50D'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200D'] = df['Close'].ewm(span=200, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_volume_indicators(df):
        """
        Calculate Moving Average of Volume and Volume Weighted Moving Averages for Price
        VMA Periods: 20D, 50D, 200D
        VWMA Periods: 50D, 200D
        """
        df['VMA_20D'] = df['Volume'].rolling(window=20).mean()
        df['VMA_50D'] = df['Volume'].rolling(window=50).mean()
        df['VMA_200D'] = df['Volume'].rolling(window=200).mean()
        df['VWMA_50D'] = (df['Close'] * df['Volume']).rolling(window=50).sum() / df['Volume'].rolling(window=50).sum()
        df['VWMA_200D'] = (df['Close'] * df['Volume']).rolling(window=200).sum() / df['Volume'].rolling(window=200).sum()
        return df
    
    @staticmethod
    def calculate_momentum_indicators(df):
        """
        Calculate Moving Average Convergence Divergence and Relative Strength Indicator
        MACD = EMA(12D) - EMA(26D)
        RSI(14D) = 100 - (100 / (1 + GAIN/LOSS))
        """
        df['MACD_12D_26D'] = df['EMA_12D'] - df['EMA_26D']

        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI_14D'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def get_market_cap(stock, df):
        """
        Calculate Market Cap
        Market Cap = Outstanding shares * Last price
        """
        try:
            shares_df = stock.get_shares_full().to_frame(name='SHARES')
            shares_df = shares_df.sort_index()
            shares_df['POS_DATE'] = shares_df.index.map(DateUtils.timestamp_to_ql)
            df = df.merge(shares_df[['POS_DATE', 'SHARES']], on='POS_DATE', how='left')
            df['SHARES'] = df['SHARES'].ffill()
            df['MARKET_CAP'] = df['SHARES'] * df['Close']
        except Exception as e:
            logger.warning(f"Could not fetch shares data: {e}")
            df['MARKET_CAP'] = None
        return df