import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict
import pandas as pd
import yfinance as yf
import QuantLib as ql

from .database.operations import DatabaseManager
from .data_loaders.technicals_loader import TechnicalIndicatorsLoader
from .data_loaders.fundamentals_loader import FundamentalMetricsLoader
from .analytics.beta import BetaCalculator
from .utils.date_utils import DateUtils

logger = logging.getLogger(__name__)


class StockDataPipeline:
    """Main pipeline for stock data ingestion and processing"""
    
    def __init__(self, db_name: str = None,
                       start_date: str = '2019-12-31',
                       beta_start_date: str = '2016-11-01',
                       max_workers: int = 5):
        if db_name:
            self.db = DatabaseManager(db_name=db_name)
        else:
            logger.error("Missing db_name")
            raise ValueError("Must provide db_name!")
        
        # Load util classes
        self.date_utils = DateUtils()
        self.tech_loader = TechnicalIndicatorsLoader()
        self.fund_loader = FundamentalMetricsLoader()
        self.beta_calc = BetaCalculator(self.date_utils)
        
        self.start_date = self.date_utils.string_to_ql(start_date)
        self.beta_start_date = self.date_utils.string_to_ql(beta_start_date)
        self.max_workers = max_workers
        
        self.db.create_intial_portfolio_snap_tables()
        
        logger.info("Pipeline initialized successfully")
    
    def get_security_info(self, ticker: str) -> Dict[str, str]:
        """Get security type and sector from database or yfinance"""
        try:
            query = "SELECT SEC_TYPE, SECTOR FROM SEC_INFO WHERE TICKER = :ticker"
            result = self.db.read_sql_qry(query, params={'ticker': ticker})
            
            if not result.empty:
                return {'sec_type': result['SEC_TYPE'].iloc[0],
                        'sector': result['SECTOR'].iloc[0] or ''}
        except Exception as e:
            logger.warning(f"Could not fetch security info from DB for {ticker}: {e}")
        
        # falls back to yfinance
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {'sec_type': info.get('quoteType', 'EQUITY'),
                    'sector': info.get('sector', '')}
        except Exception as e:
            logger.error(f"Could not fetch security info for {ticker}: {e}")
            return {'sec_type': 'EQUITY', 'sector': ''}
    
    def add_new_ticker(self, ticker: str,
                             pos_date: ql.Date,
                             beta_df: Optional[pd.DataFrame] = None
                       ) -> Dict[str, Optional[pd.DataFrame]]:
        """Add a new ticker with full historical data"""
        results = {'info': None, 'technical': None, 'fundamental': None}
        
        try:
            logger.info(f"Adding new ticker: {ticker}")
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                logger.error(f"No info available for {ticker}")
                return results
            
            # Get security info
            sec_type = info.get('quoteType', 'EQUITY')
            sector = info.get('sector', '')
            
            # Store security info
            sec_info_df = pd.DataFrame([{
                'TICKER': ticker,
                'SEC_TYPE': sec_type,
                'COMPANY_NAME': info.get('shortName'),
                'SECTOR': sector,
                'INDUSTRY': info.get('industry')
            }])
            results['info'] = sec_info_df
            
            end_date = self.date_utils.advance(pos_date, -1, ql.Days)
            
            # Load technical data
            tech_df = self.tech_loader.load_historical_technicals(
                ticker, stock, self.start_date, end_date, beta_df)
            results['technical'] = tech_df
            
            # Load fundamental data - YOUR LOGIC
            fund_df = self.fund_loader.load_historical_fundamentals(
                ticker, stock, self.start_date, end_date, sec_type, sector)
            results['fundamental'] = fund_df
            
            logger.info(f"Successfully loaded new ticker: {ticker}")
            
        except Exception as e:
            logger.error(f"Error adding new ticker {ticker}: {e}")
        
        return results
    
    def update_ticker(self, ticker: str, pos_date: ql.Date
                     ) -> Dict[str, Optional[pd.DataFrame]]:
        """Update an existing ticker with current data"""
        results = {'technical': None, 'fundamental': None}
        
        try:
            logger.info(f"Updating ticker: {ticker}")
            
            stock = yf.Ticker(ticker)
            
            # Get security info for fundamentals
            sec_info = self.get_security_info(ticker)
            
            # Load technical data
            tech_df = self.tech_loader.load_current_technicals(ticker, stock, pos_date)
            results['technical'] = tech_df
            
            # Load fundamental data
            fund_df = self.fund_loader.load_current_fundamentals(
                ticker, stock, pos_date, 
                sec_info['sec_type'], 
                sec_info['sector'])
            results['fundamental'] = fund_df
            
        except Exception as e:
            logger.error(f"Error updating ticker {ticker}: {e}")
        
        return results
    
    def process_portfolio_parallel(self, tickers: List[str], 
                                   pos_date: ql.Date,
                                   update_mode: bool = True
                                   ) -> Dict[str, List[pd.DataFrame]]:
        """Process multiple tickers in parallel"""
        results = {'info': [], 'technical': [], 'fundamental': []}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if update_mode:
                futures = {executor.submit(self.update_ticker, ticker, pos_date): ticker
                           for ticker in tickers}
            else:
                logger.info("Calculating betas for new tickers...")
                beta_df = self.beta_calc.calculate_historical_betas(
                    tickers, self.beta_start_date, pos_date)
                futures = {executor.submit(self.add_new_ticker, ticker, pos_date, beta_df): ticker
                           for ticker in tickers}
            
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    ticker_results = future.result()
                    for key in ['info', 'technical', 'fundamental']:
                        if ticker_results.get(key) is not None:
                            results[key].append(ticker_results[key])
                    logger.info(f"Successfully processed {ticker}")
                except Exception as e:
                    logger.error(f"Failed to process {ticker}: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"Processed {len(tickers)} tickers in {elapsed:.2f}s")
        return results
    
    def update_portfolio(self, tickers: List[str], pos_date: Optional[ql.Date] = None):
        """Main entry point: Update portfolio with latest data"""
        if pos_date is None:
            pos_date = self.date_utils.get_last_business_day()
        
        logger.info(f"Starting portfolio update for {pos_date.ISO()}")
        
        existing_tickers = set(self.db.get_all_tickers())
        new_tickers = set(tickers) - existing_tickers
        update_tickers = set(tickers) & existing_tickers
        
        # Process new tickers
        if new_tickers:
            logger.info(f"Adding {len(new_tickers)} new tickers")
            new_results = self.process_portfolio_parallel(
                list(new_tickers), pos_date, update_mode=False)
            
            # Insert into database
            for info_df in new_results['info']:
                self.db.upload_to_db(info_df, 'SEC_INFO')
            
            for tech_df in new_results['technical']:
                if tech_df is not None and not tech_df.empty:
                    self.db.upload_to_db(tech_df, 'TECHNICAL_SNAPS')
            
            for fund_df in new_results['fundamental']:
                if fund_df is not None and not fund_df.empty:
                    self.db.upload_to_db(fund_df, 'FUNDAMENTAL_SNAPS')
        
        # Update existing tickers
        if update_tickers:
            logger.info(f"Updating {len(update_tickers)} existing tickers")
            update_results = self.process_portfolio_parallel(
                list(update_tickers), pos_date, update_mode=True)
            
            # Insert into database
            for tech_df in update_results['technical']:
                if tech_df is not None and not tech_df.empty:
                    self.db.upload_to_db(tech_df, 'TECHNICAL_SNAPS')
            
            for fund_df in update_results['fundamental']:
                if fund_df is not None and not fund_df.empty:
                    self.db.upload_to_db(fund_df, 'FUNDAMENTAL_SNAPS')
        
        logger.info("Portfolio update completed successfully")
    
    def export_to_excel(self, output_file: str):
        """Export all data to Excel file"""
        logger.info(f"Exporting data to {output_file}")
        
        sec_info = self.db.read_sql_qry("SELECT * FROM SEC_INFO")
        tech_snaps = self.db.read_sql_qry("SELECT * FROM TECHNICAL_SNAPS ORDER BY TICKER, POS_DATE")
        fund_snaps = self.db.read_sql_qry("SELECT * FROM FUNDAMENTAL_SNAPS ORDER BY TICKER, POS_DATE")
        
        with pd.ExcelWriter(output_file) as writer:
            sec_info.to_excel(writer, sheet_name='SEC_INFO', index=False)
            tech_snaps.to_excel(writer, sheet_name='TECHNICAL_SNAPS', index=False)
            fund_snaps.to_excel(writer, sheet_name='FUNDAMENTAL_SNAPS', index=False)
        
        logger.info(f"Data exported successfully to {output_file}")
    
    def close(self):
        """Clean up resources"""
        self.db.close_conn()
        logger.info("Pipeline closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    

    pipeline = StockDataPipeline(db_name='PORTFOLIO_SNAPS', max_workers=5)
    pipeline.update_portfolio(['AAPL', 'MSFT'])
    pipeline.export_to_excel('portfolio_data.xlsx')
    pipeline.close()