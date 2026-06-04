import argparse
import logging
import sys
from pathlib import Path
import QuantLib as ql

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import StockDataPipeline
from src.utils.date_utils import DateUtils


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler('logs/pipeline.log'),
                                  logging.StreamHandler()])


def load_tickers_from_file(filepath: str) -> list:
    """Load tickers from a text file (one per line)"""
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def parse_args(): 
    parser = argparse.ArgumentParser(description='Stock Data Pipeline')
    
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument('--tickers', nargs='+', help='List of ticker symbols')
    ticker_group.add_argument('--tickers-file', help='Path to file with tickers')
    ticker_group.add_argument('--all', action='store_true', help='Process all tickers in database')
    ticker_group.add_argument('--export', help='Export database to Excel file')
    
    parser.add_argument('--date', help='Position date (YYYY-MM-DD)')
    parser.add_argument('--db', default='PORTFOLIO_SNAPS', help='Database name')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        pipeline = StockDataPipeline(db_name=args.db, max_workers=args.workers)
        
        if args.export:
            logger.info(f"Exporting database to {args.export}")
            pipeline.export_to_excel(args.export)
            pipeline.close()
            return 0
        
        date_utils = DateUtils()
        if args.date:
            pos_date = date_utils.string_to_ql(args.date)
        else:
            pos_date = date_utils.get_last_business_day()
        
        logger.info(f"Processing data for {pos_date.ISO()}")
        
        if args.tickers:
            tickers = args.tickers
        elif args.tickers_file:
            tickers = load_tickers_from_file(args.tickers_file)
        elif args.all:
            tickers = pipeline.db.get_all_tickers()
            if not tickers:
                logger.error("No tickers found in database")
                return 1
        
        logger.info(f"Processing {len(tickers)} tickers")
        pipeline.update_portfolio(tickers, pos_date)
        pipeline.close()
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())