# Domain Configuration

**Domain**: `trendearly.xyz`

## DNS Configuration

### DigitalOcean Droplet

1. **Point A Record to Droplet IP**:
   - Type: A
   - Hostname: `@` (or leave blank)
   - Value: Your Droplet IP address
   - TTL: 3600 (or default)

2. **Optional: WWW Subdomain**:
   - Type: A
   - Hostname: `www`
   - Value: Your Droplet IP address
   - TTL: 3600

### SSL Certificate

After DNS is configured, get SSL certificate:

```bash
sudo certbot --nginx -d trendearly.xyz -d www.trendearly.xyz
```

## Environment Variables

### Backend

```bash
FRONTEND_URL=https://trendearly.xyz
```

### Frontend

```bash
NEXT_PUBLIC_API_URL=https://trendearly.xyz
```

## Stripe Webhook

Configure in Stripe Dashboard:
- **Endpoint URL**: `https://trendearly.xyz/api/stripe/webhook`

## Magic Links

Magic links will use the `FRONTEND_URL` environment variable:
- Format: `https://trendearly.xyz/auth/verify?token=...`

## Testing

After deployment, verify:
- [ ] `https://trendearly.xyz` loads frontend
- [ ] `https://trendearly.xyz/api/health` returns 200
- [ ] SSL certificate is valid
- [ ] Magic links work correctly
- [ ] Stripe webhook receives events

