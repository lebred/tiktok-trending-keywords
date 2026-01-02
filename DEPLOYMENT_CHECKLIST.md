# Deployment Checklist

Use this checklist to ensure all deployment steps are completed.

## Pre-Deployment

### Environment Setup

- [ ] DigitalOcean account created
- [ ] Domain name registered (optional)
- [ ] Stripe account set up with API keys
- [ ] SMTP service configured (Gmail, SendGrid, etc.)
- [ ] GitHub repository is private and accessible

### Configuration

- [ ] Generate SECRET_KEY: `openssl rand -hex 32`
- [ ] Collect all API keys (Stripe, SMTP)
- [ ] Prepare database connection string
- [ ] Document all environment variables

## Database Setup

- [ ] Create PostgreSQL database on DigitalOcean
- [ ] Note connection string
- [ ] Configure trusted sources/access
- [ ] Test connection from local machine
- [ ] Backup connection credentials securely

## Backend Deployment

### App Platform Method

- [ ] Create new app in App Platform
- [ ] Connect GitHub repository
- [ ] Configure backend component:
  - [ ] Source directory: `backend`
  - [ ] Build command: `pip install -r requirements.txt`
  - [ ] Run command: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
  - [ ] HTTP port: 8080
- [ ] Add all environment variables
- [ ] Configure health check: `/health`
- [ ] Deploy and verify

### Droplet Method (Alternative)

- [ ] Create Ubuntu 22.04 Droplet
- [ ] Install Python 3.11, PostgreSQL client, Nginx
- [ ] Clone repository
- [ ] Set up virtual environment
- [ ] Configure environment variables
- [ ] Create systemd service
- [ ] Configure Nginx reverse proxy
- [ ] Set up SSL with Certbot

## Frontend Deployment

### App Platform Method

- [ ] Add frontend component to app
- [ ] Configure:
  - [ ] Source directory: `frontend`
  - [ ] Build command: `npm install && npm run build`
  - [ ] Run command: `npm start`
  - [ ] HTTP port: 3000
- [ ] Add frontend environment variables
- [ ] Deploy and verify

### Vercel Method (Alternative)

- [ ] Connect repository to Vercel
- [ ] Set root directory to `frontend`
- [ ] Add environment variables
- [ ] Deploy

## Database Migrations

- [ ] Run initial migration: `alembic upgrade head`
- [ ] Verify tables created
- [ ] Test database connection from app
- [ ] Verify schema matches models

## Scheduler Setup

- [ ] Verify DEBUG=False in production
- [ ] Check scheduler starts on app startup
- [ ] Verify job scheduled for 2 AM UTC
- [ ] Test manual pipeline run
- [ ] Monitor first scheduled run

## Stripe Configuration

- [ ] Add Stripe API keys to environment
- [ ] Create product and price in Stripe dashboard
- [ ] Note price ID for STRIPE_PRICE_ID
- [ ] Configure webhook endpoint:
  - [ ] URL: `https://trendearly.xyz/api/stripe/webhook`
  - [ ] Events: checkout.session.completed, customer.subscription.\*
- [ ] Copy webhook signing secret
- [ ] Test webhook with Stripe CLI
- [ ] Verify webhook processing in logs

## SSL/HTTPS

- [ ] App Platform: Verify automatic SSL
- [ ] Droplet: Install Certbot and get certificate
- [ ] Test HTTPS access
- [ ] Verify certificate auto-renewal

## Testing

### Authentication

- [ ] Test magic link request
- [ ] Verify email received
- [ ] Test token verification
- [ ] Test protected endpoints
- [ ] Test user info endpoint

### Stripe

- [ ] Test checkout session creation
- [ ] Complete test payment
- [ ] Verify webhook received
- [ ] Check subscription status updated
- [ ] Verify user tier changed to PAID

### API Endpoints

- [ ] Test `/health` endpoint
- [ ] Test `/api/keywords` (public)
- [ ] Test `/api/keywords/full` (paid)
- [ ] Test `/api/archive/{date}` (auth required)
- [ ] Test keyword detail endpoints

### Pipeline

- [ ] Run manual pipeline: `python -m scripts.run_daily_pipeline`
- [ ] Verify keywords fetched
- [ ] Verify scores calculated
- [ ] Check database for snapshots
- [ ] Monitor scheduler logs

## Monitoring

- [ ] Set up application logging
- [ ] Configure error alerts
- [ ] Set up uptime monitoring
- [ ] Monitor database performance
- [ ] Track API response times

## Security

- [ ] Verify SECRET_KEY is strong
- [ ] Check database SSL enabled
- [ ] Verify HTTPS only
- [ ] Review CORS settings
- [ ] Check environment variables not exposed
- [ ] Verify webhook signature validation
- [ ] Review access controls

## Backup

- [ ] Enable database automatic backups
- [ ] Test backup restoration
- [ ] Document backup schedule
- [ ] Store credentials securely
- [ ] Set up code repository backups

## Documentation

- [ ] Document production URLs
- [ ] Document admin access
- [ ] Document monitoring dashboards
- [ ] Create runbook for common issues
- [ ] Document rollback procedures

## Post-Deployment

- [ ] Monitor application for 24 hours
- [ ] Verify daily pipeline runs successfully
- [ ] Check error rates
- [ ] Verify email delivery
- [ ] Test user registration flow
- [ ] Test subscription flow end-to-end
- [ ] Review performance metrics
- [ ] Set up regular health checks

## Rollback Plan

- [ ] Document rollback steps
- [ ] Test rollback procedure
- [ ] Keep previous deployment artifacts
- [ ] Document database migration rollback

## Support

- [ ] Set up support email
- [ ] Document known issues
- [ ] Create troubleshooting guide
- [ ] Set up error tracking (Sentry, etc.)
