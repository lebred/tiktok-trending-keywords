# Frontend

Next.js frontend for TikTok Keyword Momentum Tracker.

## Structure

```
frontend/
├── app/                 # Next.js App Router
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Homepage
│   ├── archive/         # Archive page
│   ├── keywords/        # Keyword detail pages
│   └── api/             # API routes (if needed)
├── components/          # React components
├── lib/                 # Utilities and helpers
├── styles/              # Global styles
└── public/              # Static assets
```

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Stripe publishable key

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React 18

