"""
Beta calculation using 36-month rolling window (YOUR beta logic).
"""

import logging
from typing import List
import pandas as pd
import numpy as np
import yfinance as yf
import QuantLib as ql
from numba import jit

logger = logging.getLogger(__name__)


@jit(nopython=True)
def calculate_beta(returns_matrix: np.ndarray, sample: bool = False) -> float:
    """
    Calculated stock beta using covariance method.
    Beta = Cov(stock_returns, market_returns) / Var(market_returns)
    """
    if np.isnan(returns_matrix).any():
        return np.nan
    
    market_returns = returns_matrix[:, 0]
    stock_returns = returns_matrix[:, 1]
    
    n = len(market_returns)
    if sample:
        n -= 1
    
    if n == 0:
        return np.nan
    
    market_mean = np.sum(market_returns) / n
    stock_mean = np.sum(stock_returns) / n
    
    covariance = np.sum(
        (market_returns - market_mean) * (stock_returns - stock_mean)
    ) / n
    
    variance = np.sum((market_returns - market_mean) ** 2) / n
    
    if variance == 0:
        return np.nan
    
    return covariance / variance


class BetaCalculator:
    """Calculates historical beta for stocks"""
    
    def __init__(self, date_utils, window_months: int = 36):
        self.date_utils = date_utils
        self.window_months = window_months
        self.market_index = "^GSPC"
    
    def calculate_historical_betas(
        self,
        tickers: List[str],
        start_date: ql.Date,
        end_date: ql.Date
    ) -> pd.DataFrame:
        """
        Calculate historical betas: 
        https://investexcel.net/how-does-yahoo-finance-calculate-beta/
        """
        try:
            all_tickers = [self.market_index] + list(tickers)
            
            logger.info(f"Downloading price data for beta calculation")
            
            price_df = yf.download(
                all_tickers,
                start=start_date.ISO(),
                end=end_date.ISO(),
                interval="1d",
                progress=False
            )['Close']
            
            if price_df.empty:
                logger.error("No price data downloaded")
                return pd.DataFrame()
            
            monthly_prices = price_df.resample('MS').first()
            monthly_prices['FOM'] = monthly_prices.index.map(
                self.date_utils.timestamp_to_ql
            )
            
            for ticker in all_tickers:
                if ticker not in monthly_prices.columns:
                    continue
                
                monthly_prices[f'LAST_{ticker}'] = monthly_prices[ticker].shift(1)
                monthly_prices[f'{ticker}_RTN'] = (
                    (monthly_prices[ticker] - monthly_prices[f'LAST_{ticker}']) 
                    / monthly_prices[f'LAST_{ticker}']
                )
            
            for ticker in tickers:
                if ticker not in monthly_prices.columns:
                    continue
                
                market_rtn_col = f'{self.market_index}_RTN'
                stock_rtn_col = f'{ticker}_RTN'
                
                if market_rtn_col not in monthly_prices.columns or stock_rtn_col not in monthly_prices.columns:
                    continue
                
                beta_series = monthly_prices[
                    [market_rtn_col, stock_rtn_col]
                ].rolling(
                    window=self.window_months,
                    min_periods=self.window_months,
                    method='table'
                ).apply(
                    calculate_beta,
                    raw=True,
                    engine='numba'
                )[stock_rtn_col]
                
                monthly_prices[f'{ticker}_BETA'] = beta_series
            
            beta_columns = ['FOM'] + [
                f'{t}_BETA' for t in tickers 
                if f'{t}_BETA' in monthly_prices.columns
            ]
            
            result_df = monthly_prices[beta_columns].copy()
            
            logger.info(f"Calculated betas for {len(tickers)} tickers")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating betas: {e}")
            return pd.DataFrame()