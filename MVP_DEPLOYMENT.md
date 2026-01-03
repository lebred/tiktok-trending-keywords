# MVP Deployment Guide - SQLite Edition

**Fast, cheap deployment for MVP launch.**

**Domain**: `trendearly.xyz`

## Why SQLite for MVP?

- ✅ **Zero database costs** - No $15/month PostgreSQL bill
- ✅ **Simple setup** - No database server to manage
- ✅ **Perfect for single server** - Ideal for MVP scale
- ✅ **Easy backups** - Just copy the file
- ✅ **Easy migration** - Can move to PostgreSQL later without code changes

**Total Cost: ~$17-20/month** (Droplet ~$12 + Spaces ~$5 minimum, varies by usage)

## Quick Deployment Steps

### 1. Create DigitalOcean Droplet

1. Create Ubuntu 22.04 Droplet
2. **Size**: 2GB RAM, 1 vCPU ($12/month) - sufficient for MVP
3. Choose your region
4. Add SSH key

### 2. Initial Server Setup

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

### 3. Deploy Application

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

### 4. Initialize Database

```bash
# Run migrations (creates database file automatically)
alembic upgrade head

# Verify database created
ls -lh /var/lib/tiktok-tracker/data.db
```

### 5. Create Systemd Services

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

**Frontend service:**

```bash
sudo nano /etc/systemd/system/tiktok-frontend.service
```

```ini
[Unit]
Description=TikTok Keyword Momentum Tracker Frontend
After=network.target

[Service]
User=tiktok
WorkingDirectory=/home/tiktok/tiktok-trending-keywords/frontend
Environment="NODE_ENV=production"
Environment="NEXT_PUBLIC_API_URL=http://localhost:8000"
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable tiktok-backend tiktok-frontend
sudo systemctl start tiktok-backend tiktok-frontend

# Check status
sudo systemctl status tiktok-backend
sudo systemctl status tiktok-frontend
```

### 6. Configure Nginx

**Use the production-ready configuration:**

```bash
# Copy the Nginx config from the repository
sudo cp /path/to/tiktok-trending-keywords/deploy/nginx/trendearly.xyz.conf /etc/nginx/sites-available/trendearly.xyz

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

### 7. Set Up SSL

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

### 8. Set Up Public Pages Generation

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
0 2 * * * cd /path/to/backend && /path/to/venv/bin/python -m scripts.deploy_public_pages --source /var/www/trendearly/public_tmp --target /var/www/trendearly/public --user www-data --group www-data
```

Or integrate into the daily pipeline script (already done - pages are generated to temp dir).

### 9. Public Pages

See the [Public Pages section](#public-pages) below for complete details on:

- File locations and structure
- Nginx mapping
- Cron/systemd setup
- Troubleshooting

### 10. Set Up Daily Backups

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

### 9. Test Everything

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Test pipeline
cd backend
source venv/bin/activate
python -m scripts.run_daily_pipeline --max-keywords 5
```

## Maintenance

### View Logs

```bash
# Backend logs
sudo journalctl -u tiktok-backend -f

# Frontend is static - no logs needed (served by Nginx)
# Check Nginx logs if needed:
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

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

## When to Migrate to PostgreSQL

Migrate when you need:

- Multiple app instances (horizontal scaling)
- High write concurrency
- Advanced database features
- Better performance at scale

**Migration is easy:**

```bash
python -m scripts.migrate_from_sqlite_to_postgres \
  sqlite:////var/lib/tiktok-tracker/data.db \
  postgresql://user:pass@host:5432/db
```

## Cost Breakdown

- **Droplet (2GB)**: ~$12/month (varies by region/plan)
- **Spaces (backups)**: ~$5/month minimum (depends on storage/egress)
- **Total**: **~$17-20/month** ✅ (typical)

Compare to production setup:

- App Platform: ~$12/month
- Managed PostgreSQL: ~$15/month minimum
- **Total**: ~$27/month minimum

**Savings: ~$7-10/month = ~$84-120/year** (typical)

## Troubleshooting

**Database locked error:**

- SQLite doesn't handle concurrent writes well
- This is fine for MVP (single server, daily batch processing)
- Ensure backups run after daily pipeline (when writes are done)
- Migrate to PostgreSQL if you see this frequently

**Backup corruption:**

- The backup script uses SQLite's online backup API (safe during writes)
- If you see corruption, ensure WAL checkpoint completes
- Consider running backups right after daily pipeline completes

**Backup failed:**

- Check Spaces credentials
- Verify bucket exists
- Check file permissions

**Service won't start:**

- Check logs: `sudo journalctl -u tiktok-backend -n 50`
- Verify .env file exists and is readable
- Check database file permissions
