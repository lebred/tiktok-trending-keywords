"""
Daily snapshot model for storing keyword momentum scores.
"""

from datetime import date
from sqlalchemy import Column, Integer, ForeignKey, Date, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DailySnapshot(BaseModel):
    """Daily snapshot of keyword momentum score and metrics."""
    
    __tablename__ = "daily_snapshots"
    
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Score values
    momentum_score = Column(Integer, nullable=False)  # Final score 1-100
    raw_score = Column(Float, nullable=False)  # Raw calculated score before normalization
    
    # Component metrics
    lift_value = Column(Float, nullable=False)
    acceleration_value = Column(Float, nullable=False)
    novelty_value = Column(Float, nullable=False)
    noise_value = Column(Float, nullable=False)
    
    # Google Trends data (stored as JSON)
    google_trends_data = Column(JSON, nullable=True)
    
    # Relationship to keyword
    keyword = relationship("Keyword", back_populates="snapshots")
    
    # Ensure one snapshot per keyword per date
    __table_args__ = (
        UniqueConstraint('keyword_id', 'snapshot_date', name='uq_keyword_snapshot_date'),
    )
    
    def __repr__(self):
        return f"<DailySnapshot(id={self.id}, keyword_id={self.keyword_id}, date={self.snapshot_date}, score={self.momentum_score})>"

