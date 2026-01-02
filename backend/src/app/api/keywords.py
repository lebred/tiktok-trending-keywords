"""
Keywords API endpoints.
"""

import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.models.user import User
from app.api.schemas import (
    KeywordListResponse,
    KeywordListItem,
    KeywordDetailResponse,
    KeywordHistoryResponse,
    DailySnapshotResponse,
    ErrorResponse,
)
from app.api.dependencies import get_current_user_optional, get_paid_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Limit results (for free users)"
    ),
    db: Session = Depends(get_db),
):
    """
    List keywords with their latest momentum scores.

    For free users, use 'limit' parameter to restrict results.
    For paid users, use pagination (page, page_size).
    """
    # Apply limit for free users (if specified)
    if limit:
        page_size = min(page_size, limit)

    # Get latest snapshot for each keyword
    # Subquery to get the most recent snapshot date for each keyword
    latest_snapshot_subquery = (
        db.query(
            DailySnapshot.keyword_id,
            func.max(DailySnapshot.snapshot_date).label("max_date"),
        )
        .group_by(DailySnapshot.keyword_id)
        .subquery()
    )

    # Join keywords with their latest snapshots
    query = (
        db.query(Keyword, DailySnapshot)
        .join(
            latest_snapshot_subquery,
            Keyword.id == latest_snapshot_subquery.c.keyword_id,
        )
        .join(
            DailySnapshot,
            (DailySnapshot.keyword_id == Keyword.id)
            & (DailySnapshot.snapshot_date == latest_snapshot_subquery.c.max_date),
        )
        .order_by(desc(DailySnapshot.momentum_score))
    )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    # Build response
    items = []
    for keyword, snapshot in results:
        items.append(
            KeywordListItem(
                id=keyword.id,
                keyword=keyword.keyword,
                momentum_score=snapshot.momentum_score,
                snapshot_date=snapshot.snapshot_date,
            )
        )

    return KeywordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        has_prev=page > 1,
    )


@router.get("/full", response_model=KeywordListResponse)
async def list_all_keywords(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(get_paid_user),
):
    """
    List all keywords (paid users only).

    This endpoint provides full access without limits.
    Requires paid subscription.
    """
    # Get all keywords with latest snapshots
    latest_snapshot_subquery = (
        db.query(
            DailySnapshot.keyword_id,
            func.max(DailySnapshot.snapshot_date).label("max_date"),
        )
        .group_by(DailySnapshot.keyword_id)
        .subquery()
    )

    query = (
        db.query(Keyword, DailySnapshot)
        .outerjoin(
            latest_snapshot_subquery,
            Keyword.id == latest_snapshot_subquery.c.keyword_id,
        )
        .outerjoin(
            DailySnapshot,
            (DailySnapshot.keyword_id == Keyword.id)
            & (DailySnapshot.snapshot_date == latest_snapshot_subquery.c.max_date),
        )
        .order_by(desc(DailySnapshot.momentum_score))
    )

    total = query.count()
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    items = []
    for keyword, snapshot in results:
        items.append(
            KeywordListItem(
                id=keyword.id,
                keyword=keyword.keyword,
                momentum_score=snapshot.momentum_score if snapshot else None,
                snapshot_date=snapshot.snapshot_date if snapshot else None,
            )
        )

    return KeywordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
        has_prev=page > 1,
    )


@router.get("/{keyword_id}", response_model=KeywordDetailResponse)
async def get_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
):
    """
    Get keyword details with latest snapshot.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Get latest snapshot
    latest_snapshot = (
        db.query(DailySnapshot)
        .filter(DailySnapshot.keyword_id == keyword_id)
        .order_by(desc(DailySnapshot.snapshot_date))
        .first()
    )

    return KeywordDetailResponse(
        id=keyword.id,
        keyword=keyword.keyword,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
        latest_snapshot=(
            DailySnapshotResponse.model_validate(latest_snapshot)
            if latest_snapshot
            else None
        ),
    )


@router.get("/{keyword_id}/history", response_model=KeywordHistoryResponse)
async def get_keyword_history(
    keyword_id: int,
    limit: Optional[int] = Query(
        None, ge=1, le=365, description="Limit number of snapshots"
    ),
    db: Session = Depends(get_db),
):
    """
    Get keyword score history.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Get snapshots ordered by date (most recent first)
    query = (
        db.query(DailySnapshot)
        .filter(DailySnapshot.keyword_id == keyword_id)
        .order_by(desc(DailySnapshot.snapshot_date))
    )

    if limit:
        query = query.limit(limit)

    snapshots = query.all()

    return KeywordHistoryResponse(
        keyword_id=keyword.id,
        keyword=keyword.keyword,
        history=[DailySnapshotResponse.model_validate(s) for s in snapshots],
        total=len(snapshots),
    )
