"""
Service for managing keywords in the database.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.keyword import Keyword
from app.utils.keyword_utils import normalize_keyword

logger = logging.getLogger(__name__)


class KeywordService:
    """Service for keyword database operations."""
    
    @staticmethod
    def get_or_create_keyword(db: Session, keyword_text: str) -> Keyword:
        """
        Get existing keyword or create a new one.
        
        Args:
            db: Database session
            keyword_text: Keyword string
            
        Returns:
            Keyword model instance
        """
        normalized = normalize_keyword(keyword_text)
        if not normalized:
            raise ValueError("Keyword cannot be empty")
        
        # Check if keyword already exists
        keyword = db.query(Keyword).filter(
            Keyword.keyword == normalized
        ).first()
        
        if not keyword:
            keyword = Keyword(keyword=normalized)
            db.add(keyword)
            db.commit()
            db.refresh(keyword)
            logger.debug(f"Created new keyword: {normalized}")
        else:
            logger.debug(f"Found existing keyword: {normalized}")
        
        return keyword
    
    @staticmethod
    def bulk_create_keywords(db: Session, keywords: List[str]) -> int:
        """
        Bulk create keywords, skipping duplicates.
        
        Args:
            db: Database session
            keywords: List of keyword strings
            
        Returns:
            Number of new keywords created
        """
        created_count = 0
        normalized_keywords = []
        
        # Normalize all keywords first
        for keyword_text in keywords:
            normalized = normalize_keyword(keyword_text)
            if normalized:
                normalized_keywords.append(normalized)
        
        if not normalized_keywords:
            return 0
        
        # Get existing keywords in one query
        existing_keywords = set(
            db.query(Keyword.keyword).filter(
                Keyword.keyword.in_(normalized_keywords)
            ).all()
        )
        existing_keywords = {kw[0] for kw in existing_keywords}
        
        # Create new keywords
        new_keywords = []
        for normalized in normalized_keywords:
            if normalized not in existing_keywords:
                new_keywords.append(Keyword(keyword=normalized))
                created_count += 1
        
        if new_keywords:
            db.add_all(new_keywords)
            try:
                db.commit()
                logger.info(f"Created {created_count} new keywords in database")
            except Exception as e:
                logger.error(f"Error saving keywords to database: {e}")
                db.rollback()
                raise
        
        return created_count
    
    @staticmethod
    def get_keyword_by_id(db: Session, keyword_id: int) -> Optional[Keyword]:
        """Get keyword by ID."""
        return db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    @staticmethod
    def get_keyword_by_text(db: Session, keyword_text: str) -> Optional[Keyword]:
        """Get keyword by normalized text."""
        normalized = normalize_keyword(keyword_text)
        return db.query(Keyword).filter(Keyword.keyword == normalized).first()
    
    @staticmethod
    def get_all_keywords(db: Session, limit: Optional[int] = None) -> List[Keyword]:
        """Get all keywords, optionally limited."""
        query = db.query(Keyword).order_by(Keyword.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_keyword_count(db: Session) -> int:
        """Get total count of keywords."""
        return db.query(func.count(Keyword.id)).scalar()

