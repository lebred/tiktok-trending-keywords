# TikTok Ingestion Service

## Overview

The TikTok ingestion service fetches trending keywords, hashtags, and sounds from TikTok Creative Center using HTTP requests (no UI automation).

## API Endpoints

**Note**: The actual TikTok Creative Center API endpoints may differ from the placeholders in the code. These need to be verified and updated based on:

1. Actual TikTok Creative Center API documentation
2. Network inspection of the Creative Center web interface
3. Public API availability

### Current Placeholder Endpoints

- Keywords: `https://ads.tiktok.com/creative_radar_api/v1/popular_trend/keyword/list`
- Hashtags: `https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list`
- Sounds: `https://ads.tiktok.com/creative_radar_api/v1/popular_trend/sound/list`

### Research Required

1. **Authentication**: Does the API require authentication tokens?
2. **Parameters**: What parameters are needed? (region, category, time period, etc.)
3. **Response Format**: What is the actual JSON response structure?
4. **Rate Limits**: Are there rate limits or request throttling?
5. **CORS**: Are the endpoints accessible from server-side requests?

### Alternative Approaches

If direct API access is not available:

1. **Web Scraping**: Parse HTML from public Creative Center pages (respecting robots.txt)
2. **RSS/Feed**: Check if TikTok provides RSS feeds or data exports
3. **Official API**: Check TikTok Marketing API or Business API documentation
4. **Third-party APIs**: Consider using third-party services that aggregate TikTok trends

## Usage

```python
from app.services.tiktok_ingestion import TikTokIngestionService, save_keywords_to_database
from app.database import SessionLocal

# Create service
service = TikTokIngestionService()

# Fetch trending keywords
keywords = await service.fetch_all_trending(limit_per_source=100)

# Save to database
db = SessionLocal()
created_count = await save_keywords_to_database(db, keywords)
db.close()

# Cleanup
await service.close()
```

## Features

- ✅ Async HTTP client with httpx
- ✅ Retry logic with exponential backoff
- ✅ Keyword normalization and deduplication
- ✅ Error handling and logging
- ✅ Bulk database operations
- ✅ Concurrent fetching from multiple sources

## Testing

Run the test script:

```bash
python -m scripts.fetch_trending_keywords
```

## Next Steps

1. Research actual TikTok Creative Center API endpoints
2. Update endpoint URLs and parameters
3. Update response parsing based on actual API structure
4. Add authentication if required
5. Implement rate limiting if needed
6. Write comprehensive tests

