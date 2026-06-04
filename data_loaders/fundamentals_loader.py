import logging
import pandas as pd
import numpy as np
from yfinance import Ticker
from analytics.fundamentals import FundamentalMetricsCalculator
from database.schema import FUNDAMENTAL_COLUMNS
from utils.date_utils import DateUtils
logger = logging.getLogger(__name__)


class FundamentalMetricsLoader:
    """Loads and calculates fundamental metrics"""
    
    def __init__(self, max_retries = 3):
        self.max_retries = max_retries
        self.fund_calc = FundamentalMetricsCalculator()

    @staticmethod
    def initialize_historical_fundamentals(ticker: str, stock: Ticker, 
                                     start_date, end_date):
        df = stock.history(start=start_date.ISO(), end=end_date.ISO())
        df['POS_DATE'] = df.index.map(lambda x: DateUtils.timestamp_to_ql(x).ISO())
        df['TICKER'] = ticker
        for col in ['FYE_DATE', 'EV', 'EBIT', 'NII', 'EPS', 'PE_RATIO', 'PEG_RATIO', 
                            'ROE', 'DC_RATIO', 'ICR', 'EV_to_EBIT', 'OPERATING_MARGIN', 'QUICK_RATIO',
                            'FWD_EPS', 'FWD_PE', 'ANALYST_RECS']:
            df[col] = None
        df['UPLOAD_STAT'] = 'BC'
        return df
    
    @staticmethod
    def load_hist_financials(ticker, df, stock):
        try:
            financials = stock.financials.T[['Operating Income', 'Total Revenue',
                                                'EBIT', 'Net Interest Income', 'Basic EPS', 
                                                'Net Income', 'Interest Expense']]
        except Exception as e:
            logger.warning(f"Could not fetch all financial columns for {ticker}: {e}")

            # Attempt with available columns
            financials = stock.financials.T
        
        # DATE MAPPING
        financials['FYE_DATE'] = financials.index.map(lambda x: DateUtils.timestamp_to_ql(x).ISO())
        df = df.merge(financials, left_on='POS_DATE', right_on='FYE_DATE', how='left')
        return df
    
    @staticmethod
    def load_hist_balsht(ticker, df, stock):
        try:
            balance_sheet = stock.balance_sheet.T[['Total Debt', 'Cash And Cash Equivalents', 
                                                    'Stockholders Equity', 'Current Assets', 
                                                    'Inventory', 'Current Liabilities']]
        except Exception as e:
            logger.warning(f"Could not fetch all balance sheet columns for {ticker}: {e}")
            balance_sheet = stock.balance_sheet.T


        balance_sheet['FYE_DATE_BS'] = balance_sheet.index.map(lambda x: DateUtils.timestamp_to_ql(x).ISO())
        df = df.merge(balance_sheet, left_on='POS_DATE', right_on='FYE_DATE_BS', how='left')
        return df
    

    def load_historical_fundamentals(self, ticker: str, stock: Ticker, 
                                     start_date, end_date, sec_type, sector):
        """
        Loads historical fundamental metrics for stock in date range
        [start_date, end_date] for backfilling
        
        """
        try:
            df = self.initialize_historical_fundamentals(ticker, stock, start_date, end_date)
            
            if sec_type != 'ETF':
                # Import financials and balance sheet
                df = self.load_hist_financials(ticker, df, stock)
                df = self.load_hist_balsht(ticker, df, stock)
               
                # FORWARD-FILL LOGIC FOR MISSING/NA DATA
                for col in ['FYE_DATE', 'EBIT', 'Net Interest Income', 
                            'Total Debt', 'Cash And Cash Equivalents',
                            'Net Income', 'Stockholders Equity', 'Interest Expense',
                            'Operating Income', 'Total Revenue', 'Current Assets',
                            'Inventory', 'Current Liabilities']:
                    df[col] = df[col].ffill()
                df = df.rename({'Net Interest Income': 'NII'})
                
                df = self.fund_calc.get_hist_valuation_metrics(ticker, df, stock, sector)
                df = self.fund_calc.get_hist_solvency_metrics(df, sector)
                df = self.fund_calc.get_hist_profitability_metrics(df)
                df = self.fund_calc.get_hist_liquidity_metrics(df)
                
                df['UPLOAD_STAT'] = 'BC'
                
            df = df[FUNDAMENTAL_COLUMNS]
            
            logger.info(f"Loaded {len(df)} fundamental records for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical fundamentals for {ticker}: {e}")
            return None
    
    @staticmethod
    def initialize_current_fundamentals_dict(ticker, pos_date):
        data = {
                    'POS_DATE': pos_date.ISO(),
                    'TICKER': ticker,
                    'FYE_DATE': None,
                    'EV': None,
                    'EBIT': None,
                    'NII': None,
                    'EPS': None,
                    'PE_RATIO': None,
                    'PEG_RATIO': None,
                    'ROE': None,
                    'DC_RATIO': None,
                    'ICR': None,
                    'EV_to_EBIT': None,
                    'OPERATING_MARGIN': None,
                    'QUICK_RATIO': None,
                    'FWD_EPS': None,
                    'FWD_PE': None,
                    'ANALYST_RECS': None,
                    'UPLOAD_STAT': 'AD'
                }
        return data
            

    def load_current_fundamentals(self, ticker, stock, pos_date, sec_type, sector):
        """
        Loads current day financial metrics for stock with yfinance's stock.info
        """
        try:
            data = self.initialize_current_fundamentals_dict(ticker, pos_date)
            
            if sec_type != 'ETF':
                info = stock.info
                balance_sheet = stock.balance_sheet
                financials = stock.financials
                
                data = {
                    'POS_DATE': pos_date.ISO(),
                    'TICKER': ticker,
                    'FYE_DATE': financials.columns[0] if not financials.empty else None,
                    'EV': info.get('enterpriseValue'),
                    'EBIT': None,  # Calculated below based on sector
                    'NII': None,
                    'EPS': info.get('trailingEps', None),
                    'PE_RATIO': info.get('trailingPE', None),
                    'PEG_RATIO': info.get('trailingPegRatio'),
                    'ROE': info.get('returnOnEquity'),
                    'DC_RATIO': None,
                    'ICR': None,
                    'EV_to_EBIT': None,
                    'OPERATING_MARGIN': info.get('operatingMargins'),
                    'QUICK_RATIO': info.get('quickRatio'),
                    'FWD_EPS': info.get('forwardEps', None),
                    'FWD_PE': info.get('forwardPE', None),
                    'ANALYST_RECS': info.get('recommendationMean'),
                    'UPLOAD_STAT': 'AD'
                } 
                
                data = self.fund_calc.get_spot_EBIT_NII(ticker, data, sector, financials)
                data = self.fund_calc.get_spot_debt_to_capital(ticker, data, balance_sheet)
                data = self.fund_calc.get_spot_icr(ticker, data, financials, sector)
                data = self.fund_calc.get_spot_ev_to_ebit(ticker, data, info, financials, sector):
              
                
            df = pd.DataFrame([data])
            logger.info(f"Loaded current fundamental data for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading current fundamentals for {ticker}: {e}")
            return None