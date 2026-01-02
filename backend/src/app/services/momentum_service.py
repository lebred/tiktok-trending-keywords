"""
Momentum calculation service.

Orchestrates the calculation and storage of momentum scores for keywords.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.services.scoring import ScoringService
from app.services.google_trends import GoogleTrendsService
from app.services.trends_cache import TrendsCache

logger = logging.getLogger(__name__)


class MomentumService:
    """Service for calculating and storing momentum scores."""

    def __init__(self):
        """Initialize the momentum service."""
        self.trends_service = GoogleTrendsService()
        self.scoring_service = ScoringService()

    def calculate_and_save_score(
        self,
        db: Session,
        keyword_id: int,
        snapshot_date: Optional[date] = None,
        trends_data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Optional[DailySnapshot]:
        """
        Calculate momentum score for a keyword and save to database.

        Args:
            db: Database session
            keyword_id: Keyword ID
            snapshot_date: Date for snapshot (default: today)
            trends_data: Optional pre-fetched trends data
            use_cache: Whether to use cached trends data

        Returns:
            DailySnapshot instance or None if calculation failed
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        # Get keyword
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            logger.error(f"Keyword not found: {keyword_id}")
            return None

        # Get trends data if not provided
        if trends_data is None:
            if use_cache:
                trends_data = TrendsCache.get_cached(
                    db, keyword_id, max_age_days=7, snapshot_date=snapshot_date
                )

            if trends_data is None:
                # Fetch fresh data
                logger.info(f"Fetching Google Trends data for keyword: {keyword.keyword}")
                trends_data = self.trends_service.fetch_trends_data(
                    keyword.keyword, timeframe="today 12-m", geo=""
                )

                if trends_data:
                    # Cache the data
                    TrendsCache.set_cached(db, keyword_id, snapshot_date, trends_data)
                else:
                    logger.error(f"Failed to fetch trends data for keyword: {keyword.keyword}")
                    return None

        # Calculate score
        score_result = self.scoring_service.calculate_score_from_trends_data(trends_data)

        if score_result is None:
            logger.warning(
                f"Insufficient data to calculate score for keyword: {keyword.keyword}"
            )
            return None

        # Get or create snapshot
        snapshot = (
            db.query(DailySnapshot)
            .filter(DailySnapshot.keyword_id == keyword_id)
            .filter(DailySnapshot.snapshot_date == snapshot_date)
            .first()
        )

        if not snapshot:
            snapshot = DailySnapshot(
                keyword_id=keyword_id,
                snapshot_date=snapshot_date,
                momentum_score=score_result["momentum_score"],
                raw_score=score_result["raw_score"],
                lift_value=score_result["lift_value"],
                acceleration_value=score_result["acceleration_value"],
                novelty_value=score_result["novelty_value"],
                noise_value=score_result["noise_value"],
                google_trends_data=trends_data,
            )
            db.add(snapshot)
        else:
            # Update existing snapshot
            snapshot.momentum_score = score_result["momentum_score"]
            snapshot.raw_score = score_result["raw_score"]
            snapshot.lift_value = score_result["lift_value"]
            snapshot.acceleration_value = score_result["acceleration_value"]
            snapshot.novelty_value = score_result["novelty_value"]
            snapshot.noise_value = score_result["noise_value"]
            snapshot.google_trends_data = trends_data

        try:
            db.commit()
            db.refresh(snapshot)
            logger.info(
                f"Calculated score for '{keyword.keyword}': "
                f"{score_result['momentum_score']}/100 "
                f"(lift={score_result['lift_value']:.2f}, "
                f"accel={score_result['acceleration_value']:.2f}, "
                f"novelty={score_result['novelty_value']:.2f}, "
                f"noise={score_result['noise_value']:.2f})"
            )
            return snapshot
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            db.rollback()
            raise

    def calculate_scores_for_keywords(
        self,
        db: Session,
        keyword_ids: List[int],
        snapshot_date: Optional[date] = None,
    ) -> Dict[int, Optional[DailySnapshot]]:
        """
        Calculate scores for multiple keywords.

        Args:
            db: Database session
            keyword_ids: List of keyword IDs
            snapshot_date: Date for snapshot (default: today)

        Returns:
            Dictionary mapping keyword_id -> DailySnapshot or None
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        results = {}

        for keyword_id in keyword_ids:
            try:
                snapshot = self.calculate_and_save_score(
                    db, keyword_id, snapshot_date=snapshot_date
                )
                results[keyword_id] = snapshot
            except Exception as e:
                logger.error(f"Error calculating score for keyword_id={keyword_id}: {e}")
                results[keyword_id] = None

        return results

    def calculate_scores_for_all_keywords(
        self, db: Session, snapshot_date: Optional[date] = None
    ) -> Dict[int, Optional[DailySnapshot]]:
        """
        Calculate scores for all keywords in database.

        Args:
            db: Database session
            snapshot_date: Date for snapshot (default: today)

        Returns:
            Dictionary mapping keyword_id -> DailySnapshot or None
        """
        keywords = db.query(Keyword).all()
        keyword_ids = [kw.id for kw in keywords]

        logger.info(f"Calculating scores for {len(keyword_ids)} keywords")
        return self.calculate_scores_for_keywords(db, keyword_ids, snapshot_date)

