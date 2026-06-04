from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

SEC_INFO_COLUMNS = #
TECHNICAL_COLUMNS = ['POS_DATE', 'TICKER', 'MARKET_CAP', 'Open', 'High', 'Low', 'Close',
                'SMA_50D', 'SMA_200D', 'EMA_12D', 'EMA_26D', 'EMA_50D', 'EMA_200D',
                'Volume', 'VMA_20D', 'VMA_50D', 'VMA_200D', 'BETA',
                'VWMA_50D', 'VWMA_200D', 'MACD_12D_26D', 'RSI_14D', 'UPLOAD_STAT']
FUNDAMENTAL_COLUMNS = ['POS_DATE', 'TICKER', 'FYE_DATE', 'EV', 'EBIT', 'NII', 'EPS', 
                     'PE_RATIO', 'PEG_RATIO', 'ROE', 'DC_RATIO', 'ICR', 'EV_to_EBIT',
                     'OPERATING_MARGIN', 'QUICK_RATIO', 'FWD_EPS', 'FWD_PE', 
                     'ANALYST_RECS', 'UPLOAD_STAT']
class SecurityInfo(Base):
    """Security master information table"""
    __tablename__ = 'sec_info'
    
    ticker = Column(String(50), primary_key=True, nullable=False)
    sec_type = Column(String(100))
    company_name = Column(String(500))
    sector = Column(String(100))
    industry = Column(String(100))


class TechnicalSnapshot(Base):
    """Daily technical indicators snapshot"""
    __tablename__ = 'technical_snaps'
    
    pos_date = Column(DateTime, primary_key=True, nullable=False)
    ticker = Column(String(50), primary_key=True, nullable=False)
    market_cap = Column(Float)
    open = Column(Float, name='open')
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, name='close')
    sma_50d = Column(Float)
    sma_200d = Column(Float)
    ema_12d = Column(Float)
    ema_26d = Column(Float)
    ema_50d = Column(Float)
    ema_200d = Column(Float)
    volume = Column(Float)
    vma_20d = Column(Float)
    vma_50d = Column(Float)
    vma_200d = Column(Float)
    beta = Column(Float)
    vwma_50d = Column(Float)
    vwma_200d = Column(Float)
    macd_12d_26d = Column(Float)
    rsi_14d = Column(Float)
    upload_stat = Column(String(10), default='AD')


class FundamentalSnapshot(Base):
    """Daily fundamental metrics snapshot"""
    __tablename__ = 'fundamental_snaps'
    
    pos_date = Column(DateTime, primary_key=True, nullable=False)
    ticker = Column(String(50), primary_key=True, nullable=False)
    fye_date = Column(DateTime)
    ev = Column(Float)
    ebit = Column(Float)
    nii = Column(Float)
    eps = Column(Float)
    pe_ratio = Column(Float)
    peg_ratio = Column(Float)
    roe = Column(Float)
    dc_ratio = Column(Float)
    icr = Column(Float)
    ev_to_ebit = Column(Float)
    operating_margin = Column(Float)
    quick_ratio = Column(Float)
    fwd_eps = Column(Float)
    fwd_pe = Column(Float)
    analyst_recs = Column(Float)
    upload_stat = Column(String(10), default='AD')


def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)