#!/usr/bin/env python3
"""
Script to fetch trending keywords from TikTok Creative Center and save to database.

Usage:
    python -m scripts.fetch_trending_keywords
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.services.tiktok_ingestion import TikTokIngestionService, save_keywords_to_database
from app.utils.logging import setup_logging

logger = setup_logging()


async def main():
    """Main function to fetch and save trending keywords."""
    logger.info("Starting TikTok keyword ingestion")
    
    # Initialize database (create tables if needed)
    init_db()
    
    # Create service
    service = TikTokIngestionService()
    
    try:
        # Fetch all trending keywords
        keywords = await service.fetch_all_trending(limit_per_source=100)
        
        if not keywords:
            logger.warning("No keywords fetched. This may indicate:")
            logger.warning("1. TikTok API endpoints need to be updated")
            logger.warning("2. API requires authentication or different parameters")
            logger.warning("3. Network connectivity issues")
            return
        
        logger.info(f"Fetched {len(keywords)} unique keywords")
        
        # Save to database
        db: Session = SessionLocal()
        try:
            created_count = await save_keywords_to_database(db, keywords)
            logger.info(f"Successfully saved {created_count} new keywords to database")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())

