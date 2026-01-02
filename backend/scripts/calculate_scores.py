#!/usr/bin/env python3
"""
Script to calculate momentum scores for keywords.

Usage:
    python -m scripts.calculate_scores [keyword_id1] [keyword_id2] ...
    python -m scripts.calculate_scores --all  # Calculate for all keywords
"""

import sys
import os
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.services.momentum_service import MomentumService
from app.models.keyword import Keyword
from app.utils.logging import setup_logging

logger = setup_logging()


def main():
    """Main function to calculate momentum scores."""
    logger.info("Starting momentum score calculation")

    # Initialize database
    init_db()

    # Create service
    momentum_service = MomentumService()

    db: Session = SessionLocal()
    try:
        # Parse arguments
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            # Calculate for all keywords
            logger.info("Calculating scores for all keywords")
            results = momentum_service.calculate_scores_for_all_keywords(db)

            successful = sum(1 for v in results.values() if v is not None)
            total = len(results)

            logger.info(f"Completed: {successful}/{total} keywords scored successfully")

        else:
            # Calculate for specific keyword IDs
            if len(sys.argv) > 1:
                keyword_ids = [int(kw_id) for kw_id in sys.argv[1:]]
            else:
                # Default: get first 5 keywords
                keywords = db.query(Keyword).limit(5).all()
                keyword_ids = [kw.id for kw in keywords]
                logger.info(f"No keyword IDs provided, using first {len(keyword_ids)} keywords")

            logger.info(f"Calculating scores for keyword IDs: {keyword_ids}")

            results = momentum_service.calculate_scores_for_keywords(db, keyword_ids)

            # Print results
            for keyword_id, snapshot in results.items():
                keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
                if snapshot:
                    logger.info(
                        f"Keyword '{keyword.keyword}' (ID: {keyword_id}): "
                        f"Score = {snapshot.momentum_score}/100"
                    )
                else:
                    logger.warning(
                        f"Keyword '{keyword.keyword}' (ID: {keyword_id}): "
                        f"Failed to calculate score"
                    )

    except Exception as e:
        logger.error(f"Error during score calculation: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

