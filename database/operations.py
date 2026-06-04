import logging
import sqlite3
from typing import List, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .schema import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_name):
     
        if db_name:
            self.connection_string = f'sqlite:///{db_name}.db'
        else:
            logger.error("Missing db_name")
            raise ValueError("Must provide db_name for connection!")
        
        self.engine = create_engine(self.connection_string, 
                                    echo=False,
                                    connect_args={'check_same_thread': False} if 'sqlite' in self.connection_string else {})
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        if 'sqlite' in self.connection_string:
            db_path = self.connection_string.replace('sqlite:///', '')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
        else:
            self.conn = None
            self.cursor = None
        
        logger.info(f"Database initialized: {self.connection_string}")
    
    def create_tables(self):
        """Create all tables using SQLAlchemy ORM"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def create_intial_portfolio_snap_tables(self):
        if self.cursor is None:
            self.create_tables()
            return
        
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS SEC_INFO (
                TICKER VARCHAR(50),
                SEC_TYPE VARCHAR(100),
                COMPANY_NAME VARCHAR(500), 
                SECTOR VARCHAR(100), 
                INDUSTRY VARCHAR(100)
            );"""
            self.cursor.execute(create_table_query)
            self.conn.commit()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS TECHNICAL_SNAPS (
                POS_DATE DATETIME,
                TICKER VARCHAR(50),
                MARKET_CAP FLOAT,
                OPEN FLOAT,
                HIGH FLOAT,
                LOW FLOAT,
                CLOSE FLOAT,
                SMA_50D FLOAT,
                SMA_200D FLOAT,
                EMA_12D FLOAT,
                EMA_26D FLOAT,
                EMA_50D FLOAT,
                EMA_200D FLOAT,
                VOLUME FLOAT,
                VMA_20D FLOAT,
                VMA_50D FLOAT,
                VMA_200D FLOAT,
                BETA FLOAT,
                VWMA_50D FLOAT,
                VWMA_200D FLOAT,
                MACD_12D_26D FLOAT,
                RSI_14D FLOAT,
                UPLOAD_STAT VARCHAR(10)
            );"""
            self.cursor.execute(create_table_query)
            self.conn.commit()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS FUNDAMENTAL_SNAPS (
                POS_DATE DATETIME,
                TICKER VARCHAR(50),
                FYE_DATE DATETIME, 
                EV FLOAT,
                EBIT FLOAT,
                NII FLOAT,
                EPS FLOAT,
                PE_RATIO FLOAT,
                PEG_RATIO FLOAT,
                ROE FLOAT,
                DC_RATIO FLOAT,
                ICR FLOAT,
                EV_to_EBIT FLOAT,
                OPERATING_MARGIN FLOAT,
                QUICK_RATIO FLOAT,
                FWD_EPS FLOAT,
                FWD_PE FLOAT,
                ANALYST_RECS FLOAT,
                UPLOAD_STAT VARCHAR(10)
            );"""
            self.cursor.execute(create_table_query)
            self.conn.commit()
            
            logger.info("SNAP tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def upload_to_db(self, df: pd.DataFrame, table_name: str) -> int:

        try:
            result = df.to_sql(name=table_name, 
                               if_exists='append', 
                               con=self.conn if self.conn else self.engine,
                               index=False)
            logger.info(f"Uploaded {len(df)} rows to {table_name}")
            return result
        except Exception as e:
            logger.error(f"Error uploading to {table_name}: {e}")
            raise
    
    def read_sql_qry(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        try:
            if params: df = pd.read_sql(text(query), self.engine, params=params)
            else: df = pd.read_sql(query, self.conn if self.conn else self.engine)
            return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def close_conn(self):
        try:
            if self.cursor: self.cursor.close()
            if self.conn: self.conn.close()
        
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
            raise
    
    def get_all_tickers(self) -> List[str]:
        """Get all tickers from SEC_INFO table"""
        query = "SELECT DISTINCT TICKER FROM SEC_INFO ORDER BY TICKER"
        df = self.read_sql_qry(query)
        return df['TICKER'].tolist() if not df.empty else []
    
    def close(self):
        self.close_conn()


