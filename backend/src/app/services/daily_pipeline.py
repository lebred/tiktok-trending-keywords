"""
Daily pipeline orchestration service.

Runs the complete daily pipeline:
1. Fetch trending keywords from TikTok
2. Save keywords to database
3. Fetch Google Trends data for each keyword
4. Calculate momentum scores
5. Save daily snapshots
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.tiktok_ingestion import (
    TikTokIngestionService,
    save_keywords_to_database,
)
from app.services.google_trends import GoogleTrendsService
from app.services.momentum_service import MomentumService
from app.services.keyword_service import KeywordService
from app.models.keyword import Keyword

logger = logging.getLogger(__name__)


class DailyPipeline:
    """Orchestrates the daily data processing pipeline."""

    def __init__(self):
        """Initialize the daily pipeline."""
        self.tiktok_service = TikTokIngestionService()
        self.trends_service = GoogleTrendsService()
        self.momentum_service = MomentumService()

    async def run_pipeline(
        self, snapshot_date: Optional[date] = None, max_keywords: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Run the complete daily pipeline.

        Args:
            snapshot_date: Date for snapshot (default: today)
            max_keywords: Maximum number of keywords to process (None = all)

        Returns:
            Dictionary with pipeline execution results
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        start_time = datetime.utcnow()
        logger.info(f"Starting daily pipeline for {snapshot_date}")

        results = {
            "snapshot_date": snapshot_date.isoformat(),
            "start_time": start_time.isoformat(),
            "keywords_fetched": 0,
            "keywords_saved": 0,
            "scores_calculated": 0,
            "scores_failed": 0,
            "errors": [],
        }

        db: Session = SessionLocal()
        try:
            # Step 1: Fetch trending keywords from TikTok
            logger.info("Step 1: Fetching trending keywords from TikTok")
            try:
                keywords = await self.tiktok_service.fetch_all_trending(
                    limit_per_source=100
                )
                results["keywords_fetched"] = len(keywords)

                if not keywords:
                    logger.warning("No keywords fetched from TikTok")
                    results["errors"].append("No keywords fetched from TikTok")
                else:
                    logger.info(f"Fetched {len(keywords)} unique keywords")

            except Exception as e:
                error_msg = f"Error fetching TikTok keywords: {e}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)
                keywords = []

            # Step 2: Save keywords to database
            logger.info("Step 2: Saving keywords to database")
            try:
                if keywords:
                    created_count = await save_keywords_to_database(db, keywords)
                    results["keywords_saved"] = created_count
                    logger.info(f"Saved {created_count} new keywords to database")
            except Exception as e:
                error_msg = f"Error saving keywords: {e}"
                logger.error(error_msg, exc_info=True)
                results["errors"].append(error_msg)

            # Step 3: Get all keywords (or limit if specified)
            logger.info("Step 3: Getting keywords for processing")
            query = db.query(Keyword).order_by(Keyword.created_at.desc())
            if max_keywords:
                query = query.limit(max_keywords)
            keywords_to_process = query.all()

            logger.info(f"Processing {len(keywords_to_process)} keywords")

            # Step 4: Process each keyword (fetch trends, calculate score)
            logger.info("Step 4: Processing keywords (fetching trends and calculating scores)")
            for i, keyword in enumerate(keywords_to_process, 1):
                try:
                    logger.info(
                        f"Processing keyword {i}/{len(keywords_to_process)}: {keyword.keyword}"
                    )

                    snapshot = self.momentum_service.calculate_and_save_score(
                        db=db,
                        keyword_id=keyword.id,
                        snapshot_date=snapshot_date,
                        use_cache=True,
                    )

                    if snapshot:
                        results["scores_calculated"] += 1
                        logger.debug(
                            f"Score calculated for '{keyword.keyword}': "
                            f"{snapshot.momentum_score}/100"
                        )
                    else:
                        results["scores_failed"] += 1
                        logger.warning(
                            f"Failed to calculate score for '{keyword.keyword}'"
                        )

                except Exception as e:
                    results["scores_failed"] += 1
                    error_msg = f"Error processing keyword '{keyword.keyword}': {e}"
                    logger.error(error_msg, exc_info=True)
                    results["errors"].append(error_msg)
                    # Continue with next keyword (don't crash entire pipeline)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = duration
            results["success"] = len(results["errors"]) == 0

            logger.info(
                f"Pipeline completed in {duration:.2f}s: "
                f"{results['scores_calculated']} scores calculated, "
                f"{results['scores_failed']} failed, "
                f"{len(results['errors'])} errors"
            )

            return results

        except Exception as e:
            error_msg = f"Critical error in daily pipeline: {e}"
            logger.error(error_msg, exc_info=True)
            results["errors"].append(error_msg)
            results["success"] = False
            return results

        finally:
            db.close()
            await self.tiktok_service.close()

    def run_pipeline_sync(
        self, snapshot_date: Optional[date] = None, max_keywords: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Synchronous wrapper for run_pipeline.

        Args:
            snapshot_date: Date for snapshot (default: today)
            max_keywords: Maximum number of keywords to process

        Returns:
            Dictionary with pipeline execution results
        """
        return asyncio.run(self.run_pipeline(snapshot_date, max_keywords))


def run_daily_pipeline(
    snapshot_date: Optional[date] = None, max_keywords: Optional[int] = None
) -> Dict[str, any]:
    """
    Convenience function to run the daily pipeline.

    Args:
        snapshot_date: Date for snapshot (default: today)
        max_keywords: Maximum number of keywords to process

    Returns:
        Dictionary with pipeline execution results
    """
    pipeline = DailyPipeline()
    return pipeline.run_pipeline_sync(snapshot_date, max_keywords)

