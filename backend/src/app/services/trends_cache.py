"""
Caching layer for Google Trends data.

Provides database-based caching to minimize API calls and handle rate limiting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.daily_snapshot import DailySnapshot

logger = logging.getLogger(__name__)


class TrendsCache:
    """Cache manager for Google Trends data."""

    @staticmethod
    def get_cached(
        db: Session,
        keyword_id: int,
        max_age_days: int = 7,
        snapshot_date: Optional[datetime.date] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached Google Trends data.

        Args:
            db: Database session
            keyword_id: Keyword ID
            max_age_days: Maximum age of cached data in days
            snapshot_date: Specific snapshot date to retrieve (optional)

        Returns:
            Cached trends data or None
        """
        query = (
            db.query(DailySnapshot)
            .filter(DailySnapshot.keyword_id == keyword_id)
            .filter(DailySnapshot.google_trends_data.isnot(None))
        )

        if snapshot_date:
            query = query.filter(DailySnapshot.snapshot_date == snapshot_date)
        else:
            # Get most recent
            query = query.order_by(DailySnapshot.snapshot_date.desc())

        snapshot = query.first()

        if not snapshot or not snapshot.google_trends_data:
            return None

        # Check age if not requesting specific date
        if not snapshot_date and snapshot.snapshot_date:
            age = datetime.utcnow().date() - snapshot.snapshot_date
            if age.days > max_age_days:
                logger.debug(
                    f"Cached data for keyword_id={keyword_id} is {age.days} days old, "
                    f"exceeds max_age={max_age_days}"
                )
                return None

        logger.debug(f"Cache hit for keyword_id={keyword_id}")
        return snapshot.google_trends_data

    @staticmethod
    def set_cached(
        db: Session,
        keyword_id: int,
        snapshot_date: datetime.date,
        trends_data: Dict[str, Any],
    ) -> DailySnapshot:
        """
        Cache Google Trends data.

        Args:
            db: Database session
            keyword_id: Keyword ID
            snapshot_date: Date for the snapshot
            trends_data: Trends data to cache

        Returns:
            DailySnapshot instance
        """
        # Get or create snapshot
        snapshot = (
            db.query(DailySnapshot)
            .filter(
                and_(
                    DailySnapshot.keyword_id == keyword_id,
                    DailySnapshot.snapshot_date == snapshot_date,
                )
            )
            .first()
        )

        if not snapshot:
            snapshot = DailySnapshot(
                keyword_id=keyword_id,
                snapshot_date=snapshot_date,
                momentum_score=0,
                raw_score=0.0,
                lift_value=0.0,
                acceleration_value=0.0,
                novelty_value=0.0,
                noise_value=0.0,
            )
            db.add(snapshot)

        snapshot.google_trends_data = trends_data
        db.commit()
        db.refresh(snapshot)

        logger.debug(
            f"Cached trends data for keyword_id={keyword_id}, date={snapshot_date}"
        )
        return snapshot

    @staticmethod
    def invalidate_cache(db: Session, keyword_id: int) -> int:
        """
        Invalidate all cached data for a keyword.

        Args:
            db: Database session
            keyword_id: Keyword ID

        Returns:
            Number of snapshots updated
        """
        count = (
            db.query(DailySnapshot)
            .filter(DailySnapshot.keyword_id == keyword_id)
            .filter(DailySnapshot.google_trends_data.isnot(None))
            .update({DailySnapshot.google_trends_data: None})
        )
        db.commit()
        logger.info(f"Invalidated cache for keyword_id={keyword_id}: {count} snapshots")
        return count

    @staticmethod
    def get_cache_stats(db: Session, keyword_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            db: Database session
            keyword_id: Optional keyword ID to filter by

        Returns:
            Dictionary with cache statistics
        """
        query = db.query(DailySnapshot).filter(
            DailySnapshot.google_trends_data.isnot(None)
        )

        if keyword_id:
            query = query.filter(DailySnapshot.keyword_id == keyword_id)

        total_cached = query.count()

        # Get oldest and newest cached data
        oldest = (
            query.order_by(DailySnapshot.snapshot_date.asc()).first()
            if total_cached > 0
            else None
        )
        newest = (
            query.order_by(DailySnapshot.snapshot_date.desc()).first()
            if total_cached > 0
            else None
        )

        return {
            "total_cached": total_cached,
            "oldest_date": oldest.snapshot_date.isoformat() if oldest else None,
            "newest_date": newest.snapshot_date.isoformat() if newest else None,
        }

