"""
Archive API endpoints for historical snapshots.
"""

import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.daily_snapshot import DailySnapshot
from app.models.keyword import Keyword
from app.models.user import User
from app.api.schemas import ArchiveResponse, KeywordListItem, ErrorResponse
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/archive", tags=["archive"])


@router.get("/{snapshot_date}", response_model=ArchiveResponse)
async def get_archive_snapshot(
    snapshot_date: date,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get historical snapshot for a specific date.

    Returns all keywords with their scores for the given date.
    Requires authentication.
    """
    # Get all snapshots for the date, ordered by score
    query = (
        db.query(DailySnapshot, Keyword)
        .join(Keyword, DailySnapshot.keyword_id == Keyword.id)
        .filter(DailySnapshot.snapshot_date == snapshot_date)
        .order_by(desc(DailySnapshot.momentum_score))
    )

    total = query.count()

    if total == 0:
        raise HTTPException(
            status_code=404, detail=f"No snapshot found for date {snapshot_date}"
        )

    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    # Build response
    keywords = []
    for snapshot, keyword in results:
        keywords.append(
            KeywordListItem(
                id=keyword.id,
                keyword=keyword.keyword,
                momentum_score=snapshot.momentum_score,
                snapshot_date=snapshot.snapshot_date,
            )
        )

    return ArchiveResponse(
        date=snapshot_date,
        keywords=keywords,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        has_prev=page > 1,
    )


@router.get("", response_model=list[date])
async def list_available_dates(
    limit: int = Query(30, ge=1, le=365, description="Number of dates to return"),
    db: Session = Depends(get_db),
):
    """
    List available snapshot dates.

    Returns list of dates that have snapshots, most recent first.
    """
    dates = (
        db.query(DailySnapshot.snapshot_date)
        .distinct()
        .order_by(desc(DailySnapshot.snapshot_date))
        .limit(limit)
        .all()
    )

    return [d[0] for d in dates]
