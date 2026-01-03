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
- No schema changes needed (using portable types)

**Implementation Details**:

- SQLite engine uses StaticPool for single-file databases
- Foreign keys enabled via PRAGMA on every connection
- Backup uses SQLite online backup API (safe during writes)
- WAL checkpoint before backup for consistency
- Backup verification included
- All schema types are portable (Integer, String, Float, Date, DateTime, JSON)
- No database-specific features used (UUID functions, JSONB, etc.)

**Documentation**:

- Created `DATABASE_PORTABILITY.md` to track portability requirements
- Updated deployment docs with accurate cost estimates
- Clarified "no code changes" to "no schema changes" (more accurate)

---

### Decision: Static Frontend Export

**Date**: [Current Date]
**Context**: Simplifying production deployment by eliminating Node.js server requirement
**Decision**:

- Convert Next.js frontend to fully static export
- Remove Node.js server dependency in production
- Serve static files directly via Nginx
- All data fetching happens client-side from FastAPI backend

**Rationale**:

- **Simpler Deployment**: No need to run Node.js server, manage PM2/systemd, or handle Node.js process restarts
- **Lower Resource Usage**: Static files require minimal server resources (just file serving)
- **Better Performance**: Static files can be cached aggressively, served from CDN
- **Easier Scaling**: Static files can be served from any web server or CDN
- **Cost Effective**: No Node.js runtime overhead on Droplet
- **Security**: Fewer moving parts, no Node.js vulnerabilities to patch
- **Compatibility**: Works with any static file server (Nginx, Apache, CDN)

**Implementation**:

- Changed `next.config.js` to `output: 'export'`
- Converted server components to client components
- All data fetching moved to `useEffect` hooks
- Build produces `out/` directory with static files
- Removed `next start` script (not needed)

**Trade-offs**:

- **SEO**: Slightly reduced (no server-side rendering), but acceptable for MVP
- **Initial Load**: Data fetched after page load (adds loading states)
- **Dynamic Routes**: Must be handled client-side (acceptable for this use case)

**Alternatives Considered**:

- Keep Next.js server (rejected - adds complexity and resource usage)
- Use Vercel/Netlify (rejected - want full control, using DigitalOcean)
- Pre-render all pages (rejected - dynamic keyword IDs unknown at build time)

**Migration Path**:

- If SEO becomes critical, can add ISR (Incremental Static Regeneration) later
- Can pre-render top keywords at build time if needed
- Current approach is optimal for MVP scale

---

### Decision: Google Trends Cache Table for Static Pages

**Date**: [Current Date]
**Context**: Need to generate static public pages for keywords using only Google Trends data (no TikTok details)
**Decision**:

- Create dedicated `google_trends_cache` table separate from `daily_snapshots`
- Store full time series data (weekly values) as JSON
- Add keyword metadata fields (keyword_type, first_seen, last_seen) to keywords table
- Support multiple geo/timeframe combinations per keyword

**Rationale**:

- **Separation of Concerns**: Public pages only need Google Trends data, not TikTok-specific metrics
- **Performance**: Dedicated cache table enables fast queries for static page generation
- **Flexibility**: Can store multiple geo/timeframe combinations for future features
- **Data Structure**: JSON storage matches pytrends output format exactly
- **Clean API**: Public pages can query cache table directly without joining snapshots

**Schema Design**:

- `google_trends_cache` table with (keyword_id, geo, timeframe) unique constraint
- `time_series_data` JSON column stores full weekly time series
- `keywords` table enhanced with metadata fields for public display
- All types are portable (String, Date, Integer, JSON)

**Alternatives Considered**:

- Reuse daily_snapshots.google_trends_data (rejected - mixes TikTok metrics with public data)
- Store in separate JSON files (rejected - database is more reliable and queryable)
- Single cache entry per keyword (rejected - need geo/timeframe flexibility)

**Migration Strategy**:

- Portable migration handles both SQLite and PostgreSQL
- Existing keywords get default keyword_type='keyword'
- Cache table can be populated independently of daily pipeline

---

### Decision: Static Public Page Generation and Deployment

**Date**: [Current Date]
**Context**: Generate static public pages for keywords using only Google Trends data, integrated into daily automation
**Decision**:

- Generate static HTML pages after daily scoring completes
- Use atomic swap deployment to avoid partial updates
- Separate temp directory for generation, then swap to public directory
- Public pages contain only Google Trends data (no TikTok details)

**Rationale**:

- **Public-Facing Content**: Enables SEO-friendly public pages without exposing TikTok data
- **Atomic Deployment**: Prevents serving partial/corrupted pages during generation
- **Automation**: Integrated into daily pipeline for automatic updates
- **Separation**: Public pages separate from authenticated app frontend
- **Performance**: Static HTML can be cached aggressively, served from CDN

**Implementation**:

- `build_public_pages.py` script generates HTML from database
- Generates to temp directory first
- `deploy_public_pages.py` performs atomic swap
- Integrated as Step 5 in daily pipeline
- Manual deployment step (or cron job)

**Deployment Process**:

1. Generate to temp directory (`public_tmp`)
2. Backup current public directory (`public_prev`)
3. Move temp to public (atomic swap)
4. Remove backup
5. Set ownership and permissions

**Trade-offs**:

- **Manual Deployment**: Requires separate step or cron job (acceptable - can be automated)
- **Storage**: Duplicate pages in temp and public (acceptable - small size)
- **CDN**: Static files can be served from CDN (future optimization)

**Alternatives Considered**:

- Generate directly to public directory (rejected - risk of partial updates)
- Use Next.js static export (rejected - want simple HTML, no build complexity)
- Serve from database dynamically (rejected - want static files for performance/CDN)

**Security**:

- Public pages contain only Google Trends data
- No TikTok-specific metrics exposed
- No authentication required
- Can be served from separate domain/subdomain

---

### Decision: Production Nginx Configuration and CORS Security

**Date**: [Current Date]
**Context**: Setting up production-ready Nginx configuration and securing backend API with proper CORS
**Decision**:

- Create production Nginx config file in repository
- Serve public pages from root (`/`)
- Proxy API requests from `/api/*` to FastAPI backend
- Configure CORS dynamically based on environment (debug mode)
- Add `/api/health` endpoint for monitoring

**Rationale**:

- **Repository Config**: Keeps production config version-controlled and documented
- **Root Public Pages**: SEO-friendly URLs (trendearly.xyz/keywords/123/)
- **API Proxy**: Standard `/api/*` pattern for API routes
- **Dynamic CORS**: Automatically adjusts for dev vs production
- **Health Endpoint**: Needed for monitoring and load balancer health checks

**Nginx Configuration**:

- Serves static public pages from `/var/www/trendearly/public`
- Reverse proxy `/api/*` to `http://127.0.0.1:8000`
- Gzip compression for text-based files
- Caching: Static assets (1y), HTML (1h), API (no cache)
- Basic security headers (X-Frame-Options, X-Content-Type-Options)
- SSL-ready (commented block for certbot)

**CORS Strategy**:

- **Development**: Allow localhost:3000 for development
- **Production**: Restrict to trendearly.xyz and www.trendearly.xyz
- **Dynamic**: Uses `settings.debug` to determine environment
- **Credentials**: Enabled for authentication cookies

**Health Endpoints**:

- `/api/health`: Primary endpoint for monitoring
- `/health`: Legacy endpoint (backward compatibility)

**Alternatives Considered**:

- Separate Nginx config per environment (rejected - single config with comments is simpler)
- Wildcard CORS in production (rejected - security risk)
- No health endpoint (rejected - needed for monitoring)
- Serve API directly (rejected - Nginx provides better security and caching)

**Security Considerations**:

- CORS restricted to actual domain in production
- Security headers prevent common attacks
- Hidden files denied access
- SSL ready for HTTPS enforcement

**Trade-offs**:

- **Single Config**: Works for both HTTP and HTTPS (with certbot modifications)
- **Basic Security Headers**: Sufficient for MVP, can add more later
- **Health Endpoint**: Simple JSON response (can add DB checks later)

---

### Decision: Public Pages Verification and Automated Checks

**Date**: [Current Date]
**Context**: Need to verify public pages are generated correctly and contain no TikTok mentions
**Decision**:

- Create comprehensive verification documentation
- Implement automated script to check for forbidden words
- Add public pages section to deployment docs
- Include troubleshooting and monitoring guidance

**Rationale**:

- **Documentation**: Step-by-step guide ensures consistent verification process
- **Automated Checks**: Prevents human error, catches violations before deployment
- **Deployment Docs**: Centralizes all public pages information in one place
- **Troubleshooting**: Reduces support burden, helps diagnose issues quickly

**Verification Guide**:

- Covers full workflow: migrations → ingestion → generation → inspection
- Includes both manual and automated checks
- Provides troubleshooting for common issues
- Links to related documentation

**Automated Check Script**:

- Scans all HTML files recursively
- Checks for comprehensive list of forbidden words
- Reports violations with file and line numbers
- Exits with error code for CI/CD integration

**Forbidden Words List**:

- "tiktok" (all cases)
- "Creative Center"
- "hashtag trend"
- "trending hashtag/sound"
- TikTok URLs (ads.tiktok.com, tiktok.com)

**Deployment Documentation**:

- File locations (production, temp, backup)
- Nginx mapping and URL structure
- Cron and systemd timer setup
- Troubleshooting common issues
- Monitoring recommendations

**Alternatives Considered**:

- Manual verification only (rejected - error-prone, not scalable)
- Simple grep check (rejected - less informative, harder to maintain)
- Separate verification repo (rejected - adds complexity)

**Trade-offs**:

- **Comprehensive List**: May need updates as new terms emerge (acceptable - easy to extend)
- **Manual Inspection**: Still recommended alongside automated checks (acceptable - catches edge cases)
- **Sitemap/Robots**: Optional for now (acceptable - can add later)

**Integration Points**:

- Can be run before deployment
- Can be integrated into CI/CD pipeline
- Can be scheduled as part of daily pipeline
- Can be used for monitoring/alerting

---

### Decision: Consolidate Deployment Documentation

**Date**: [Current Date]
**Context**: Two deployment guides (DEPLOYMENT.md and MVP_DEPLOYMENT.md) with significant overlap causing maintenance burden and confusion
**Decision**:
- Consolidate both files into a single DEPLOYMENT.md
- Structure with "Quick Start: MVP" at top for fast deployment
- Include comprehensive sections for both MVP and Production
- Delete MVP_DEPLOYMENT.md after consolidation

**Rationale**:
- **Single Source of Truth**: Eliminates confusion about which guide to follow
- **Reduced Maintenance**: Updates only needed in one place
- **Better Organization**: Clear structure with Quick Start for MVP users
- **Complete Coverage**: All information preserved, nothing lost
- **Easier Navigation**: One comprehensive guide with clear sections

**Structure**:
- Quick Start: MVP section at top (streamlined, fast path)
- Detailed MVP Deployment Steps (complete instructions)
- Production Deployment section (App Platform + PostgreSQL)
- Shared sections (Environment Variables, Stripe, Monitoring, etc.)
- Public Pages section fully integrated
- All troubleshooting and maintenance preserved

**Alternatives Considered**:
- Keep both files with cross-references (rejected - still causes confusion)
- Make MVP_DEPLOYMENT.md a short "Quick Start" linking to DEPLOYMENT.md (rejected - adds complexity)
- Split by deployment method instead (rejected - MVP vs Production is clearer distinction)

**Trade-offs**:
- **Longer File**: Single file is longer (~900 lines) but well-organized (acceptable)
- **Quick Start**: MVP users can skip to Quick Start section (good UX)
- **Completeness**: All information preserved, nothing lost (good)

**Migration**:
- Updated all references in documentation
- Deleted MVP_DEPLOYMENT.md
- Verified all content preserved in consolidated file

---
