"""
Google Trends cache model for storing time series data.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    JSON,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class GoogleTrendsCache(BaseModel):
    """
    Cache for Google Trends time series data.

    Stores the full time series (weekly values) for each keyword/geo/timeframe combination.
    This enables generating static public pages with Google Trends charts without
    exposing TikTok-specific details.
    """

    __tablename__ = "google_trends_cache"

    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    geo = Column(
        String(10), default="", nullable=False
    )  # Geographic location (empty = worldwide)
    timeframe = Column(String(50), default="today 12-m", nullable=False)  # Time range

    # Time series data stored as JSON
    # Format: {"data": [{"date": "2024-01-01", "value": 50}, ...], "fetched_at": "..."}
    time_series_data = Column(JSON, nullable=False)

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship to keyword
    keyword = relationship("Keyword", back_populates="trends_cache")

    # Ensure one cache entry per keyword/geo/timeframe combination
    __table_args__ = (
        UniqueConstraint(
            "keyword_id", "geo", "timeframe", name="uq_keyword_geo_timeframe"
        ),
        Index("idx_keyword_fetched", "keyword_id", "fetched_at"),
    )

    def __repr__(self):
        return f"<GoogleTrendsCache(id={self.id}, keyword_id={self.keyword_id}, geo='{self.geo}', timeframe='{self.timeframe}')>"
