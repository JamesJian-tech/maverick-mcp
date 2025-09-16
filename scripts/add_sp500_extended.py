#!/usr/bin/env python3
"""
Add extended S&P 500 stocks to the existing database.

This script adds the next 100 stocks to reach ~200 total S&P 500 stocks
in the maverick_mcp.db without complex connection pooling.
"""

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
logger = logging.getLogger("add_sp500_extended")

# Additional 100 S&P 500 stocks to extend from current 100 to 200
ADDITIONAL_SP500_STOCKS = [
    # Technology & Software
    "CRM", "ORCL", "ADBE", "INTC", "CSCO", "QCOM", "TXN", "AVGO", "AMD", "NVDA",
    "AMAT", "LRCX", "KLAC", "MCHP", "ADI", "MXIM", "XLNX", "INTU", "CTSH", "GLW",
    
    # Healthcare & Pharmaceuticals  
    "UNH", "JNJ", "PFE", "ABBV", "MRK", "BMY", "AMGN", "GILD", "REGN", "VRTX",
    "BIIB", "ILMN", "ISRG", "DXCM", "ZTS", "COO", "WAT", "IDXX", "ALGN", "TECH",
    
    # Financial Services
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB",
    "PNC", "TFC", "COF", "BK", "STT", "NTRS", "RF", "CFG", "KEY", "FITB",
    
    # Consumer & Retail
    "AMZN", "TSLA", "HD", "LOW", "TJX", "SBUX", "NKE", "MCD", "COST", "WMT",
    "TGT", "DG", "DLTR", "ROST", "BBY", "GPS", "M", "KSS", "JWN", "NCLH",
    
    # Industrial & Manufacturing
    "BA", "CAT", "MMM", "GE", "HON", "RTX", "LMT", "NOC", "GD", "EMR",
    "ITW", "PH", "ROK", "ETN", "JCI", "IR", "CMI", "DE", "FDX", "UPS",
    
    # Energy & Utilities
    "XOM", "CVX", "COP", "EOG", "SLB", "OXY", "VLO", "PSX", "MPC", "HES",
    "APA", "DVN", "FANG", "MRO", "HAL", "BKR", "NOV", "HP", "CHK", "EQT",
    
    # Materials & Chemicals  
    "LIN", "APD", "ECL", "SHW", "FCX", "NEM", "DD", "DOW", "LYB", "CF",
    "FMC", "PPG", "IFF", "ALB", "CE", "VMC", "MLM", "NUE", "STLD", "X",
    
    # Communication & Media
    "GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR", "FOXA",
    "FOX", "PARA", "WBD", "NWSA", "NWS", "IPG", "OMC", "TTWO", "EA", "ATVI",
    
    # Real Estate & REITs
    "AMT", "PLD", "CCI", "EQIX", "SPG", "O", "WELL", "PSA", "EXR", "AVB",
    "EQR", "VTR", "ESS", "MAA", "UDR", "CPT", "FRT", "REG", "KIM", "BXP",
    
    # Consumer Staples
    "PG", "KO", "PEP", "WMT", "COST", "MDLZ", "GIS", "K", "HSY", "CPB",
    "CAG", "SJM", "MKC", "CHD", "CLX", "CL", "KMB", "TSN", "HRL", "MNST"
]


def add_stocks_to_database(database_url: str = None) -> int:
    """Add additional S&P 500 stocks to the database."""
    db_url = database_url or os.getenv("DATABASE_URL") or "sqlite:///maverick_mcp.db"
    
    # Use simple engine without complex pooling for SQLite
    engine = create_engine(db_url, echo=False, pool_size=1, max_overflow=0)
    SessionLocal = sessionmaker(bind=engine)
    
    added_count = 0
    
    with SessionLocal() as session:
        for ticker in ADDITIONAL_SP500_STOCKS:
            try:
                # Check if stock already exists
                existing = session.query(Stock).filter_by(ticker_symbol=ticker).first()
                if existing:
                    logger.info(f"Stock {ticker} already exists, skipping")
                    continue
                
                # Create new stock record with basic info
                stock = Stock(
                    ticker_symbol=ticker,
                    company_name=f"{ticker} Inc.",  # Placeholder name
                    sector="Unknown",  # Will be updated later if needed
                    industry="Unknown",
                    exchange="NYSE",  # Default exchange
                    country="US",
                    currency="USD",
                    is_active=True,
                )
                session.add(stock)
                session.commit()
                
                added_count += 1
                logger.info(f"Added stock: {ticker}")
                
            except Exception as e:
                logger.error(f"Error adding stock {ticker}: {e}")
                session.rollback()
                continue
    
    return added_count


def main():
    """Main function."""
    logger.info("Adding extended S&P 500 stocks to database...")
    
    try:
        added_count = add_stocks_to_database()
        logger.info(f"Successfully added {added_count} new stocks to database")
        
        # Show final count
        db_url = os.getenv("DATABASE_URL") or "sqlite:///maverick_mcp.db"
        engine = create_engine(db_url, echo=False, pool_size=1, max_overflow=0)
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            total_count = session.query(Stock).count()
            logger.info(f"Total stocks in database: {total_count}")
            
    except Exception as e:
        logger.error(f"Failed to add stocks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()