# Deployment Guide

Complete guide for deploying TikTok Keyword Momentum Tracker to DigitalOcean.

## 🚀 Quick Start: MVP Deployment

**For fastest, cheapest deployment, see [MVP_DEPLOYMENT.md](./MVP_DEPLOYMENT.md)**

- Single Droplet + SQLite = **$17/month**
- No database setup needed
- Simple daily backups
- Easy migration to PostgreSQL later

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
Cost: ~$12/month + Spaces ($5/month) = $17/month
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

## Step 1: Database Setup

### Option A: SQLite (MVP - Recommended)

**No setup needed!** SQLite is built into Python.

1. **Set Environment Variable:**

   ```bash
   DATABASE_URL=sqlite:///./data.db
   ```

   Or leave it unset to use the default.

2. **Database File Location:**

   - The database file (`data.db`) will be created automatically
   - Store it in a persistent location (e.g., `/var/lib/tiktok-tracker/data.db`)

3. **Run Migrations:**

   ```bash
   alembic upgrade head
   ```

   This creates the database file and all tables.

4. **Backup Setup:**
   - Set up daily cron job to backup database:
   ```bash
   # Add to crontab
   0 3 * * * cd /path/to/backend && python -m scripts.backup_sqlite --upload
   ```

### Option B: PostgreSQL (Production - After Traction)

### 1.1 Create PostgreSQL Database

1. Log into DigitalOcean dashboard
2. Navigate to **Databases** → **Create Database**
3. Choose:
   - **Engine**: PostgreSQL
   - **Version**: 14 or later
   - **Plan**: Basic ($15/month minimum for production)
   - **Region**: Same as your app
   - **Database Name**: `tiktok_keywords` (or your choice)

### 1.2 Configure Database Access

1. Go to database settings
2. Under **Trusted Sources**, add your app's IP or allow all (for App Platform)
3. Note the connection string (you'll need this)

### 1.3 Run Migrations

Once your backend is deployed, run migrations:

```bash
# SSH into your app or use App Platform console
cd backend
alembic upgrade head
```

Or create a one-time migration job in App Platform.

### 1.4 Migrating from SQLite to PostgreSQL

When ready to migrate:

```bash
python -m scripts.migrate_from_sqlite_to_postgres \
  sqlite:///./data.db \
  postgresql://user:pass@host:5432/db
```

This script copies all data from SQLite to PostgreSQL.

## Step 2: Environment Variables

### 2.1 Backend Environment Variables

Set these in DigitalOcean App Platform → Settings → App-Level Environment Variables:

```bash
# Database (SQLite for MVP - no setup needed!)
DATABASE_URL=sqlite:///./data.db
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
```

**Generate SECRET_KEY:**

```bash
openssl rand -hex 32
```

### 2.2 Frontend Environment Variables

Set these in App Platform for the frontend component:

```bash
NEXT_PUBLIC_API_URL=https://trendearly.xyz
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## Step 3: Backend Deployment

### 3.1 Option A: DigitalOcean Droplet (MVP - Recommended)

**Best for MVP:** Single Droplet with SQLite

1. **Create Droplet**

   - Ubuntu 22.04 LTS
   - **Basic**: 2GB RAM, 1 vCPU ($12/month) - sufficient for MVP
   - **Recommended**: 4GB RAM, 2 vCPU ($24/month) - better performance

2. **Initial Setup**

   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3-pip -y

   # Install Node.js 18
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs

   # Install Nginx
   sudo apt install nginx -y
   ```

3. **Deploy Application**

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

   # Set environment variables
   nano .env
   # DATABASE_URL=sqlite:////var/lib/tiktok-tracker/data.db
   # Add other variables...

   # Run migrations
   alembic upgrade head
   ```

4. **Create Systemd Service**

   ```bash
   sudo nano /etc/systemd/system/tiktok-backend.service
   ```

   Content:

   ```ini
   [Unit]
   Description=TikTok Keyword Momentum Tracker API
   After=network.target

   [Service]
   User=your-user
   WorkingDirectory=/home/your-user/tiktok-trending-keywords/backend
   Environment="PATH=/home/your-user/tiktok-trending-keywords/backend/venv/bin"
   EnvironmentFile=/home/your-user/tiktok-trending-keywords/backend/.env
   ExecStart=/home/your-user/tiktok-trending-keywords/backend/venv/bin/uvicorn src.app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tiktok-backend
   sudo systemctl start tiktok-backend
   ```

5. **Set Up Daily Backups**

   ```bash
   # Install boto3 for Spaces upload (optional)
   source venv/bin/activate
   pip install boto3

   # Add to crontab
   crontab -e
   # Add: 0 3 * * * cd /path/to/backend && /path/to/venv/bin/python -m scripts.backup_sqlite --upload
   ```

6. **Configure Nginx**

   ```bash
   sudo nano /etc/nginx/sites-available/tiktok-backend
   ```

   Content:

   ```nginx
   server {
       listen 80;
       server_name trendearly.xyz;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/tiktok-backend /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### 3.2 Option B: DigitalOcean App Platform (Production)

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

   - Add all backend environment variables from Step 2.1

4. **Health Check**
   - **Path**: `/health`
   - **Initial Delay**: 30 seconds

### 3.3 Option C: DigitalOcean Droplet (Manual - Alternative)

1. **Create Droplet**

   - Ubuntu 22.04 LTS
   - Minimum: 2GB RAM, 1 vCPU ($12/month)
   - Recommended: 4GB RAM, 2 vCPU ($24/month)

2. **Initial Setup**

   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3-pip -y

   # Install PostgreSQL client
   sudo apt install postgresql-client -y

   # Install Nginx
   sudo apt install nginx -y
   ```

3. **Deploy Application**

   ```bash
   # Clone repository
   git clone your-repo-url
   cd tiktok-trending-keywords/backend

   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Set environment variables
   nano .env
   # (Add all environment variables)

   # Run migrations
   alembic upgrade head
   ```

4. **Create Systemd Service**

   ```bash
   sudo nano /etc/systemd/system/tiktok-backend.service
   ```

   Content:

   ```ini
   [Unit]
   Description=TikTok Keyword Momentum Tracker API
   After=network.target

   [Service]
   User=your-user
   WorkingDirectory=/home/your-user/tiktok-trending-keywords/backend
   Environment="PATH=/home/your-user/tiktok-trending-keywords/backend/venv/bin"
   ExecStart=/home/your-user/tiktok-trending-keywords/backend/venv/bin/uvicorn src.app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tiktok-backend
   sudo systemctl start tiktok-backend
   ```

5. **Configure Nginx**

   ```bash
   sudo nano /etc/nginx/sites-available/tiktok-backend
   ```

   Content:

   ```nginx
   server {
       listen 80;
       server_name trendearly.xyz;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/tiktok-backend /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Step 4: Frontend Deployment

### 4.1 Option A: Same Droplet (MVP)

Deploy frontend on the same Droplet:

```bash
cd frontend
npm install
npm run build

# Create systemd service for frontend
sudo nano /etc/systemd/system/tiktok-frontend.service
```

Content:

```ini
[Unit]
Description=TikTok Keyword Momentum Tracker Frontend
After=network.target

[Service]
User=your-user
WorkingDirectory=/home/your-user/tiktok-trending-keywords/frontend
Environment="NODE_ENV=production"
Environment="NEXT_PUBLIC_API_URL=http://localhost:8000"
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

Update Nginx to serve both:

```nginx
server {
    listen 80;
    server_name trendearly.xyz;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4.2 Option B: DigitalOcean App Platform

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
   - Add frontend environment variables from Step 2.2

### 4.3 Option C: Vercel (Alternative - Recommended for Next.js)

1. **Connect Repository**

   - Go to vercel.com
   - Import your GitHub repository
   - Set root directory to `frontend`

2. **Environment Variables**

   - Add `NEXT_PUBLIC_API_URL`
   - Add `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

3. **Deploy**
   - Vercel auto-deploys on push to main branch

## Step 5: Scheduler Setup

### 5.1 App Platform (Automatic)

The scheduler runs automatically when the backend starts (if DEBUG=False).

### 5.2 Droplet (Cron Job)

If using a Droplet, you can use cron instead:

```bash
# Edit crontab
crontab -e

# Add daily job at 2 AM UTC
0 2 * * * cd /path/to/backend && /path/to/venv/bin/python -m scripts.run_daily_pipeline >> /var/log/tiktok-pipeline.log 2>&1
```

Or keep the APScheduler running in the background service.

## Step 6: Stripe Webhook Configuration

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

## Step 7: SSL/HTTPS Setup

### 7.1 App Platform

SSL is automatically handled by App Platform.

### 7.2 Droplet with Nginx

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d trendearly.xyz

# Auto-renewal is set up automatically
```

## Step 8: Monitoring and Logging

### 8.1 App Platform

- Built-in logging dashboard
- Set up alerts for errors

### 8.2 Droplet

```bash
# View backend logs
sudo journalctl -u tiktok-backend -f

# View pipeline logs
tail -f /var/log/tiktok-pipeline.log
```

### 8.3 External Monitoring (Optional)

- Set up UptimeRobot or similar for health checks
- Monitor `/health` endpoint
- Set up error alerting

## Step 9: Backup Strategy

### 9.1 SQLite Backups (MVP)

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

### 9.2 PostgreSQL Backups (Production)

DigitalOcean Managed PostgreSQL:

- Automatic daily backups (included)
- Retention: 7 days (can upgrade)

Manual backups:

```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 9.3 Application Backups

- Code: GitHub repository
- Environment variables: Store securely (1Password, etc.)
- Regular database exports

## Step 10: Initial Setup Checklist

- [ ] PostgreSQL database created and accessible
- [ ] Database migrations run successfully
- [ ] All environment variables configured
- [ ] Backend deployed and health check passing
- [ ] Frontend deployed and accessible
- [ ] Stripe webhook configured and tested
- [ ] SSL certificate installed
- [ ] Scheduler running (check logs)
- [ ] Test magic link authentication
- [ ] Test Stripe checkout flow
- [ ] Monitor first daily pipeline run

## Step 11: Post-Deployment Testing

### 11.1 Test Authentication

1. Request magic link: `POST /api/auth/login`
2. Check email for magic link
3. Verify token: `POST /api/auth/verify`
4. Test protected endpoint: `GET /api/auth/me`

### 11.2 Test Stripe

1. Create checkout session: `POST /api/stripe/create-checkout`
2. Complete test payment
3. Verify webhook received
4. Check user subscription status

### 11.3 Test Pipeline

1. Run manually: `python -m scripts.run_daily_pipeline`
2. Check logs for errors
3. Verify keywords in database
4. Verify scores calculated

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL

# Check SSL mode
# Ensure DATABASE_URL includes ?sslmode=require
```

### Scheduler Not Running

- Check DEBUG environment variable (should be False)
- Check application logs
- Verify scheduler started in startup logs

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

- **Droplet (2GB)**: ~$12/month (varies by region)
- **DigitalOcean Spaces** (for backups): ~$5/month minimum (depends on storage/egress)
- **Total: ~$17-20/month** ✅ (typical cost)

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
- [ ] Database uses SSL connections
- [ ] Environment variables not in code
- [ ] HTTPS enabled (SSL certificate)
- [ ] CORS configured for frontend domain only
- [ ] Rate limiting enabled (consider adding)
- [ ] Database backups enabled
- [ ] Webhook signature verification working
- [ ] SMTP credentials secure

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
