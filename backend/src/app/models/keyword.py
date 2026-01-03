"""
Keyword model.
"""

from datetime import date
from sqlalchemy import Column, String, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class KeywordType(str, enum.Enum):
    """Keyword type enumeration."""

    KEYWORD = "keyword"
    HASHTAG = "hashtag"
    SOUND = "sound"


class Keyword(BaseModel):
    """Keyword model for tracking TikTok keywords."""

    __tablename__ = "keywords"

    keyword = Column(String(255), unique=True, nullable=False, index=True)
    keyword_type = Column(
        SQLEnum(KeywordType), default=KeywordType.KEYWORD, nullable=False, index=True
    )
    first_seen = Column(Date, nullable=True, index=True)
    last_seen = Column(Date, nullable=True, index=True)

    # Relationship to daily snapshots
    snapshots = relationship(
        "DailySnapshot",
        back_populates="keyword",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Relationship to Google Trends cache
    trends_cache = relationship(
        "GoogleTrendsCache",
        back_populates="keyword",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', type={self.keyword_type.value})>"
