"""
TikTok Creative Center trend ingestion service.

Fetches trending keywords, hashtags, and sounds from TikTok Creative Center
using HTTP requests (no UI automation).
"""

import asyncio
import logging
import re
from typing import List, Set
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.models.keyword import Keyword
from app.config import settings
from app.utils.keyword_utils import (
    normalize_keywords as normalize_keywords_util,
    deduplicate_keywords,
)
from app.services.keyword_service import KeywordService
from app.utils.retry import retry_async

logger = logging.getLogger(__name__)


class TikTokIngestionService:
    """Service for ingesting trending keywords from TikTok Creative Center."""

    # TikTok Creative Center base URLs
    BASE_URL = "https://ads.tiktok.com"
    TRENDING_KEYWORDS_URL = (
        f"{BASE_URL}/creative_radar_api/v1/popular_trend/keyword/list"
    )
    TRENDING_HASHTAGS_URL = (
        f"{BASE_URL}/creative_radar_api/v1/popular_trend/hashtag/list"
    )
    TRENDING_SOUNDS_URL = f"{BASE_URL}/creative_radar_api/v1/popular_trend/sound/list"

    def __init__(self):
        """Initialize the ingestion service."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def fetch_trending_keywords(self, limit: int = 100) -> List[str]:
        """
        Fetch trending keywords from TikTok Creative Center.

        Args:
            limit: Maximum number of keywords to fetch

        Returns:
            List of keyword strings
        """

        async def _fetch():
            # Note: Actual endpoint may require parameters like region, category, etc.
            # This is a placeholder structure - actual API may differ
            params = {
                "limit": limit,
                "period": "7d",  # Last 7 days
            }

            response = await self.client.get(
                self.TRENDING_KEYWORDS_URL,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await retry_async(
                _fetch,
                max_attempts=3,
                delay=1.0,
                exceptions=(
                    httpx.HTTPError,
                    httpx.TimeoutException,
                    httpx.NetworkError,
                ),
            )

            keywords = self._extract_keywords_from_response(data)
            logger.info(f"Fetched {len(keywords)} trending keywords")
            return keywords

        except Exception as e:
            logger.error(f"Error fetching trending keywords after retries: {e}")
            return []

    async def fetch_trending_hashtags(self, limit: int = 100) -> List[str]:
        """
        Fetch trending hashtags from TikTok Creative Center.

        Args:
            limit: Maximum number of hashtags to fetch

        Returns:
            List of hashtag strings (without #)
        """

        async def _fetch():
            params = {
                "limit": limit,
                "period": "7d",
            }

            response = await self.client.get(
                self.TRENDING_HASHTAGS_URL,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await retry_async(
                _fetch,
                max_attempts=3,
                delay=1.0,
                exceptions=(
                    httpx.HTTPError,
                    httpx.TimeoutException,
                    httpx.NetworkError,
                ),
            )

            hashtags = self._extract_hashtags_from_response(data)
            logger.info(f"Fetched {len(hashtags)} trending hashtags")
            return hashtags

        except Exception as e:
            logger.error(f"Error fetching trending hashtags after retries: {e}")
            return []

    async def fetch_trending_sounds(self, limit: int = 100) -> List[str]:
        """
        Fetch trending sound names from TikTok Creative Center.

        Args:
            limit: Maximum number of sounds to fetch

        Returns:
            List of sound name strings
        """

        async def _fetch():
            params = {
                "limit": limit,
                "period": "7d",
            }

            response = await self.client.get(
                self.TRENDING_SOUNDS_URL,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await retry_async(
                _fetch,
                max_attempts=3,
                delay=1.0,
                exceptions=(
                    httpx.HTTPError,
                    httpx.TimeoutException,
                    httpx.NetworkError,
                ),
            )

            sounds = self._extract_sounds_from_response(data)
            logger.info(f"Fetched {len(sounds)} trending sounds")
            return sounds

        except Exception as e:
            logger.error(f"Error fetching trending sounds after retries: {e}")
            return []

    async def fetch_all_trending(self, limit_per_source: int = 100) -> List[str]:
        """
        Fetch all trending keywords from all sources.

        Args:
            limit_per_source: Maximum number of items per source

        Returns:
            Combined and deduplicated list of keywords
        """
        logger.info("Fetching all trending keywords from TikTok Creative Center")

        # Fetch from all sources concurrently
        keywords, hashtags, sounds = await asyncio.gather(
            self.fetch_trending_keywords(limit_per_source),
            self.fetch_trending_hashtags(limit_per_source),
            self.fetch_trending_sounds(limit_per_source),
            return_exceptions=True,
        )

        # Handle exceptions
        if isinstance(keywords, Exception):
            logger.error(f"Error fetching keywords: {keywords}")
            keywords = []
        if isinstance(hashtags, Exception):
            logger.error(f"Error fetching hashtags: {hashtags}")
            hashtags = []
        if isinstance(sounds, Exception):
            logger.error(f"Error fetching sounds: {sounds}")
            sounds = []

        # Combine all sources
        all_keywords = keywords + hashtags + sounds

        # Normalize and deduplicate
        normalized = normalize_keywords_util(all_keywords)
        unique_keywords = deduplicate_keywords(normalized)

        logger.info(
            f"Total unique keywords after normalization: {len(unique_keywords)}"
        )
        return unique_keywords

    def _extract_keywords_from_response(self, data: dict) -> List[str]:
        """
        Extract keywords from API response.

        This method needs to be adapted based on actual API response structure.
        """
        keywords = []

        # Placeholder: Actual structure depends on TikTok API response
        # Common patterns:
        # - data['list'] or data['data']['list']
        # - Each item may have 'keyword', 'name', 'text', etc.

        if isinstance(data, dict):
            items = data.get("data", {}).get("list", []) or data.get("list", [])
            for item in items:
                if isinstance(item, dict):
                    keyword = (
                        item.get("keyword") or item.get("name") or item.get("text")
                    )
                    if keyword:
                        keywords.append(str(keyword))
                elif isinstance(item, str):
                    keywords.append(item)

        return keywords

    def _extract_hashtags_from_response(self, data: dict) -> List[str]:
        """Extract hashtags from API response."""
        hashtags = []

        if isinstance(data, dict):
            items = data.get("data", {}).get("list", []) or data.get("list", [])
            for item in items:
                if isinstance(item, dict):
                    hashtag = (
                        item.get("hashtag") or item.get("name") or item.get("text")
                    )
                    if hashtag:
                        # Remove # if present
                        hashtag = str(hashtag).lstrip("#")
                        hashtags.append(hashtag)
                elif isinstance(item, str):
                    hashtag = str(item).lstrip("#")
                    hashtags.append(hashtag)

        return hashtags

    def _extract_sounds_from_response(self, data: dict) -> List[str]:
        """Extract sound names from API response."""
        sounds = []

        if isinstance(data, dict):
            items = data.get("data", {}).get("list", []) or data.get("list", [])
            for item in items:
                if isinstance(item, dict):
                    sound = (
                        item.get("sound_name") or item.get("name") or item.get("title")
                    )
                    if sound:
                        sounds.append(str(sound))
                elif isinstance(item, str):
                    sounds.append(str(item))

        return sounds


async def save_keywords_to_database(db: Session, keywords: List[str]) -> int:
    """
    Save keywords to database, creating new entries for keywords that don't exist.

    Args:
        db: Database session
        keywords: List of keyword strings

    Returns:
        Number of new keywords created
    """
    return KeywordService.bulk_create_keywords(db, keywords)
