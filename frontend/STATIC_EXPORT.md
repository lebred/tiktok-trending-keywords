# Static Export Configuration

This frontend is configured for **fully static export** - no Node.js server required in production.

## Build Output

Running `npm run build` produces:

- `out/` directory containing static HTML/CSS/JS files
- All pages pre-rendered as static HTML
- Client-side data fetching for dynamic content

## Deployment

The `out/` directory can be served by:

- Nginx (recommended)
- Apache
- Any static file server
- CDN (Cloudflare, CloudFront, etc.)

## Configuration

### next.config.js

- `output: 'export'` - Enables static export
- `trailingSlash: true` - Required for proper routing
- `images.unoptimized: true` - Required for static export

### Routing

- All routes work client-side
- Dynamic routes (`/keywords/[id]`) fetch data on the client
- No server-side rendering or API routes

## Data Fetching

All data is fetched client-side from the FastAPI backend:

- API calls use `NEXT_PUBLIC_API_URL` environment variable
- Set at build time: `NEXT_PUBLIC_API_URL=https://trendearly.xyz npm run build`
- All API calls happen in browser after page load

## Production Build

```bash
# Set API URL
export NEXT_PUBLIC_API_URL=https://trendearly.xyz

# Build static files
npm run build

# Output is in out/ directory
# Copy to Nginx web root
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name trendearly.xyz;
    root /var/www/trendearly.xyz/out;
    index index.html;

    # Handle client-side routing
    location / {
        try_files $uri $uri/ $uri.html /index.html;
    }

    # Cache static assets
    location /_next/static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```
