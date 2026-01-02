"""
Keyword model.
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Keyword(BaseModel):
    """Keyword model for tracking TikTok keywords."""
    
    __tablename__ = "keywords"
    
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    
    # Relationship to daily snapshots
    snapshots = relationship(
        "DailySnapshot",
        back_populates="keyword",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"

