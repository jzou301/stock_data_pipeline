# Import packages
import sqlite3 
import pandas as pd

class myDB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(f'{self.db_name}.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
       
    def upload_to_db(self, df, table_name):
        return df.to_sql(name=table_name, if_exists='append', con=self.conn, index=False)

    def read_sql_qry(self, query):
        return pd.read_sql(query, self.conn)
    
    def close_conn(self):
        self.conn.close()
        self.cursor.close()
        return

    def create_intial_portfolio_snap_tables(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS SEC_INFO (
            TICKER VARCHAR(50),
            SEC_TYPE VARCHAR(100),
            COMPANY_NAME VARCHAR(500), 
            SECTOR VARCHAR(100), 
            INDUSTRY VARCHAR(100)); """ 
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
            UPLOAD_STAT VARCHAR(10)  );"""
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

        print("SNAP tables created successfully.")
        return
