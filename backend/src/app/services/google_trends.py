"""
Google Trends data fetching service.

Fetches Google Trends data for keywords using pytrends library.
Implements caching to minimize API calls and handle rate limiting.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from pytrends.request import TrendReq
import pandas as pd

from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.utils.retry import retry_sync

logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Service for fetching Google Trends data with caching."""

    # Rate limiting: pytrends recommends delays between requests
    MIN_REQUEST_DELAY = 1.0  # seconds between requests
    MAX_RETRIES = 3

    def __init__(self, hl: str = "en-US", tz: int = 360):
        """
        Initialize Google Trends service.

        Args:
            hl: Language (default: en-US)
            tz: Timezone offset in minutes (default: 360 = UTC-6)
        """
        self.pytrends = TrendReq(hl=hl, tz=tz, timeout=(10, 25))
        self.last_request_time: Optional[float] = None
        self.hl = hl
        self.tz = tz

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.MIN_REQUEST_DELAY:
                sleep_time = self.MIN_REQUEST_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_trends_data(
        self,
        keyword: str,
        timeframe: str = "today 12-m",
        geo: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch Google Trends data for a keyword.

        Args:
            keyword: Keyword to fetch trends for
            timeframe: Time range (default: "today 12-m" for past 12 months)
            geo: Geographic location (empty string = worldwide)

        Returns:
            Dictionary with trends data or None if error
        """
        self._rate_limit()

        def _fetch():
            try:
                self.pytrends.build_payload(
                    [keyword],
                    cat=0,  # All categories
                    timeframe=timeframe,
                    geo=geo,
                    gprop="",  # Web search (not images, news, etc.)
                )

                # Get interest over time
                interest_over_time = self.pytrends.interest_over_time()

                if interest_over_time.empty:
                    logger.warning(f"No data returned for keyword: {keyword}")
                    return None

                # Convert to dictionary format
                data = {
                    "keyword": keyword,
                    "timeframe": timeframe,
                    "geo": geo,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "data": interest_over_time.to_dict(orient="records"),
                    "columns": list(interest_over_time.columns),
                }

                logger.info(
                    f"Fetched Google Trends data for '{keyword}': "
                    f"{len(interest_over_time)} data points"
                )
                return data

            except Exception as e:
                logger.error(f"Error fetching Google Trends for '{keyword}': {e}")
                raise

        try:
            data = retry_sync(
                _fetch,
                max_attempts=self.MAX_RETRIES,
                delay=2.0,
                exceptions=(Exception,),
            )
            return data
        except Exception as e:
            logger.error(
                f"Failed to fetch Google Trends data for '{keyword}' after retries: {e}"
            )
            return None

    def get_weekly_values(self, trends_data: Dict[str, Any]) -> List[float]:
        """
        Extract weekly values from trends data.

        Args:
            trends_data: Dictionary from fetch_trends_data

        Returns:
            List of weekly trend values (0-100 scale)
        """
        if not trends_data or "data" not in trends_data:
            return []

        values = []
        for record in trends_data["data"]:
            # Get the keyword column value (usually the keyword itself)
            keyword_col = trends_data.get("keyword", "")
            if keyword_col and keyword_col in record:
                values.append(float(record[keyword_col]))
            else:
                # Fallback: get first numeric column
                for key, value in record.items():
                    if isinstance(value, (int, float)) and key != "isPartial":
                        values.append(float(value))
                        break

        return values

    def get_cached_trends_data(
        self, db: Session, keyword_id: int, max_age_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached Google Trends data from database.

        Args:
            db: Database session
            keyword_id: Keyword ID
            max_age_days: Maximum age of cached data in days

        Returns:
            Cached trends data or None if not found or too old
        """
        # Get most recent snapshot with trends data
        snapshot = (
            db.query(DailySnapshot)
            .filter(DailySnapshot.keyword_id == keyword_id)
            .filter(DailySnapshot.google_trends_data.isnot(None))
            .order_by(DailySnapshot.snapshot_date.desc())
            .first()
        )

        if not snapshot or not snapshot.google_trends_data:
            return None

        # Check if data is recent enough
        if snapshot.snapshot_date:
            age = datetime.utcnow().date() - snapshot.snapshot_date
            if age.days > max_age_days:
                logger.debug(
                    f"Cached data for keyword_id={keyword_id} is {age.days} days old, "
                    f"exceeds max_age={max_age_days}"
                )
                return None

        logger.debug(f"Using cached Google Trends data for keyword_id={keyword_id}")
        return snapshot.google_trends_data

    def fetch_or_get_cached(
        self,
        db: Session,
        keyword: str,
        keyword_id: Optional[int] = None,
        use_cache: bool = True,
        max_cache_age_days: int = 7,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch Google Trends data or return cached version if available.

        Args:
            db: Database session
            keyword: Keyword text
            keyword_id: Keyword ID (for cache lookup)
            use_cache: Whether to use cached data if available
            max_cache_age_days: Maximum age of cached data

        Returns:
            Trends data dictionary or None
        """
        # Try cache first if enabled
        if use_cache and keyword_id:
            cached = self.get_cached_trends_data(
                db, keyword_id, max_age_days=max_cache_age_days
            )
            if cached:
                return cached

        # Fetch fresh data
        return self.fetch_trends_data(keyword, timeframe="today 12-m", geo="")

    def batch_fetch_trends(
        self,
        db: Session,
        keywords: List[str],
        keyword_ids: Optional[List[int]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch trends data for multiple keywords with caching.

        Args:
            db: Database session
            keywords: List of keyword strings
            keyword_ids: Optional list of keyword IDs (for cache lookup)
            use_cache: Whether to use cached data

        Returns:
            Dictionary mapping keyword -> trends data
        """
        results = {}

        for i, keyword in enumerate(keywords):
            keyword_id = keyword_ids[i] if keyword_ids and i < len(keyword_ids) else None

            logger.info(f"Fetching trends for keyword {i+1}/{len(keywords)}: {keyword}")

            trends_data = self.fetch_or_get_cached(
                db=db,
                keyword=keyword,
                keyword_id=keyword_id,
                use_cache=use_cache,
            )

            results[keyword] = trends_data

            # Rate limiting between keywords
            if i < len(keywords) - 1:
                self._rate_limit()

        return results


def save_trends_data_to_snapshot(
    db: Session,
    keyword_id: int,
    snapshot_date: datetime.date,
    trends_data: Dict[str, Any],
) -> DailySnapshot:
    """
    Save Google Trends data to a daily snapshot.

    Args:
        db: Database session
        keyword_id: Keyword ID
        snapshot_date: Date for the snapshot
        trends_data: Google Trends data dictionary

    Returns:
        DailySnapshot instance
    """
    # Get or create snapshot
    snapshot = (
        db.query(DailySnapshot)
        .filter(DailySnapshot.keyword_id == keyword_id)
        .filter(DailySnapshot.snapshot_date == snapshot_date)
        .first()
    )

    if not snapshot:
        # Create new snapshot (score will be calculated later)
        snapshot = DailySnapshot(
            keyword_id=keyword_id,
            snapshot_date=snapshot_date,
            momentum_score=0,  # Will be calculated
            raw_score=0.0,
            lift_value=0.0,
            acceleration_value=0.0,
            novelty_value=0.0,
            noise_value=0.0,
        )
        db.add(snapshot)

    # Update trends data
    snapshot.google_trends_data = trends_data
    db.commit()
    db.refresh(snapshot)

    return snapshot

