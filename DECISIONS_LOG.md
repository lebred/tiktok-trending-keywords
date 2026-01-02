# Design Decisions Log

## 2024 - Repository Initialization

### Decision: Documentation Structure

**Date**: [Current Date]
**Context**: Setting up project documentation
**Decision**: Created separate files for different concerns:

- `PROJECT_STATE.md` - Current status (editable, not append-only)
- `BUILD_SPEC.md` - Technical specifications
- `TODO.md` - Task tracking
- `CURSOR_LOG.md` - Session logs (append-only)
- `DECISIONS_LOG.md` - This file (append-only)

**Rationale**:

- Separates concerns for easier maintenance
- PROJECT_STATE.md should be edited to reflect current state, not appended
- Logs should be append-only for history tracking

**Alternatives Considered**: Single documentation file (rejected - too unwieldy)

---

### Decision: Database Model Design

**Date**: [Current Date]
**Context**: Designing database schema for keyword tracking and user management
**Decision**:

- Created BaseModel abstract class with common fields (id, created_at, updated_at)
- Used SQLAlchemy ORM with declarative base
- Implemented relationships with proper cascade behavior
- Used JSON column for flexible Google Trends data storage
- Added unique constraints and indexes for performance

**Rationale**:

- BaseModel reduces code duplication and ensures consistent timestamp management
- SQLAlchemy ORM provides type safety and easy querying
- Cascade deletes ensure data integrity (e.g., deleting keyword deletes snapshots)
- JSON column allows storing variable Google Trends data without schema changes
- Unique constraints prevent duplicate data (keywords, emails, daily snapshots)
- Indexes on foreign keys and frequently queried fields improve query performance

**Alternatives Considered**:

- Raw SQL (rejected - less maintainable, no type safety)
- Separate timestamp fields per model (rejected - code duplication)
- Separate table for Google Trends data (rejected - unnecessary complexity for MVP)

---

### Decision: TikTok Ingestion Service Architecture

**Date**: [Current Date]
**Context**: Implementing TikTok keyword ingestion with unknown API endpoints
**Decision**:

- Created flexible service with placeholder endpoints
- Implemented async HTTP client with retry logic
- Separated keyword processing utilities from ingestion logic
- Used placeholder API structure that can be easily updated
- Created separate KeywordService for database operations

**Rationale**:

- Placeholder endpoints allow development to proceed while API is researched
- Async client provides better performance for concurrent requests
- Retry logic handles transient network failures gracefully
- Separation of concerns: ingestion vs. processing vs. persistence
- Flexible response parsing can adapt to actual API structure
- Bulk database operations improve performance for large keyword lists

**Alternatives Considered**:

- Wait for API documentation (rejected - blocks development)
- Use web scraping (rejected - violates "no UI automation" constraint)
- Use third-party API (rejected - adds dependency and cost)
- Synchronous requests (rejected - slower, less efficient)

**Risks**:

- API endpoints may be incorrect and need updating
- Response structure may differ from assumptions
- Authentication may be required
- Rate limiting may need additional handling

---

### Decision: Google Trends Caching Strategy

**Date**: [Current Date]
**Context**: Implementing caching for Google Trends data to minimize API calls
**Decision**:

- Use database-based caching (DailySnapshot.google_trends_data JSON field)
- Cache duration: 7 days default (configurable)
- Store trends data as JSON in existing snapshot model
- Separate cache management service (TrendsCache)

**Rationale**:

- Database caching avoids external cache dependencies (Redis, etc.)
- JSON field in DailySnapshot already designed for this purpose
- 7-day cache balances freshness with API call reduction
- Reuses existing model structure (no new tables)
- Cache can be invalidated manually if needed
- Historical data preserved in snapshots

**Alternatives Considered**:

- Redis caching (rejected - adds infrastructure dependency for MVP)
- In-memory caching (rejected - lost on restart, not shared across processes)
- No caching (rejected - too many API calls, rate limiting issues)
- Separate trends_cache table (rejected - unnecessary complexity)

**Trade-offs**:

- Database queries for cache lookups (acceptable for MVP scale)
- JSON storage less queryable than normalized tables (acceptable for trends data)
- Cache invalidation requires manual management (acceptable for daily batch processing)

---

### Decision: Scoring Algorithm Implementation

**Date**: [Current Date]
**Context**: Implementing deterministic momentum scoring algorithm
**Decision**:

- Exact implementation of BUILD_SPEC.md formulas
- Used numpy for slope calculation (linear regression)
- Implemented percentile rank manually (no external library)
- Minimum 28 weeks of data required (7 + 21 weeks)
- Edge case handling for insufficient data, division by zero, overflow

**Rationale**:

- Deterministic scoring required by spec (no AI, reproducible)
- numpy provides efficient linear regression for slope calculation
- Manual percentile rank keeps dependencies minimal
- 28 weeks minimum ensures all metrics can be calculated
- Edge cases prevent crashes and provide graceful degradation

**Alternatives Considered**:

- scipy for statistics (rejected - adds large dependency for simple calculations)
- pandas for data manipulation (rejected - numpy sufficient, already used)
- Different minimum data requirement (rejected - need 7+21 weeks minimum)
- Skip edge case handling (rejected - would cause crashes on real data)

**Implementation Details**:

- Slope: Linear regression formula: m = (n*Σxy - Σx*Σy) / (n\*Σx² - (Σx)²)
- Percentile rank: (count_below + 0.5\*count_equal) / total
- Final score: Sigmoid function with clamping to [1, 100]
- All calculations match BUILD_SPEC.md exactly

---

### Decision: Daily Automation Architecture

**Date**: [Current Date]
**Context**: Implementing daily automation pipeline for scheduled execution
**Decision**:

- Used APScheduler with BackgroundScheduler
- Scheduled for 2 AM UTC daily
- Pipeline orchestration service separates concerns
- Error handling at each step (partial failures don't crash pipeline)
- Scheduler disabled in debug mode
- MemoryJobStore for simplicity (MVP scale)

**Rationale**:

- APScheduler is Python-native and integrates well with FastAPI
- BackgroundScheduler runs in separate thread, doesn't block main app
- 2 AM UTC chosen to avoid peak hours and ensure data freshness
- Separate pipeline service allows manual execution and testing
- Graceful error handling ensures pipeline completes even with partial failures
- Debug mode disable prevents scheduler conflicts during development
- MemoryJobStore sufficient for MVP (can upgrade to database store later)

**Alternatives Considered**:

- Cron jobs (rejected - requires system-level configuration, less portable)
- Celery (rejected - overengineering for MVP, adds Redis dependency)
- Database job store (rejected - MemoryJobStore sufficient for MVP)
- Different schedule time (rejected - 2 AM UTC is reasonable default)

**Trade-offs**:

- MemoryJobStore loses jobs on restart (acceptable - jobs are idempotent)
- Single scheduler instance (acceptable - can scale horizontally later)
- No distributed locking (acceptable - single instance deployment for MVP)

---

### Decision: SQLite for MVP Deployment

**Date**: [Current Date]
**Context**: Reducing deployment costs and complexity for MVP launch
**Decision**:
- Use SQLite as default database for MVP
- Support both SQLite and PostgreSQL (switch via DATABASE_URL)
- Simple daily backups to DigitalOcean Spaces
- Provide migration script for PostgreSQL when needed

**Rationale**:
- Zero database costs ($0 vs $15/month for managed PostgreSQL)
- Perfect for single-server deployment (MVP scale)
- No connection management complexity
- Easy backups (just copy the file)
- SQLAlchemy abstracts database differences
- Can migrate to PostgreSQL later without code changes
- Saves $120/year during MVP phase

**Alternatives Considered**:
- Start with PostgreSQL (rejected - unnecessary cost for MVP)
- Use Supabase/Neon free tier (rejected - adds complexity, may hit limits)
- Use managed PostgreSQL from day one (rejected - premature optimization)

**Trade-offs**:
- SQLite doesn't handle concurrent writes well (acceptable - single server, daily batch)
- No advanced features (acceptable - not needed for MVP)
- Migration required later (acceptable - script provided, easy process)

**Migration Strategy**:
- Script provided: `migrate_from_sqlite_to_postgres.py`
- Zero-downtime migration possible
- All data preserved
- No code changes required

---
