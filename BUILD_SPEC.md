# BUILD SPECIFICATION

## Project: TikTok Keyword Momentum Tracker

### Purpose
Identify newly emerging TikTok keywords that show strong short-term momentum when cross-validated with Google Trends data.

### Core Value Proposition
Surface keywords that:
- Were historically low or near-zero
- Have begun accelerating sharply in the past days or weeks
- Are likely early indicators of viral trends

### Technical Stack

#### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI (recommended) or Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (recommended)
- **Scheduler**: APScheduler or cron
- **HTTP Client**: httpx or requests
- **Google Trends**: pytrends library

#### Frontend
- **Framework**: Next.js (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (recommended)
- **Auth**: NextAuth.js or similar
- **Payment**: Stripe integration

#### Infrastructure
- **Deployment**: DigitalOcean
- **Database Hosting**: DigitalOcean Managed PostgreSQL
- **Version Control**: Private GitHub repository

### Data Sources

#### TikTok Creative Center
- Trending keywords
- Trending hashtags
- Trending sounds
- **Method**: HTTP requests to public endpoints (no authentication, no UI automation)

#### Google Trends
- Worldwide search interest
- Past 12 months of data
- Weekly granularity
- **Library**: pytrends
- **Caching**: Required to minimize API calls

### Scoring Algorithm

#### Input
- Weekly Google Trends values for each keyword
- Historical baseline periods

#### Metrics Calculation

1. **Lift**
   ```
   lift = (avg(last_7) - avg(prev_21)) / (avg(prev_21) + 0.01)
   ```
   - Compares recent 7-day average to previous 21-day average
   - Normalized by baseline to handle scale differences

2. **Acceleration**
   ```
   acceleration = slope(last_7) - slope(prev_21)
   ```
   - Rate of change in recent period vs previous period
   - Positive = accelerating upward

3. **Novelty**
   ```
   novelty = 1 - percentile_rank(avg(prev_90))
   ```
   - Rewards keywords with historically low baselines
   - Higher novelty = lower historical average

4. **Noise**
   ```
   noise = stdev(last_7) / (avg(last_7) + 0.01)
   ```
   - Penalizes volatile spikes
   - Coefficient of variation for recent period

#### Score Calculation

**Raw Score:**
```
raw = 0.45*lift + 0.35*acceleration + 0.25*novelty - 0.25*noise
```

**Final Score:**
```
score = int(100 / (1 + exp(-raw)))
```
Clamp to [1, 100]

**Weight Distribution:**
- Lift: 45% (strongest signal)
- Acceleration: 35% (momentum indicator)
- Novelt: 25% (emerging trend bonus)
- Noise: -25% (volatility penalty)

### Database Schema (Planned)

#### Tables
1. **keywords**
   - id (PK)
   - keyword (unique)
   - created_at
   - updated_at

2. **daily_snapshots**
   - id (PK)
   - keyword_id (FK)
   - snapshot_date
   - momentum_score (1-100)
   - raw_score
   - lift_value
   - acceleration_value
   - novelty_value
   - noise_value
   - google_trends_data (JSON)
   - created_at

3. **users**
   - id (PK)
   - email (unique)
   - subscription_tier (free/paid)
   - stripe_customer_id
   - created_at
   - updated_at

4. **subscriptions**
   - id (PK)
   - user_id (FK)
   - stripe_subscription_id
   - status
   - current_period_end
   - created_at
   - updated_at

### API Endpoints (Planned)

#### Public
- `GET /api/keywords` - List top keywords (limited for free users)
- `GET /api/keywords/:id` - Keyword details
- `GET /api/keywords/:id/history` - Score history

#### Authenticated
- `GET /api/keywords/full` - Full keyword list (paid users)
- `GET /api/archive/:date` - Historical snapshot

#### Auth
- `POST /api/auth/login` - Request magic link
- `POST /api/auth/verify` - Verify magic link token
- `POST /api/auth/logout` - Logout

#### Stripe
- `POST /api/stripe/create-checkout` - Create subscription checkout
- `POST /api/stripe/webhook` - Handle Stripe webhooks

### Frontend Pages

1. **Homepage** (`/`)
   - Daily ranked list of hottest keywords
   - Momentum scores
   - Free users: Top 10
   - Paid users: Full list with filters

2. **Archive** (`/archive`)
   - Historical daily snapshots
   - Date picker
   - Keyword search

3. **Keyword Detail** (`/keywords/:id`)
   - Score history chart
   - Score breakdown (lift, acceleration, novelty, noise)
   - Google Trends visualization
   - Explanation of score

4. **Auth Pages**
   - `/login` - Email input for magic link
   - `/verify` - Token verification
   - `/dashboard` - User account and subscription

### Automation

#### Daily Pipeline
1. Fetch trending keywords from TikTok Creative Center
2. Normalize and deduplicate keywords
3. For each keyword:
   - Fetch Google Trends data (with caching)
   - Calculate momentum score
   - Store snapshot
4. Update rankings
5. Send notifications (optional, future)

#### Error Handling
- Partial failures should not crash the system
- Log all errors
- Retry logic for external API calls
- Graceful degradation

### Constraints

#### Forbidden
- UI automation
- App emulation
- Headless browsers
- Non-deterministic AI scoring
- Real-time systems
- Overengineering

#### Required
- Deterministic scoring
- Reproducible results
- Caching for external APIs
- Daily batch processing

### Implementation Order

1. ✅ Repository structure and documentation
2. Backend data models and DB schema
3. TikTok trend ingestion
4. Google Trends fetch + caching
5. Scoring algorithm
6. Daily automation
7. Frontend pages
8. Auth and Stripe
9. Final documentation pass

### Deployment Checklist

- [ ] PostgreSQL database setup
- [ ] Environment variables configuration
- [ ] Backend deployment
- [ ] Frontend deployment
- [ ] Cron job / scheduler setup
- [ ] Stripe webhook endpoint
- [ ] Monitoring and logging
- [ ] Backup strategy

