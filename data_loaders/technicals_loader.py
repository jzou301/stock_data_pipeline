import logging
import time
import pandas as pd
import QuantLib as ql
from yfinance import Ticker
from utils.date_utils import DateUtils
from analytics.technicals import TechnicalsMetricsCalculator
from database.schema import TECHNICAL_COLUMNS

logger = logging.getLogger(__name__)

class TechnicalIndicatorsLoader:

    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.tech_calc = TechnicalsMetricsCalculator()
    
    def fetch_stock_history(self, stock: Ticker, start_date, end_date):
        """
        Fetch stock history from yfinance for [start_date, end_date] with attempts capped at self.max_retries
        """
        for attempt in range(self.max_retries):
            try:
                df = stock.history(start=start_date, end=end_date)
                if df.empty:
                    logger.warning(f"No data returned for {stock.ticker}")
                    return None
                return df
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch history: {e}")
                    return None
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
        return None
    
    def load_historical_technicals(self, ticker: str, stock: Ticker, start_date, end_date, beta_df):
        """
        Loads historical technical metrics for stock in [start_date, end_date] for backfilling
        """
        try:
            extended_start = DateUtils.advance(start_date, -200, ql.Days)
            
            df = self.fetch_stock_history(stock, extended_start.ISO(), end_date.ISO())
            if df is None:
                return None
            
            df['POS_DATE'] = df.index.map(DateUtils.timestamp_to_ql)
            df['TICKER'] = ticker
            
            df = self.tech_calc.get_market_cap(stock, df)
            df = self.tech_calc.calculate_moving_averages(df)
            df = self.tech_calc.calculate_volume_indicators(df)
            df = self.tech_calc.calculate_momentum_indicators(df)
            
            if beta_df is not None:
                df['FOM'] = df['POS_DATE'].apply(lambda x: ql.Date(1, x.month(), x.year()))
                df = df.merge(beta_df[['FOM', f'{ticker}_BETA']], on='FOM', how='left')
                df['BETA'] = df[f'{ticker}_BETA']
                df = df.drop(columns=['FOM', f'{ticker}_BETA'], errors='ignore')
            else:
                df['BETA'] = None
            
            df['POS_DATE'] = df['POS_DATE'].apply(lambda x: x.ISO())
            df['UPLOAD_STAT'] = 'BC'
            df = df[df['POS_DATE'] >= start_date.ISO()]
            
            
            df = df[TECHNICAL_COLUMNS]
            logger.info(f"Loaded {len(df)} technical records for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading technical data for {ticker}: {e}")
            return None
    
    def load_current_technicals(self, ticker: str, stock: Ticker, pos_date):
        """
        Loads current day financial metrics for stock with yfinance's stock.info
        """
        try:
            info = stock.info
            history = stock.history(period="1y")
            
            if history.empty:
                logger.warning(f"No history data for {ticker}")
                return None
            
            if not DateUtils.compare_dates(pos_date, history.index[-1]):
                logger.warning(f"Yahoo Finance data not updated for {ticker}")
                return None
            
            calc_df = pd.DataFrame(history)
            calc_df = self.tech_calc.calculate_moving_averages(calc_df)
            calc_df = self.tech_calc.calculate_volume_indicators(calc_df)
            calc_df = self.tech_calc.calculate_momentum_indicators(calc_df)
            
            data = {'POS_DATE': pos_date.ISO(),
                    'TICKER': ticker,
                    'MARKET_CAP': info.get('marketCap'),
                    'OPEN': info.get('open'),
                    'HIGH': info.get('dayHigh'),
                    'LOW': info.get('dayLow'),
                    'CLOSE': info.get('previousClose'),
                    'SMA_50D': info.get('fiftyDayAverage'),
                    'SMA_200D': info.get('twoHundredDayAverage'),
                    'EMA_12D': calc_df['EMA_12D'].iloc[-1],
                    'EMA_26D': calc_df['EMA_26D'].iloc[-1],
                    'EMA_50D': calc_df['EMA_50D'].iloc[-1],
                    'EMA_200D': calc_df['EMA_200D'].iloc[-1],
                    'VOLUME': info.get('volume'),
                    'VMA_20D': calc_df['VMA_20D'].iloc[-1],
                    'VMA_50D': calc_df['VMA_50D'].iloc[-1],
                    'VMA_200D': calc_df['VMA_200D'].iloc[-1],
                    'BETA': info.get('beta'),
                    'VWMA_50D': calc_df['VWMA_50D'].iloc[-1],
                    'VWMA_200D': calc_df['VWMA_200D'].iloc[-1],
                    'MACD_12D_26D': calc_df['MACD_12D_26D'].iloc[-1],
                    'RSI_14D': calc_df['RSI_14D'].iloc[-1],
                    'UPLOAD_STAT': 'AD'}
            
            df = pd.DataFrame([data])
            logger.info(f"Loaded current technical data for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading current technicals for {ticker}: {e}")
            return None