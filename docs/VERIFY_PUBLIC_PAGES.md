# Public Pages Verification Guide

This guide walks through verifying that public pages are generated correctly and contain only Google Trends data (no TikTok mentions).

## Prerequisites

- Python 3.11+ with virtual environment activated
- Database initialized (SQLite or PostgreSQL)
- Backend dependencies installed

## Step 1: Run Database Migrations

Ensure your database schema is up to date:

```bash
cd backend
source venv/bin/activate  # If using virtual environment

# Run migrations
python -m scripts.migrate upgrade head

# Or using alembic directly
alembic upgrade head
```

**Expected Output:**

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_add_keyword_fields, add keyword fields and google trends cache
```

**Verify:**

```bash
# Check that tables exist (SQLite)
sqlite3 data.db ".tables"
# Should show: alembic_version, daily_snapshots, google_trends_cache, keywords, subscriptions, users
```

## Step 2: Ingest Sample Data

### Option A: Fetch Real Keywords (if TikTok API is configured)

```bash
cd backend
source venv/bin/activate

# Fetch trending keywords
python -m scripts.fetch_trending_keywords
```

**Expected Output:**

```
INFO  Starting TikTok keyword ingestion
INFO  Fetched X unique keywords
INFO  Successfully saved Y new keywords to database
```

### Option B: Run Full Pipeline (Recommended)

This will fetch keywords, get Google Trends data, and calculate scores:

```bash
cd backend
source venv/bin/activate

# Run pipeline with limited keywords for testing
python -m scripts.run_daily_pipeline --max-keywords 5
```

**Expected Output:**

```
Pipeline Execution Results
============================================================
Snapshot Date: 2024-01-15
Duration: XX.XX seconds
Keywords Fetched: X
Keywords Saved: Y
Scores Calculated: Z
Scores Failed: 0
Success: True
============================================================
```

**Verify Data in Database:**

```bash
# Check keywords
sqlite3 data.db "SELECT COUNT(*) FROM keywords;"

# Check snapshots
sqlite3 data.db "SELECT COUNT(*) FROM daily_snapshots;"

# Check Google Trends cache
sqlite3 data.db "SELECT COUNT(*) FROM google_trends_cache;"
```

## Step 3: Generate Public Pages

Generate static HTML pages from the database:

```bash
cd backend
source venv/bin/activate

# Generate to a test directory
python -m scripts.build_public_pages \
  --out ./public_test \
  --date $(date +%Y-%m-%d)  # Or use specific date: --date 2024-01-15
```

**Expected Output:**

```
INFO  Generating public pages to: ./public_test
INFO  Using snapshot date: 2024-01-15
INFO  Found X keywords with snapshots
INFO  Generated page for keyword: example_keyword -> ./public_test/keywords/1/index.html
...
INFO  Generated index page: ./public_test/index.html
INFO  Successfully generated X keyword pages + index
```

**Verify Output Structure:**

```bash
# Check directory structure
ls -la public_test/
# Should show: index.html, keywords/

ls -la public_test/keywords/
# Should show numbered directories (1/, 2/, etc.)

ls -la public_test/keywords/1/
# Should show: index.html
```

## Step 4: Inspect Generated Pages

### Check Index Page

```bash
# View index page
cat public_test/index.html | head -50

# Or open in browser
open public_test/index.html  # macOS
xdg-open public_test/index.html  # Linux
```

**What to Look For:**

- ✅ Page title: "TrendEarly - Trending Keywords"
- ✅ List of keywords with scores
- ✅ Links to `/keywords/{id}/`
- ✅ Footer mentions "Data source: Google Trends"
- ❌ **NO mentions of "TikTok", "Creative Center", "hashtag", etc.**

### Check Keyword Detail Page

```bash
# View a keyword page
cat public_test/keywords/1/index.html | head -100

# Or open in browser
open public_test/keywords/1/index.html
```

**What to Look For:**

- ✅ Keyword name displayed
- ✅ Momentum score (1-100)
- ✅ Metrics: Lift, Acceleration, Novelty, Noise
- ✅ Google Trends chart (if data available)
- ✅ Last updated date
- ✅ Footer mentions "Data source: Google Trends"
- ❌ **NO mentions of TikTok, Creative Center, or TikTok-specific terms**

## Step 5: Run Automated Check

Use the automated script to scan for forbidden words:

```bash
cd backend
source venv/bin/activate

# Run the check script
python -m scripts.check_public_pages_no_tiktok ./public_test
```

**Expected Output (Success):**

```
INFO  Scanning public pages in: ./public_test
INFO  Checking index.html
INFO  Checking keywords/1/index.html
...
INFO  ✓ All pages passed: No TikTok mentions found
```

**Expected Output (Failure):**

```
ERROR  Found forbidden word in keywords/1/index.html: "TikTok"
ERROR  ✗ Check failed: Found 1 forbidden word(s)
```

## Step 6: Verify Sitemap and Robots.txt

### Check for Sitemap

```bash
# Check if sitemap exists (optional - may not be generated yet)
ls -la public_test/sitemap.xml

# If exists, verify format
cat public_test/sitemap.xml
```

**Note:** Sitemap generation is optional. If not present, it can be added later.

### Check for Robots.txt

```bash
# Check if robots.txt exists (optional)
ls -la public_test/robots.txt

# If exists, verify content
cat public_test/robots.txt
```

**Expected Content (if exists):**

```
User-agent: *
Allow: /
Sitemap: https://trendearly.xyz/sitemap.xml
```

**Note:** Robots.txt generation is optional. If not present, it can be added later.

## Step 7: Full Verification Checklist

Run through this checklist to ensure everything is correct:

- [ ] Database migrations ran successfully
- [ ] Sample data ingested (keywords, snapshots, trends cache)
- [ ] Public pages generated without errors
- [ ] Index page exists and displays keywords
- [ ] Keyword detail pages exist and display data
- [ ] No TikTok mentions in any HTML files
- [ ] Google Trends data displayed correctly
- [ ] Charts render (if Chart.js loads correctly)
- [ ] All links work (index → keyword pages)
- [ ] Footer shows "Data source: Google Trends"
- [ ] Automated check script passes

## Troubleshooting

### No Keywords Generated

**Problem:** `INFO  Found 0 keywords with snapshots`

**Solutions:**

1. Run the daily pipeline to create snapshots:
   ```bash
   python -m scripts.run_daily_pipeline --max-keywords 5
   ```
2. Check database has data:
   ```bash
   sqlite3 data.db "SELECT COUNT(*) FROM daily_snapshots;"
   ```
3. Verify snapshot date matches:
   ```bash
   sqlite3 data.db "SELECT DISTINCT snapshot_date FROM daily_snapshots ORDER BY snapshot_date DESC LIMIT 1;"
   ```

### Missing Google Trends Data

**Problem:** Charts don't display or show "No data"

**Solutions:**

1. Check Google Trends cache:
   ```bash
   sqlite3 data.db "SELECT COUNT(*) FROM google_trends_cache;"
   ```
2. Run pipeline to fetch trends data:
   ```bash
   python -m scripts.run_daily_pipeline --max-keywords 5
   ```
3. Manually fetch trends for a keyword:
   ```bash
   python -m scripts.fetch_google_trends
   ```

### Forbidden Words Found

**Problem:** Check script finds TikTok mentions

**Solutions:**

1. Review the generated HTML files:
   ```bash
   grep -r -i "tiktok" public_test/
   ```
2. Check the build script (`scripts/build_public_pages.py`) for any hardcoded mentions
3. Verify database doesn't contain TikTok-specific metadata in public-facing fields
4. Re-generate pages after fixing issues

### Pages Don't Load in Browser

**Problem:** 404 errors or blank pages

**Solutions:**

1. Check file permissions:
   ```bash
   ls -la public_test/keywords/1/index.html
   ```
2. Verify file exists:
   ```bash
   find public_test -name "index.html"
   ```
3. Check HTML syntax:
   ```bash
   # Use a validator or check manually
   head -20 public_test/index.html
   ```

## Next Steps

After local verification:

1. **Deploy to Production:**

   - Generate pages to production directory
   - Run automated check
   - Deploy using atomic swap script

2. **Set Up Automation:**

   - Configure cron job for daily generation
   - Set up monitoring/alerting for failures

3. **Add Sitemap/Robots (Optional):**
   - Generate sitemap.xml
   - Create robots.txt
   - Update build script if needed

## Related Documentation

- `DEPLOYMENT.md` - Complete deployment guide
- `backend/scripts/build_public_pages.py` - Page generation script
- `backend/scripts/check_public_pages_no_tiktok.py` - Automated check script
- `backend/scripts/deploy_public_pages.py` - Deployment script
