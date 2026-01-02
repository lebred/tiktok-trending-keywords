"""
Pydantic schemas for API request/response models.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KeywordBase(BaseModel):
    """Base keyword schema."""

    keyword: str


class KeywordResponse(KeywordBase):
    """Keyword response schema."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScoreMetrics(BaseModel):
    """Score metrics breakdown."""

    momentum_score: int = Field(
        ..., ge=1, le=100, description="Final momentum score (1-100)"
    )
    raw_score: float = Field(..., description="Raw calculated score")
    lift_value: float = Field(..., description="Lift metric value")
    acceleration_value: float = Field(..., description="Acceleration metric value")
    novelty_value: float = Field(..., description="Novelty metric value")
    noise_value: float = Field(..., description="Noise metric value")


class DailySnapshotResponse(BaseModel):
    """Daily snapshot response schema."""

    id: int
    keyword_id: int
    snapshot_date: date
    momentum_score: int
    raw_score: float
    lift_value: float
    acceleration_value: float
    novelty_value: float
    noise_value: float
    created_at: datetime

    class Config:
        from_attributes = True


class KeywordDetailResponse(KeywordResponse):
    """Keyword detail response with latest snapshot."""

    latest_snapshot: Optional[DailySnapshotResponse] = None


class KeywordListItem(BaseModel):
    """Keyword list item with score."""

    id: int
    keyword: str
    momentum_score: Optional[int] = None
    snapshot_date: Optional[date] = None

    class Config:
        from_attributes = True


class KeywordListResponse(BaseModel):
    """Paginated keyword list response."""

    items: List[KeywordListItem]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class KeywordHistoryResponse(BaseModel):
    """Keyword score history response."""

    keyword_id: int
    keyword: str
    history: List[DailySnapshotResponse]
    total: int


class ArchiveResponse(BaseModel):
    """Archive snapshot response."""

    date: date
    keywords: List[KeywordListItem]
    total: int
    page: int = 1
    page_size: int = 50
    has_next: bool = False
    has_prev: bool = False


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: Optional[str] = None
