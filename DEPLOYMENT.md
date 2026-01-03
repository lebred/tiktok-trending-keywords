# Deployment Guide

Complete guide for deploying TikTok Keyword Momentum Tracker to DigitalOcean.

**Domain**: `trendearly.xyz`

## 🚀 Quick Start: MVP Deployment

**Fastest, cheapest deployment for MVP launch.**

- Single Droplet + SQLite = **~$17-20/month**
- No database setup needed
- Simple daily backups
- Easy migration to PostgreSQL later

### Quick Steps

1. **Create Droplet** (Ubuntu 22.04, 2GB RAM, $12/month)
2. **Initial Setup**: Install Python 3.11, Node.js 18, Nginx
3. **Deploy App**: Clone repo, setup backend/frontend, configure .env
4. **Database**: Run migrations (SQLite auto-created)
5. **Services**: Create systemd services for backend
6. **Nginx**: Use config from `deploy/nginx/trendearly.xyz.conf`
7. **SSL**: Run certbot
8. **Backups**: Setup cron job for daily backups to Spaces

**See [Detailed MVP Steps](#mvp-deployment-steps) below for complete instructions.**

---

## Prerequisites

- DigitalOcean account
- Domain name: **trendearly.xyz**
- Stripe account with API keys
- SMTP service (Gmail, SendGrid, etc.) for magic links
- GitHub repository (private)

## Architecture Overview

### MVP Setup (Recommended for Launch)

```
┌─────────────────┐
│  DigitalOcean    │
│                 │
│  ┌───────────┐  │
│  │  Droplet  │  │  Backend + Frontend + SQLite
│  │  ($12/mo) │  │  Simple daily backups to Spaces
│  └───────────┘  │
└─────────────────┘
Cost: ~$12/month + Spaces ($5/month) = $17-20/month
```

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

## MVP Deployment Steps

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

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Nginx
apt install nginx -y

# Create app user (optional but recommended)
adduser tiktok
usermod -aG sudo tiktok
su - tiktok
```

### Step 3: Deploy Application

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
APP_NAME=TikTok Keyword Momentum Tracker
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

### Step 5: Create Systemd Services

**Backend service:**

```bash
sudo nano /etc/systemd/system/tiktok-backend.service
```

```ini
[Unit]
Description=TikTok Keyword Momentum Tracker API
After=network.target

[Service]
User=tiktok
WorkingDirectory=/home/tiktok/tiktok-trending-keywords/backend
Environment="PATH=/home/tiktok/tiktok-trending-keywords/backend/venv/bin"
EnvironmentFile=/home/tiktok/tiktok-trending-keywords/backend/.env
ExecStart=/home/tiktok/tiktok-trending-keywords/backend/venv/bin/uvicorn src.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable tiktok-backend
sudo systemctl start tiktok-backend

# Check status
sudo systemctl status tiktok-backend
```

### Step 6: Configure Nginx

**Use the production-ready configuration:**

```bash
# Copy the Nginx config from the repository
sudo cp /home/tiktok/tiktok-trending-keywords/deploy/nginx/trendearly.xyz.conf /etc/nginx/sites-available/trendearly.xyz

# Create symlink
sudo ln -s /etc/nginx/sites-available/trendearly.xyz /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Configuration Details:**

The Nginx config (`deploy/nginx/trendearly.xyz.conf`) includes:

- **Root**: `/var/www/trendearly/public` (static public pages)
- **API Proxy**: `/api/*` → `http://127.0.0.1:8000`
- **Gzip compression**: Enabled for text-based files
- **Caching**: Static assets (1y), HTML pages (1h), API (no cache)
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **SSL ready**: Commented SSL block for after certbot setup

**Note**: The config serves public pages from the root (`/`) and the API from `/api/`. Make sure public pages are generated to `/var/www/trendearly/public` before starting Nginx.

### Step 7: Set Up SSL

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

### Step 8: Set Up Public Pages Generation

The daily pipeline automatically generates static public pages after scoring completes.

**Configure Public Pages Directory:**

Add to `.env`:

```bash
PUBLIC_PAGES_DIR=/var/www/trendearly/public
```

**Manual Generation (Optional):**

```bash
cd backend
source venv/bin/activate
python -m scripts.build_public_pages --out /var/www/trendearly/public_tmp --date $(date +%Y-%m-%d)
```

**Deploy Public Pages (Atomic Swap):**

```bash
python -m scripts.deploy_public_pages \
  --source /var/www/trendearly/public_tmp \
  --target /var/www/trendearly/public \
  --user www-data \
  --group www-data
```

**Note**: Public pages contain only Google Trends data - no TikTok-specific details are exposed.

**Automatic Deployment (Optional):**

To automatically deploy after generation, add to cron job:

```bash
# After daily pipeline completes, deploy public pages
30 2 * * * cd /home/tiktok/tiktok-trending-keywords/backend && /home/tiktok/tiktok-trending-keywords/backend/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data >> /var/log/trendearly/public_pages_deploy.log 2>&1
```

Or use systemd timer (see [Public Pages](#public-pages) section below).

### Step 9: Set Up Daily Backups

**Create DigitalOcean Spaces bucket:**

1. Go to DigitalOcean → Spaces
2. Create bucket
3. Generate access keys
4. Add to .env:
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

**Set up cron job:**

```bash
crontab -e
# Add this line (backup daily at 3 AM):
0 3 * * * cd /home/tiktok/tiktok-trending-keywords/backend && /home/tiktok/tiktok-trending-keywords/backend/venv/bin/python -m scripts.backup_sqlite --upload
```

### Step 10: Test Everything

```bash
# Test backend
curl http://localhost:8000/api/health

# Test Nginx
curl http://localhost

# Test pipeline
cd backend
source venv/bin/activate
python -m scripts.run_daily_pipeline --max-keywords 5
```

## Public Pages

### Overview

Public pages are static HTML files generated from Google Trends data. They contain **no TikTok-specific information** - only keyword names, momentum scores, and Google Trends charts.

### File Locations

- **Generation Directory**: `/var/www/trendearly/public_tmp` (temporary, during generation)
- **Production Directory**: `/var/www/trendearly/public` (served by Nginx)
- **Backup Directory**: `/var/www/trendearly/public_prev` (created during atomic swap)

### Structure

```
/var/www/trendearly/public/
├── index.html              # Main listing page
└── keywords/
    ├── 1/
    │   └── index.html      # Keyword detail page
    ├── 2/
    │   └── index.html
    └── ...
```

### Nginx Mapping

The Nginx configuration serves public pages from the root (`/`):

```nginx
location / {
    root /var/www/trendearly/public;
    try_files $uri $uri/ $uri.html /index.html;
}
```

**URL Structure:**

- `https://trendearly.xyz/` → `index.html` (keyword listing)
- `https://trendearly.xyz/keywords/1/` → `keywords/1/index.html` (keyword detail)

### Daily Generation (Cron)

The daily pipeline automatically generates public pages. To set up a cron job for deployment:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 2:30 AM, after pipeline completes at 2 AM)
30 2 * * * cd /home/tiktok/tiktok-trending-keywords/backend && /home/tiktok/tiktok-trending-keywords/backend/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data >> /var/log/trendearly/public_pages_deploy.log 2>&1
```

**Or use systemd timer** (more robust):

Create `/etc/systemd/system/trendearly-deploy-pages.service`:

```ini
[Unit]
Description=Deploy TrendEarly Public Pages
After=daily-pipeline.service

[Service]
Type=oneshot
User=tiktok
WorkingDirectory=/home/tiktok/tiktok-trending-keywords/backend
ExecStart=/home/tiktok/tiktok-trending-keywords/backend/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data
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

### Verification

**Before deploying, verify pages are clean:**

```bash
cd backend
source venv/bin/activate

# Check for forbidden words
python -m scripts.check_public_pages_no_tiktok /var/www/trendearly/public_tmp
```

**Expected Output:**

```
INFO: ✓ All pages passed: No TikTok mentions found
```

### Troubleshooting

#### Pages Not Updating

**Problem:** Public pages show old data

**Solutions:**

1. Check if generation ran:
   ```bash
   ls -la /var/www/trendearly/public_tmp/
   ```
2. Check pipeline logs:
   ```bash
   journalctl -u tiktok-backend -f | grep "public pages"
   ```
3. Manually regenerate:
   ```bash
   cd backend
   source venv/bin/activate
   python -m scripts.build_public_pages --out /var/www/trendearly/public_tmp --date $(date +%Y-%m-%d)
   ```

#### Permission Errors

**Problem:** `Permission denied` when deploying

**Solutions:**

1. Check directory ownership:
   ```bash
   ls -la /var/www/trendearly/
   ```
2. Fix ownership:
   ```bash
   sudo chown -R tiktok:tiktok /var/www/trendearly/public_tmp
   ```
3. Ensure deploy script has sudo access (if needed):
   ```bash
   sudo visudo
   # Add: tiktok ALL=(ALL) NOPASSWD: /usr/bin/chown, /usr/bin/chmod
   ```

#### Nginx 404 Errors

**Problem:** Pages return 404 in browser

**Solutions:**

1. Check Nginx root directory:
   ```bash
   sudo nginx -T | grep "root"
   ```
2. Verify files exist:
   ```bash
   ls -la /var/www/trendearly/public/index.html
   ```
3. Check Nginx error log:
   ```bash
   sudo tail -f /var/log/nginx/trendearly_error.log
   ```
4. Test Nginx configuration:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

#### Forbidden Words Found

**Problem:** Check script finds TikTok mentions

**Solutions:**

1. Review the violation:
   ```bash
   python -m scripts.check_public_pages_no_tiktok /var/www/trendearly/public_tmp
   ```
2. Check the source:
   ```bash
   grep -r -i "tiktok" /var/www/trendearly/public_tmp/
   ```
3. Review build script for hardcoded mentions
4. Regenerate after fixing

#### Missing Google Trends Data

**Problem:** Charts don't display

**Solutions:**

1. Check database has trends cache:
   ```bash
   sqlite3 /var/lib/tiktok-tracker/data.db "SELECT COUNT(*) FROM google_trends_cache;"
   ```
2. Verify trends data in snapshot:
   ```bash
   sqlite3 /var/lib/tiktok-tracker/data.db "SELECT keyword_id, google_trends_data IS NOT NULL FROM daily_snapshots LIMIT 5;"
   ```
3. Re-run pipeline to fetch trends:
   ```bash
   python -m scripts.run_daily_pipeline --max-keywords 10
   ```

### Monitoring

**Check generation status:**

```bash
# Check last generation time
ls -lt /var/www/trendearly/public/index.html

# Check deployment log
tail -f /var/log/trendearly/public_pages_deploy.log
```

**Set up alerts:**

- Monitor file modification time
- Check for errors in deployment log
- Verify check script passes before deployment

### Related Documentation

- `docs/VERIFY_PUBLIC_PAGES.md` - Full verification guide
- `backend/scripts/build_public_pages.py` - Generation script
- `backend/scripts/check_public_pages_no_tiktok.py` - Verification script
- `backend/scripts/deploy_public_pages.py` - Deployment script

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
APP_NAME=TikTok Keyword Momentum Tracker
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

## Scheduler Setup

### App Platform (Automatic)

The scheduler runs automatically when the backend starts (if DEBUG=False).

### Droplet (Cron Job or APScheduler)

**Option 1: Use APScheduler (Recommended)**

The scheduler runs automatically in the backend service (if DEBUG=False).

**Option 2: Use Cron Job**

```bash
# Edit crontab
crontab -e

# Add daily job at 2 AM UTC
0 2 * * * cd /home/tiktok/tiktok-trending-keywords/backend && /home/tiktok/tiktok-trending-keywords/backend/venv/bin/python -m scripts.run_daily_pipeline >> /var/log/tiktok-pipeline.log 2>&1
```

## Monitoring and Logging

### App Platform

- Built-in logging dashboard
- Set up alerts for errors

### Droplet

```bash
# View backend logs
sudo journalctl -u tiktok-backend -f

# View pipeline logs (if using cron)
tail -f /var/log/tiktok-pipeline.log

# View Nginx logs
sudo tail -f /var/log/nginx/trendearly_access.log
sudo tail -f /var/log/nginx/trendearly_error.log
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
   - Set environment variables:
     ```bash
     SPACES_ACCESS_KEY=your-key
     SPACES_SECRET_KEY=your-secret
     SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
     SPACES_BUCKET=your-bucket-name
     ```

2. **Install backup dependencies:**

   ```bash
   pip install boto3
   ```

3. **Set up cron job:**

   ```bash
   crontab -e
   # Daily backup at 3 AM
   0 3 * * * cd /path/to/backend && /path/to/venv/bin/python -m scripts.backup_sqlite --upload
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

## Maintenance

### View Logs

```bash
# Backend logs
sudo journalctl -u tiktok-backend -f

# Frontend is static - no logs needed (served by Nginx)
# Check Nginx logs if needed:
sudo tail -f /var/log/nginx/trendearly_access.log
sudo tail -f /var/log/nginx/trendearly_error.log

# Pipeline logs (if using cron)
tail -f /var/log/tiktok-pipeline.log
```

### Manual Backup

```bash
cd backend
source venv/bin/activate
python -m scripts.backup_sqlite --upload
```

### Restore from Backup

```bash
# Download backup from Spaces
# Then:
cp backup_file.db /var/lib/tiktok-tracker/data.db
sudo systemctl restart tiktok-backend
```

## Initial Setup Checklist

- [ ] Droplet/App Platform created
- [ ] Database initialized (SQLite or PostgreSQL)
- [ ] Database migrations run successfully
- [ ] All environment variables configured
- [ ] Backend deployed and health check passing (`/api/health`)
- [ ] Frontend deployed and accessible
- [ ] Nginx configured and serving pages
- [ ] SSL certificate installed
- [ ] Stripe webhook configured and tested
- [ ] Scheduler running (check logs)
- [ ] Daily backups configured
- [ ] Public pages generation working
- [ ] Test magic link authentication
- [ ] Test Stripe checkout flow
- [ ] Monitor first daily pipeline run

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
- Ensure backups run after daily pipeline (when writes are done)
- Migrate to PostgreSQL if you see this frequently

### Backup Corruption

- The backup script uses SQLite's online backup API (safe during writes)
- If you see corruption, ensure WAL checkpoint completes
- Consider running backups right after daily pipeline completes

### Backup Failed

- Check Spaces credentials
- Verify bucket exists
- Check file permissions

### Scheduler Not Running

- Check DEBUG environment variable (should be False)
- Check application logs
- Verify scheduler started in startup logs

### Service Won't Start

- Check logs: `sudo journalctl -u tiktok-backend -n 50`
- Verify .env file exists and is readable
- Check database file permissions
- Verify all environment variables are set

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
