#!/usr/bin/env python3
"""
Add smart stocks from JSON file to the database.

This script adds the missing stocks from top_100_smart.json to the maverick_mcp database.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from maverick_mcp.data.models import Stock

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("add_smart_stocks")

# Missing smart stocks that need to be added
MISSING_SMART_STOCKS = [
    'ABNB', 'ANSS', 'ASML', 'AXON', 'BIDU', 'BKNG', 'BMRN', 'CDNS', 'CEG', 'CPRT', 
    'CRWD', 'CTAS', 'DLR', 'EBAY', 'EXC', 'FAST', 'FSLR', 'GOOG', 'JD', 'KDP', 
    'LCID', 'LLY', 'LULU', 'MAR', 'MRNA', 'MTCH', 'NTES', 'NXPI', 'ODFL', 'OKTA', 
    'PANW', 'PAYX', 'PCAR', 'PDD', 'PLTR', 'RIVN', 'SIRI', 'SMCI', 'SNOW', 'TEAM', 
    'TTD', 'VERI', 'VRSK', 'WDAY', 'XEL', 'ZS'
]

# Company mappings for better naming
COMPANY_NAMES = {
    'ABNB': 'Airbnb Inc.',
    'ANSS': 'Ansys Inc.',
    'ASML': 'ASML Holding N.V.',
    'AXON': 'Axon Enterprise Inc.',
    'BIDU': 'Baidu Inc.',
    'BKNG': 'Booking Holdings Inc.',
    'BMRN': 'BioMarin Pharmaceutical Inc.',
    'CDNS': 'Cadence Design Systems Inc.',
    'CEG': 'Constellation Energy Corporation',
    'CPRT': 'Copart Inc.',
    'CRWD': 'CrowdStrike Holdings Inc.',
    'CTAS': 'Cintas Corporation',
    'DLR': 'Digital Realty Trust Inc.',
    'EBAY': 'eBay Inc.',
    'EXC': 'Exelon Corporation',
    'FAST': 'Fastenal Company',
    'FSLR': 'First Solar Inc.',
    'GOOG': 'Alphabet Inc. Class C',
    'JD': 'JD.com Inc.',
    'KDP': 'Keurig Dr Pepper Inc.',
    'LCID': 'Lucid Group Inc.',
    'LLY': 'Eli Lilly and Company',
    'LULU': 'Lululemon Athletica Inc.',
    'MAR': 'Marriott International Inc.',
    'MRNA': 'Moderna Inc.',
    'MTCH': 'Match Group Inc.',
    'NTES': 'NetEase Inc.',
    'NXPI': 'NXP Semiconductors N.V.',
    'ODFL': 'Old Dominion Freight Line Inc.',
    'OKTA': 'Okta Inc.',
    'PANW': 'Palo Alto Networks Inc.',
    'PAYX': 'Paychex Inc.',
    'PCAR': 'PACCAR Inc.',
    'PDD': 'PDD Holdings Inc.',
    'PLTR': 'Palantir Technologies Inc.',
    'RIVN': 'Rivian Automotive Inc.',
    'SIRI': 'Sirius XM Holdings Inc.',
    'SMCI': 'Super Micro Computer Inc.',
    'SNOW': 'Snowflake Inc.',
    'TEAM': 'Atlassian Corporation',
    'TTD': 'The Trade Desk Inc.',
    'VERI': 'Veritone Inc.',
    'VRSK': 'Verisk Analytics Inc.',
    'WDAY': 'Workday Inc.',
    'XEL': 'Xcel Energy Inc.',
    'ZS': 'Zscaler Inc.'
}

# Sector mappings
SECTOR_MAPPINGS = {
    'ABNB': 'Consumer Discretionary',
    'ANSS': 'Information Technology',
    'ASML': 'Information Technology', 
    'AXON': 'Industrials',
    'BIDU': 'Communication Services',
    'BKNG': 'Consumer Discretionary',
    'BMRN': 'Health Care',
    'CDNS': 'Information Technology',
    'CEG': 'Utilities',
    'CPRT': 'Industrials',
    'CRWD': 'Information Technology',
    'CTAS': 'Industrials',
    'DLR': 'Real Estate',
    'EBAY': 'Consumer Discretionary',
    'EXC': 'Utilities',
    'FAST': 'Industrials',
    'FSLR': 'Information Technology',
    'GOOG': 'Communication Services',
    'JD': 'Consumer Discretionary',
    'KDP': 'Consumer Staples',
    'LCID': 'Consumer Discretionary',
    'LLY': 'Health Care',
    'LULU': 'Consumer Discretionary',
    'MAR': 'Consumer Discretionary',
    'MRNA': 'Health Care',
    'MTCH': 'Communication Services',
    'NTES': 'Communication Services',
    'NXPI': 'Information Technology',
    'ODFL': 'Industrials',
    'OKTA': 'Information Technology',
    'PANW': 'Information Technology',
    'PAYX': 'Information Technology',
    'PCAR': 'Industrials',
    'PDD': 'Consumer Discretionary',
    'PLTR': 'Information Technology',
    'RIVN': 'Consumer Discretionary',
    'SIRI': 'Communication Services',
    'SMCI': 'Information Technology',
    'SNOW': 'Information Technology',
    'TEAM': 'Information Technology',
    'TTD': 'Information Technology',
    'VERI': 'Information Technology',
    'VRSK': 'Industrials',
    'WDAY': 'Information Technology',
    'XEL': 'Utilities',
    'ZS': 'Information Technology'
}


def add_smart_stocks_to_database(database_url: str = None) -> int:
    """Add missing smart stocks to the database."""
    db_url = database_url or os.getenv("DATABASE_URL") or "sqlite:///maverick_mcp.db"
    
    # Use simple engine without complex pooling for SQLite
    engine = create_engine(db_url, echo=False, pool_size=1, max_overflow=0)
    SessionLocal = sessionmaker(bind=engine)
    
    added_count = 0
    
    with SessionLocal() as session:
        for ticker in MISSING_SMART_STOCKS:
            try:
                # Check if stock already exists
                existing = session.query(Stock).filter_by(ticker_symbol=ticker).first()
                if existing:
                    logger.info(f"Stock {ticker} already exists, skipping")
                    continue
                
                # Create new stock record with detailed info
                stock = Stock(
                    ticker_symbol=ticker,
                    company_name=COMPANY_NAMES.get(ticker, f"{ticker} Inc."),
                    sector=SECTOR_MAPPINGS.get(ticker, "Unknown"),
                    industry="Technology/Growth",  # Most smart stocks are tech/growth
                    exchange="NASDAQ" if ticker in ['ABNB', 'ANSS', 'CRWD', 'SNOW', 'TEAM', 'ZS'] else "NYSE",
                    country="US" if ticker not in ['ASML', 'BIDU', 'JD', 'NTES', 'NXPI', 'PDD'] else "International",
                    currency="USD",
                    is_active=True,
                )
                session.add(stock)
                session.commit()
                
                added_count += 1
                logger.info(f"Added smart stock: {ticker} - {COMPANY_NAMES.get(ticker, ticker)}")
                
            except Exception as e:
                logger.error(f"Error adding stock {ticker}: {e}")
                session.rollback()
                continue
    
    return added_count


def main():
    """Main function."""
    logger.info("Adding smart stocks from JSON to database...")
    
    try:
        added_count = add_smart_stocks_to_database()
        logger.info(f"Successfully added {added_count} new smart stocks to database")
        
        # Show final count
        db_url = os.getenv("DATABASE_URL") or "sqlite:///maverick_mcp.db"
        engine = create_engine(db_url, echo=False, pool_size=1, max_overflow=0)
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            total_count = session.query(Stock).count()
            logger.info(f"Total stocks in database: {total_count}")
            
            # Count smart stocks in database
            smart_count = session.query(Stock).filter(
                Stock.ticker_symbol.in_(MISSING_SMART_STOCKS + 
                ['AAPL', 'ADBE', 'AMD', 'AMZN', 'AVGO', 'BAC', 'BIIB', 'BLK', 'CAT', 'CHTR',
                 'CMCSA', 'COP', 'COST', 'CSCO', 'CTSH', 'CVX', 'DE', 'DLTR', 'FANG', 'GE',
                 'GILD', 'GOOGL', 'GS', 'HD', 'IDXX', 'ILMN', 'INTC', 'INTU', 'ISRG', 'JNJ',
                 'JPM', 'KO', 'LMT', 'MCHP', 'MDLZ', 'META', 'MNST', 'MRK', 'MS', 'MSFT',
                 'MU', 'NOC', 'NVDA', 'PEP', 'PFE', 'PG', 'QCOM', 'REGN', 'ROST', 'SBUX',
                 'SLB', 'TSLA', 'TTWO', 'TXN', 'UNH', 'VRTX', 'WFC', 'WMT', 'XOM'])
            ).count()
            logger.info(f"Smart stocks now in database: {smart_count}")
            
    except Exception as e:
        logger.error(f"Failed to add smart stocks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()