from functools import wraps
import numpy as np
import logging
from utils.date_utils import DateUtils
logger = logging.getLogger(__name__)

def calc_ratio(ratio_name):
    def decorator(func):
        @wraps(func)
        def wrapper(ticker, df, *args, **kwargs):
            try:
                return func(ticker, df, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Could not calculate {ratio_name} for {ticker}: {e}")
                return df
        return wrapper
    return decorator

class FundamentalMetricsCalculator:

    @calc_ratio('EBIT/NII')
    @staticmethod
    def get_spot_EBIT_NII(ticker, data: dict, sector, financials): 
        if 'Financial' in sector:
            data['EBIT'] = financials.loc['Net Income'].iloc[0]
            data['NII'] = financials.loc['Net Interest Income'].iloc[0]
        else:
            data['EBIT'] = financials.loc['EBIT'].iloc[0]
            data['NII'] = financials.loc['Net Interest Income'].iloc[0] if 'Net Interest Income' in financials.index else None
        return data

    @calc_ratio('DC Ratio')
    @staticmethod
    def get_spot_debt_to_capital(ticker, df: dict, df_balsht):
        total_debt = df_balsht.loc['Total Debt'].iloc[0]
        stockholders_equity = df_balsht.loc['Stockholders Equity'].iloc[0]
        df['DC_RATIO'] = total_debt / (total_debt + stockholders_equity)
        return df
    
    @calc_ratio('ICR')
    @staticmethod
    def get_spot_icr(ticker, data: dict, financials, sector):
        interest_expense = financials.loc['Interest Expense'].iloc[0]
        if 'Financial' in sector:
            data['ICR'] = financials.loc['Net Income'].iloc[0] / interest_expense
        else:
            data['ICR'] = financials.loc['EBIT'].iloc[0] / interest_expense
        return data
    
    @calc_ratio('EV_to_EBIT')
    @staticmethod
    def get_spot_ev_to_ebit(ticker, data: dict, info, financials, sector):
        if 'Financial' in sector:
            data['EV_to_EBIT'] = info.get('enterpriseValue') / financials.loc['Net Income'].iloc[0]
        else:
            data['EV_to_EBIT'] = info.get('enterpriseValue') / financials.loc['EBIT'].iloc[0]
        return data

    @calc_ratio('EPS')
    @staticmethod
    def get_hist_eps(ticker, df, stock):
      
        eps = stock.get_earnings_history()[['epsActual']]
        eps['POS_DATE'] = eps.index.map(lambda x: DateUtils.timestamp_to_ql(x).ISO())
        df = df.merge(eps, on='POS_DATE', how='left')

        df['EPS'] = np.vectorize(lambda fye, qtr: qtr if qtr is not None else fye) \
            (df['epsActual'], df['EPS'])
       
        return df
    
    @staticmethod
    def get_hist_valuation_metrics(ticker, df, stock, sector):
        # EV CALCULATION
        df['EV'] = None  # df['MARKET_CAP'] + df['Total Debt'] - df['Cash And Cash Equivalents']
                
        # EPS - merging quarterly with annual
        df['EPS'] = df['Basic EPS']
        df['Annual EPS Growth Rate'] = df['EPS'].pct_change() * 100
        df = FundamentalMetricsCalculator.get_hist_eps(ticker, df, stock)
        df['EPS'] = df['EPS'].ffill()
        df['Annual EPS Growth Rate'] = df['Annual EPS Growth Rate'].ffill()

        # PE/PEG RATIO 
        df['PE_RATIO'] = df['Close'] / df['EPS']
        df['PEG_RATIO'] = np.vectorize(
            lambda pe, eps_growth: pe / eps_growth if eps_growth != 0 else None
        )(df['PE_RATIO'], df['Annual EPS Growth Rate'])

        # EV/EBIT
        if 'Financial' in sector:
            df['EV_to_EBIT'] = df['EV'] / df['Net Income']
        else:
            df['EV_to_EBIT'] = df['EV'] / df['EBIT']

        df['FWD_EPS'] = None
        df['FWD_PE'] = None
        df['ANALYST_RECS'] = None
        return df
    
    @staticmethod
    def get_hist_solvency_metrics(df, sector):
        df['DC_RATIO'] = df['Total Debt'] / (df['Total Debt'] + df['Stockholders Equity'])
                
        # ICR 
        if 'Financial' in sector:
            df['ICR'] = df['Net Income'] / df['Interest Expense']
    
        else:
            df['ICR'] = df['EBIT'] / df['Interest Expense']
        return df
    
    @staticmethod
    def get_hist_profitability_metrics(df):
        df['ROE'] = df['Net Income'] / df['Stockholders Equity']
        df['OPERATING_MARGIN'] = df['Operating Income'] / df['Total Revenue']
        return df
    
    @staticmethod
    def get_hist_liquidity_metrics(df):
        df['QUICK_RATIO'] = (df['Current Assets'] - df['Inventory']) / df['Current Liabilities']
        return df
                
                