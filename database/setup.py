from dataclasses import dataclass

@dataclass(frozen=True)
class TableSchema:
    columns : list 
    create_table : str

SEC_INFO_SCHEMA = TableSchema(columns = ['TICKER', 'SEC_TYPE', 'COMPANY_NAME', 'SECTOR', 'INDUSTRY'],
                              create_table = """
                                    CREATE TABLE IF NOT EXISTS SEC_INFO (
                                        TICKER VARCHAR(50),
                                        SEC_TYPE VARCHAR(100),
                                        COMPANY_NAME VARCHAR(500), 
                                        SECTOR VARCHAR(100), 
                                        INDUSTRY VARCHAR(100)
                                    );""")

TECHNICAL_SNAPS_SCHEMA = TableSchema(columns = ['POS_DATE', 'TICKER', 'MARKET_CAP'],
                                     create_table = """CREATE TABLE IF NOT EXISTS TECHNICAL_SNAPS (
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

FUNDAMENTAL_SNAPS_INITIALIZATION = """
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
            