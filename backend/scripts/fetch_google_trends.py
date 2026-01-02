#!/usr/bin/env python3
"""
Script to fetch Google Trends data for keywords and save to database.

Usage:
    python -m scripts.fetch_google_trends [keyword1] [keyword2] ...
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.services.google_trends import GoogleTrendsService
from app.services.trends_cache import TrendsCache
from app.services.keyword_service import KeywordService
from app.utils.logging import setup_logging

logger = setup_logging()


def main():
    """Main function to fetch and cache Google Trends data."""
    logger.info("Starting Google Trends data fetching")

    # Initialize database
    init_db()

    # Get keywords from command line or use defaults
    if len(sys.argv) > 1:
        keyword_texts = sys.argv[1:]
    else:
        # Default test keywords
        keyword_texts = ["python", "javascript", "tiktok"]

    logger.info(f"Fetching trends for keywords: {keyword_texts}")

    # Create service
    trends_service = GoogleTrendsService()

    db: Session = SessionLocal()
    try:
        # Get or create keywords
        keyword_ids = []
        for keyword_text in keyword_texts:
            keyword = KeywordService.get_or_create_keyword(db, keyword_text)
            keyword_ids.append(keyword.id)
            logger.info(f"Keyword: {keyword.keyword} (ID: {keyword.id})")

        # Fetch trends data
        today = date.today()
        results = {}

        for keyword_text, keyword_id in zip(keyword_texts, keyword_ids):
            logger.info(f"\nFetching trends for: {keyword_text}")

            # Check cache first
            cached = TrendsCache.get_cached(db, keyword_id, max_age_days=7)
            if cached:
                logger.info(f"Using cached data for '{keyword_text}'")
                results[keyword_text] = cached
            else:
                # Fetch fresh data
                trends_data = trends_service.fetch_trends_data(
                    keyword_text, timeframe="today 12-m", geo=""
                )

                if trends_data:
                    # Save to cache
                    TrendsCache.set_cached(db, keyword_id, today, trends_data)
                    results[keyword_text] = trends_data

                    # Extract weekly values
                    weekly_values = trends_service.get_weekly_values(trends_data)
                    logger.info(
                        f"Fetched {len(weekly_values)} weekly data points for '{keyword_text}'"
                    )
                    if weekly_values:
                        logger.info(
                            f"  First value: {weekly_values[0]}, "
                            f"Last value: {weekly_values[-1]}"
                        )
                else:
                    logger.warning(f"Failed to fetch trends for '{keyword_text}'")

        logger.info(f"\nSuccessfully processed {len(results)} keywords")

    except Exception as e:
        logger.error(f"Error during trends fetching: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

