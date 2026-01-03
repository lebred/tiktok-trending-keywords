# Deployment Guide

Complete guide for deploying TrendEarly to DigitalOcean.

**Domain**: `trendearly.xyz`

## 🚀 Quick Start: MVP Deployment

**Fastest, cheapest deployment for MVP launch.**

- Single Droplet + SQLite = **~$17-20/month**
- No database setup needed
- Simple daily backups
- Easy migration to PostgreSQL later

### Quick Steps

1. **Create Droplet** (Ubuntu 22.04, 2GB RAM, $12/month)
2. **Initial Setup**: Install Python 3.11, Nginx (no Node.js needed on server)
3. **Deploy Backend**: Clone repo, setup backend, configure .env
4. **Build Frontend**: Build locally/CI, copy static files to `/var/www/trendearly/app`
5. **Database**: Run migrations (SQLite auto-created)
6. **Services**: Create systemd service for backend only
7. **Nginx**: Use config from `deploy/nginx/trendearly.xyz.conf`
8. **SSL**: Run certbot
9. **Automation**: Setup daily pipeline + public pages + backups

**See [Detailed MVP Steps](#mvp-deployment-droplet--sqlite) below for complete instructions.**

---

## Prerequisites

- DigitalOcean account
- Domain name: **trendearly.xyz**
- Stripe account with API keys
- SMTP service (Gmail, SendGrid, etc.) for magic links
- GitHub repository (private)
- Local machine or CI with Node.js 18+ (for frontend build only)

## Architecture Overview

### MVP Setup (Recommended for Launch)

```
┌─────────────────┐
│  DigitalOcean    │
│                 │
│  ┌───────────┐  │
│  │  Droplet  │  │  Backend (FastAPI) + Static Files + SQLite
│  │  ($12/mo) │  │  - /var/www/trendearly/public (public pages)
│  │           │  │  - /var/www/trendearly/app (paid UI, optional)
│  │           │  │  - /var/lib/tiktok-tracker/data.db (SQLite)
│  └───────────┘  │
└─────────────────┘
Cost: ~$12/month + Spaces ($5/month) = $17-20/month
```

**Key Points:**

- **No Node.js server** on droplet - frontend is pre-built static files
- **Nginx serves** all static content directly
- **FastAPI backend** runs on localhost:8000, proxied via Nginx
- **SQLite database** for MVP (zero cost)

### Production Setup (After Traction)

```
┌─────────────────┐
│  DigitalOcean   │
│                 │
│  ┌───────────┐  │
│  │  App      │  │  Backend (FastAPI) + Frontend (Next.js)
│  │  Platform │  │
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │ Managed   │  │  PostgreSQL Database
│  │ PostgreSQL│  │
│  └───────────┘  │
└─────────────────┘
Cost: ~$72/month
```

## Database Strategy: SQLite for MVP

**Recommended approach for MVP:**

- Start with SQLite (no additional cost)
- Simple daily backups to DigitalOcean Spaces
- Migrate to PostgreSQL when you hit traction

**Why SQLite for MVP:**

- ✅ Zero database costs
- ✅ No connection management
- ✅ Perfect for single-server deployment
- ✅ Safe backups using SQLite online backup API
- ✅ Can migrate to PostgreSQL later without schema changes (using portable types)

**When to migrate to PostgreSQL:**

- Multiple app instances needed
- High write concurrency
- Need advanced features (full-text search, etc.)
- Scaling beyond single server

## MVP Deployment (Droplet + SQLite)

### Step 1: Create DigitalOcean Droplet

1. Create Ubuntu 22.04 Droplet
2. **Size**: 2GB RAM, 1 vCPU ($12/month) - sufficient for MVP
3. Choose your region
4. Add SSH key

### Step 2: Initial Server Setup

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Python 3.11
apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx
apt install nginx -y

# Create app user (optional but recommended)
adduser trendearly
usermod -aG sudo trendearly
su - trendearly
```

**Note**: Node.js is NOT needed on the server. Frontend is built locally/CI and static files are copied to the server.

### Step 3: Deploy Backend

```bash
# Clone repository
git clone your-repo-url
cd tiktok-trending-keywords

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create data directory
sudo mkdir -p /var/lib/tiktok-tracker
sudo chown $USER:$USER /var/lib/tiktok-tracker

# Create directories for static files
sudo mkdir -p /var/www/trendearly/{public,app}
sudo chown -R $USER:$USER /var/www/trendearly

# Create .env file
nano .env
```

**Minimum .env configuration:**

```bash
# Database - SQLite (no setup needed!)
DATABASE_URL=sqlite:////var/lib/tiktok-tracker/data.db

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Email (for magic links)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# App
APP_NAME=TrendEarly
DEBUG=False
FRONTEND_URL=https://trendearly.xyz

# Public Pages (static HTML generation)
PUBLIC_PAGES_DIR=/var/www/trendearly/public
```

### Step 4: Initialize Database

```bash
# Run migrations (creates database file automatically)
alembic upgrade head

# Verify database created
ls -lh /var/lib/tiktok-tracker/data.db
```

### Step 5: Create Backend Systemd Service

```bash
sudo nano /etc/systemd/system/trendearly-backend.service
```

```ini
[Unit]
Description=TrendEarly API
After=network.target

[Service]
User=trendearly
WorkingDirectory=/home/trendearly/tiktok-trending-keywords/backend
Environment="PATH=/home/trendearly/tiktok-trending-keywords/backend/venv/bin"
EnvironmentFile=/home/trendearly/tiktok-trending-keywords/backend/.env
ExecStart=/home/trendearly/tiktok-trending-keywords/backend/venv/bin/uvicorn src.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable trendearly-backend
sudo systemctl start trendearly-backend

# Check status
sudo systemctl status trendearly-backend

# Check logs
sudo journalctl -u trendearly-backend -f
```

### Step 6: Static Frontend Build + Deploy (Optional /app)

**Build frontend locally or in CI:**

```bash
# On your local machine or CI
cd frontend
npm ci
npm run build

# This creates frontend/out/ directory with static files
```

**Copy to server:**

```bash
# From your local machine
scp -r frontend/out/* trendearly@your-droplet-ip:/var/www/trendearly/app/

# Or use rsync
rsync -avz frontend/out/ trendearly@your-droplet-ip:/var/www/trendearly/app/
```

**Or build on server (one-time, then remove Node.js):**

```bash
# On server (temporary - install Node.js only for build)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Build
cd frontend
npm ci
npm run build

# Copy to app directory
cp -r out/* /var/www/trendearly/app/

# Optional: Remove Node.js if not needed
# sudo apt remove nodejs
```

**Note**: The `/app` route is optional. If you don't have a paid UI, skip this step. Public pages are generated separately and don't require Node.js.

### Step 7: Configure Nginx

**Use the production-ready configuration:**

```bash
# Copy the Nginx config from the repository
sudo cp /home/trendearly/tiktok-trending-keywords/deploy/nginx/trendearly.xyz.conf /etc/nginx/sites-available/trendearly.xyz

# Create symlink
sudo ln -s /etc/nginx/sites-available/trendearly.xyz /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration (CRITICAL - always do this first!)
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Nginx URL Mapping:**

- `/` → `/var/www/trendearly/public` (public pages)
- `/keywords/{id}/` → `/var/www/trendearly/public/keywords/{id}/index.html`
- `/api/*` → `http://127.0.0.1:8000` (reverse proxy)
- `/app/*` → `/var/www/trendearly/app` (paid UI, optional)

**Configuration Details:**

The Nginx config (`deploy/nginx/trendearly.xyz.conf`) includes:

- **Root**: `/var/www/trendearly/public` (static public pages)
- **API Proxy**: `/api/*` → `http://127.0.0.1:8000`
- **App Route**: `/app/*` → `/var/www/trendearly/app` (optional)
- **Gzip compression**: Enabled for text-based files
- **Caching**: Static assets (1y), HTML pages (1h), API (no cache)
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **SSL ready**: Commented SSL block for after certbot setup

**Important**: The `try_files` directive in the root location must NOT interfere with `/api/` routing. The config ensures `/api/` is matched first before the root location.

### Step 8: Set Up SSL

**Install Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx -y
```

**Obtain SSL Certificate:**

```bash
sudo certbot --nginx -d trendearly.xyz -d www.trendearly.xyz
```

**Note**: After running certbot, it will automatically update the Nginx configuration to enable SSL. The config file includes commented SSL blocks that certbot will uncomment and configure.

**Verify SSL:**

```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

**Auto-renewal**: Certbot sets up automatic renewal via systemd timer. Certificates renew automatically 30 days before expiration.

### Step 9: Public Pages Generation + Deploy

Public pages are static HTML files generated from Google Trends data. They contain **no TikTok-specific information**.

**File Locations:**

- **Generation Directory**: `/var/www/trendearly/public_tmp` (temporary, during generation)
- **Production Directory**: `/var/www/trendearly/public` (served by Nginx)
- **Backup Directory**: `/var/www/trendearly/public_prev` (created during atomic swap)

**Structure:**

```
/var/www/trendearly/public/
├── index.html              # Main listing page
├── sitemap.xml             # Sitemap (generated)
├── robots.txt              # Robots file (generated)
└── keywords/
    ├── 1/
    │   └── index.html      # Keyword detail page (numeric ID)
    ├── 2/
    │   └── index.html
    └── ...
```

**URL Structure:**

- `https://trendearly.xyz/` → `index.html` (keyword listing)
- `https://trendearly.xyz/keywords/1/` → `keywords/1/index.html` (keyword detail by numeric ID)
- `https://trendearly.xyz/sitemap.xml` → `sitemap.xml`
- `https://trendearly.xyz/robots.txt` → `robots.txt`

**Note**: Current implementation uses numeric IDs (`/keywords/1/`). Future enhancement could use slugs (`/k/keyword-slug/`).

**Manual Generation (for testing):**

```bash
cd backend
source venv/bin/activate

# Generate to temp directory
python -m scripts.build_public_pages --out /var/www/trendearly/public_tmp --date $(date +%Y-%m-%d)

# Verify no TikTok mentions
python -m scripts.check_public_pages_no_tiktok /var/www/trendearly/public_tmp

# Deploy (atomic swap)
python -m scripts.deploy_public_pages \
  --source /var/www/trendearly/public_tmp \
  --target /var/www/trendearly/public \
  --user www-data \
  --group www-data
```

### Step 10: Scheduler

**Recommended: Use APScheduler (built into backend)**

The backend service automatically runs the daily pipeline via APScheduler when `DEBUG=False`. No additional setup needed.

**Schedule:**

- **Pipeline**: Runs daily at 2:00 AM UTC
- **Public Pages**: Generated automatically after pipeline completes
- **Deployment**: Manual or via cron (see below)

**Optional: Use Cron for Public Pages Deployment**

If you want to deploy public pages separately from generation:

```bash
crontab -e

# Deploy public pages at 2:30 AM UTC (after pipeline completes)
30 2 * * * cd /home/trendearly/tiktok-trending-keywords/backend && /home/trendearly/tiktok-trending-keywords/backend/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data >> /var/log/trendearly/public_pages_deploy.log 2>&1
```

**Or use systemd timer** (more robust):

Create `/etc/systemd/system/trendearly-deploy-pages.service`:

```ini
[Unit]
Description=Deploy TrendEarly Public Pages
After=trendearly-backend.service

[Service]
Type=oneshot
User=trendearly
WorkingDirectory=/home/trendearly/tiktok-trending-keywords/backend
ExecStart=/home/trendearly/tiktok-trending-keywords/backend/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data
```

Create `/etc/systemd/system/trendearly-deploy-pages.timer`:

```ini
[Unit]
Description=Deploy TrendEarly Public Pages Daily
Requires=trendearly-deploy-pages.service

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl enable trendearly-deploy-pages.timer
sudo systemctl start trendearly-deploy-pages.timer
```

### Step 11: Backups

**Daily Automation Order (Safe Sequence):**

1. **2:00 AM UTC**: Daily pipeline runs (writes to SQLite)
2. **2:05 AM UTC**: Public pages generated to `public_tmp`
3. **2:10 AM UTC**: Forbidden-word scan runs
4. **2:15 AM UTC**: Atomic deploy public pages (swap)
5. **3:00 AM UTC**: SQLite backup runs (after all writes complete)

**Set Up DigitalOcean Spaces:**

1. Go to DigitalOcean → Spaces
2. Create bucket
3. Generate access keys
4. Add to `.env`:
   ```bash
   SPACES_ACCESS_KEY=your-key
   SPACES_SECRET_KEY=your-secret
   SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
   SPACES_BUCKET=your-bucket-name
   ```

**Install backup dependency:**

```bash
cd backend
source venv/bin/activate
pip install boto3
```

**Set up cron job for backup:**

```bash
crontab -e

# Backup SQLite daily at 3:00 AM UTC (after pipeline and deploy complete)
0 3 * * * cd /home/trendearly/tiktok-trending-keywords/backend && /home/trendearly/tiktok-trending-keywords/backend/venv/bin/python -m scripts.backup_sqlite --upload >> /var/log/trendearly/backup.log 2>&1
```

**Manual backup:**

```bash
cd backend
source venv/bin/activate
python -m scripts.backup_sqlite --upload
```

**Restore from backup:**

```bash
# Download backup from Spaces
# Then:
cp backup_file.db /var/lib/tiktok-tracker/data.db
sudo systemctl restart trendearly-backend
```

### Common Pitfalls

**⚠️ Always run `nginx -t` before reload:**

```bash
sudo nginx -t  # Must pass before reloading
sudo systemctl reload nginx
```

**⚠️ Disk space monitoring:**

- Monitor `/var/log/` for log growth
- Monitor `/var/www/trendearly/public_tmp` (cleanup old temp dirs)
- Monitor database size: `du -h /var/lib/tiktok-tracker/data.db`

**⚠️ SQLite locked errors:**

- Ensure backups run AFTER pipeline completes (3:00 AM, not 2:00 AM)
- Don't run manual pipeline and backup simultaneously
- If locked, wait for current operation to finish

**⚠️ Permissions under /var/www/trendearly:**

- Ensure `trendearly` user can write to `public_tmp`
- Ensure `www-data` can read from `public` and `app`
- Use deploy script to set correct ownership

**⚠️ Frontend build artifacts:**

- Build happens locally/CI, not on server
- Copy only `frontend/out/*` contents, not the `out/` directory itself
- Verify files exist: `ls -la /var/www/trendearly/app/index.html`

### MVP Validation Checklist

After deployment, verify everything works:

```bash
# 1. Backend health check
curl -s https://trendearly.xyz/api/health
# Expected: {"status":"healthy","service":"api"}

# 2. Public pages root
curl -I https://trendearly.xyz/
# Expected: HTTP/1.1 200 OK

# 3. Sitemap (if generated)
curl -I https://trendearly.xyz/sitemap.xml
# Expected: HTTP/1.1 200 OK (or 404 if not generated yet)

# 4. Robots.txt (if generated)
curl -I https://trendearly.xyz/robots.txt
# Expected: HTTP/1.1 200 OK (or 404 if not generated yet)

# 5. Verify no TikTok mentions in public pages
cd backend
source venv/bin/activate
python -m scripts.check_public_pages_no_tiktok /var/www/trendearly/public_tmp
# Expected: INFO: ✓ All pages passed: No TikTok mentions found

# 6. Database exists and has data
ls -lh /var/lib/tiktok-tracker/data.db
# Expected: File exists with reasonable size

# 7. Backend service running
sudo systemctl status trendearly-backend
# Expected: active (running)

# 8. Nginx serving correctly
sudo systemctl status nginx
# Expected: active (running)

# 9. SSL certificate valid
sudo certbot certificates
# Expected: Valid certificate listed
```

## Production Deployment (App Platform + PostgreSQL)

### When to Use Production Setup

Migrate to production setup when you need:

- Multiple app instances (horizontal scaling)
- High write concurrency
- Advanced database features
- Better performance at scale
- Managed infrastructure

### Step 1: Create PostgreSQL Database

1. Log into DigitalOcean dashboard
2. Navigate to **Databases** → **Create Database**
3. Choose:
   - **Engine**: PostgreSQL
   - **Version**: 14 or later
   - **Plan**: Basic ($15/month minimum for production)
   - **Region**: Same as your app
   - **Database Name**: `tiktok_keywords` (or your choice)

### Step 2: Configure Database Access

1. Go to database settings
2. Under **Trusted Sources**, add your app's IP or allow all (for App Platform)
3. Note the connection string (you'll need this)

### Step 3: Deploy Backend on App Platform

1. **Connect Repository**

   - Go to App Platform → Create App
   - Connect your GitHub repository
   - Select the repository and branch

2. **Configure Backend Component**

   - **Type**: Web Service
   - **Source Directory**: `backend`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Run Command**:
     ```bash
     uvicorn src.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **HTTP Port**: 8080 (or use $PORT variable)

3. **Environment Variables**

   - Add all backend environment variables (see [Environment Variables](#environment-variables) section)
   - Set `DATABASE_URL` to PostgreSQL connection string

4. **Health Check**
   - **Path**: `/api/health`
   - **Initial Delay**: 30 seconds

### Step 4: Deploy Frontend on App Platform

1. **Add Frontend Component**

   - In same app or separate app
   - **Type**: Web Service
   - **Source Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Run Command**:
     ```bash
     npm start
     ```
   - **HTTP Port**: 3000 (or use $PORT)

2. **Environment Variables**
   - Add frontend environment variables (see [Environment Variables](#environment-variables) section)

### Step 5: Run Migrations

Once backend is deployed, run migrations:

```bash
# SSH into your app or use App Platform console
cd backend
alembic upgrade head
```

Or create a one-time migration job in App Platform.

### Step 6: Migrating from SQLite to PostgreSQL

When ready to migrate:

```bash
python -m scripts.migrate_from_sqlite_to_postgres \
  sqlite:////var/lib/tiktok-tracker/data.db \
  postgresql://user:pass@host:5432/db
```

This script copies all data from SQLite to PostgreSQL.

## Environment Variables

### Backend Environment Variables

Set these in DigitalOcean App Platform → Settings → App-Level Environment Variables, or in `.env` file for Droplet:

```bash
# Database (SQLite for MVP - no setup needed!)
DATABASE_URL=sqlite:////var/lib/tiktok-tracker/data.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require

# Security
SECRET_KEY=your-very-long-random-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (for magic links)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# App
APP_NAME=TrendEarly
DEBUG=False
FRONTEND_URL=https://trendearly.xyz

# Public Pages (static HTML generation)
PUBLIC_PAGES_DIR=/var/www/trendearly/public
```

**Generate SECRET_KEY:**

```bash
openssl rand -hex 32
```

### Frontend Environment Variables

Set these in App Platform for the frontend component, or in `.env.local` for local development:

```bash
NEXT_PUBLIC_API_URL=https://trendearly.xyz
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## Stripe Webhook Configuration

1. **Get Webhook Secret**

   - Go to Stripe Dashboard → Developers → Webhooks
   - Click "Add endpoint"
   - **Endpoint URL**: `https://trendearly.xyz/api/stripe/webhook`
   - **Events to send**: Select:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - Copy the **Signing secret** (starts with `whsec_`)
   - Add to `STRIPE_WEBHOOK_SECRET` environment variable

2. **Test Webhook**
   - Use Stripe CLI for local testing:
     ```bash
     stripe listen --forward-to localhost:8000/api/stripe/webhook
     ```

## Monitoring and Logging

### App Platform

- Built-in logging dashboard
- Set up alerts for errors

### Droplet

```bash
# View backend logs
sudo journalctl -u trendearly-backend -f

# View pipeline logs (check backend logs for scheduler output)
sudo journalctl -u trendearly-backend | grep "pipeline"

# View Nginx logs
sudo tail -f /var/log/nginx/trendearly_access.log
sudo tail -f /var/log/nginx/trendearly_error.log

# View public pages deployment log (if using cron)
tail -f /var/log/trendearly/public_pages_deploy.log

# View backup log
tail -f /var/log/trendearly/backup.log
```

### External Monitoring (Optional)

- Set up UptimeRobot or similar for health checks
- Monitor `/api/health` endpoint
- Set up error alerting

## Backup Strategy

### SQLite Backups (MVP)

**Daily Automated Backup to Spaces:**

1. **Set up DigitalOcean Spaces:**

   - Create Spaces bucket
   - Generate access keys
   - Set environment variables (see Step 11 above)

2. **Install backup dependencies:**

   ```bash
   pip install boto3
   ```

3. **Set up cron job:**

   ```bash
   crontab -e
   # Daily backup at 3:00 AM UTC (after pipeline completes)
   0 3 * * * cd /home/trendearly/tiktok-trending-keywords/backend && /home/trendearly/tiktok-trending-keywords/backend/venv/bin/python -m scripts.backup_sqlite --upload >> /var/log/trendearly/backup.log 2>&1
   ```

4. **Manual backup:**
   ```bash
   python -m scripts.backup_sqlite
   # Or with upload:
   python -m scripts.backup_sqlite --upload
   ```

**Backup Retention:**

- Keep last 7 days of backups
- Monthly backups for long-term retention
- Test restore procedure regularly

### PostgreSQL Backups (Production)

DigitalOcean Managed PostgreSQL:

- Automatic daily backups (included)
- Retention: 7 days (can upgrade)

Manual backups:

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Application Backups

- Code: GitHub repository
- Environment variables: Store securely (1Password, etc.)
- Regular database exports

## Initial Setup Checklist

- [ ] Droplet/App Platform created
- [ ] Database initialized (SQLite or PostgreSQL)
- [ ] Database migrations run successfully
- [ ] All environment variables configured
- [ ] Backend deployed and health check passing (`/api/health`)
- [ ] Frontend built and static files copied to `/var/www/trendearly/app` (if using)
- [ ] Nginx configured and serving pages
- [ ] SSL certificate installed
- [ ] Stripe webhook configured and tested
- [ ] Scheduler running (check logs)
- [ ] Daily backups configured
- [ ] Public pages generation working
- [ ] Test magic link authentication
- [ ] Test Stripe checkout flow
- [ ] Monitor first daily pipeline run
- [ ] All validation checklist items pass

## Post-Deployment Testing

### Test Authentication

1. Request magic link: `POST /api/auth/login`
2. Check email for magic link
3. Verify token: `POST /api/auth/verify`
4. Test protected endpoint: `GET /api/auth/me`

### Test Stripe

1. Create checkout session: `POST /api/stripe/create-checkout`
2. Complete test payment
3. Verify webhook received
4. Check user subscription status

### Test Pipeline

1. Run manually: `python -m scripts.run_daily_pipeline --max-keywords 5`
2. Check logs for errors
3. Verify keywords in database
4. Verify scores calculated
5. Verify public pages generated

## Troubleshooting

### Database Connection Issues

```bash
# Test SQLite connection
sqlite3 /var/lib/tiktok-tracker/data.db "SELECT COUNT(*) FROM keywords;"

# Test PostgreSQL connection
psql $DATABASE_URL

# Check SSL mode (PostgreSQL)
# Ensure DATABASE_URL includes ?sslmode=require
```

### Database Locked Error (SQLite)

- SQLite doesn't handle concurrent writes well
- This is fine for MVP (single server, daily batch processing)
- Ensure backups run AFTER daily pipeline (3:00 AM, not 2:00 AM)
- Don't run manual pipeline and backup simultaneously
- Migrate to PostgreSQL if you see this frequently

### Backup Corruption

- The backup script uses SQLite's online backup API (safe during writes)
- If you see corruption, ensure WAL checkpoint completes
- Consider running backups right after daily pipeline completes (3:00 AM)

### Backup Failed

- Check Spaces credentials
- Verify bucket exists
- Check file permissions
- Check logs: `tail -f /var/log/trendearly/backup.log`

### Scheduler Not Running

- Check DEBUG environment variable (should be False)
- Check application logs: `sudo journalctl -u trendearly-backend | grep scheduler`
- Verify scheduler started in startup logs
- Check that pipeline runs at 2:00 AM UTC

### Service Won't Start

- Check logs: `sudo journalctl -u trendearly-backend -n 50`
- Verify .env file exists and is readable
- Check database file permissions
- Verify all environment variables are set
- Check port 8000 is not in use: `sudo lsof -i :8000`

### Email Not Sending

- Verify SMTP credentials
- Check firewall rules (port 587)
- Test with aiosmtplib directly
- Consider using SendGrid or Mailgun for production

### Stripe Webhook Failing

- Verify webhook secret matches
- Check webhook signature in logs
- Test with Stripe CLI locally first
- Ensure endpoint is publicly accessible

### Nginx 404 Errors

- Check Nginx root directory: `sudo nginx -T | grep "root"`
- Verify files exist: `ls -la /var/www/trendearly/public/index.html`
- Check Nginx error log: `sudo tail -f /var/log/nginx/trendearly_error.log`
- Test Nginx configuration: `sudo nginx -t`
- Ensure `/api/` location is defined BEFORE root location in config

### Public Pages Not Updating

- Check if generation ran: `ls -la /var/www/trendearly/public_tmp/`
- Check pipeline logs: `sudo journalctl -u trendearly-backend | grep "public pages"`
- Manually regenerate: `python -m scripts.build_public_pages --out /var/www/trendearly/public_tmp --date $(date +%Y-%m-%d)`
- Check deploy log: `tail -f /var/log/trendearly/public_pages_deploy.log`

### Forbidden Words Found

- Review violation: `python -m scripts.check_public_pages_no_tiktok /var/www/trendearly/public_tmp`
- Check source: `grep -r -i "tiktok" /var/www/trendearly/public_tmp/`
- Review build script for hardcoded mentions
- Regenerate after fixing

## Cost Estimation

### MVP Setup (Recommended for Launch)

- **Droplet (2GB)**: ~$12/month (varies by region/plan)
- **DigitalOcean Spaces** (for backups): ~$5/month minimum (depends on storage/egress)
- **Total: ~$17-20/month** ✅ (typical cost)

Compare to production setup:

- App Platform: ~$12/month
- Managed PostgreSQL: ~$15/month minimum
- **Total: ~$27/month minimum**

**Savings: ~$7-10/month = ~$84-120/year** (typical)

### Production Setup (After Traction)

- **App Platform (Professional)**: $12/month
- **Managed PostgreSQL (Professional)**: $60/month
- **Total: ~$72/month**

### Alternative Production

- **Droplet (4GB)**: $24/month
- **Managed PostgreSQL (Basic)**: $15/month
- **Total: ~$39/month**

**Recommendation:** Start with MVP setup ($17/month), migrate to production when you have traction.

## Security Checklist

- [ ] SECRET_KEY is strong and unique
- [ ] Database uses SSL connections (PostgreSQL)
- [ ] Environment variables not in code
- [ ] HTTPS enabled (SSL certificate)
- [ ] CORS configured for frontend domain only
- [ ] Rate limiting enabled (consider adding)
- [ ] Database backups enabled
- [ ] Webhook signature verification working
- [ ] SMTP credentials secure
- [ ] Public pages contain no TikTok mentions (verified)

## Next Steps

1. Set up monitoring alerts
2. Configure custom domain
3. Set up CI/CD pipeline
4. Add rate limiting middleware
5. Implement error tracking (Sentry, etc.)
6. Set up analytics
7. Create admin dashboard (optional)

## Support

For issues:

1. Check application logs
2. Check database logs
3. Verify environment variables
4. Test endpoints with curl/Postman
5. Review error messages in logs
6. See `docs/VERIFY_PUBLIC_PAGES.md` for public pages verification
