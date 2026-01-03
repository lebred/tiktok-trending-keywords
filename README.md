# TikTok Keyword Momentum Tracker

An MVP web application that identifies newly emerging TikTok keywords with strong short-term momentum, cross-validated with Google Trends data.

## Purpose

The application surfaces keywords that:

- Were historically low or near-zero
- Have begun accelerating sharply in the past days or weeks
- Are likely early indicators of viral trends

## Features

- **Daily Automated Processing**: Runs once per day to fetch and score trending keywords
- **Momentum Scoring**: Deterministic algorithm (1-100) based on lift, acceleration, novelty, and noise
- **Google Trends Validation**: Cross-validates TikTok trends with Google search data
- **Historical Tracking**: Daily snapshots preserve keyword score history
- **Web Interface**: View rankings, archives, and keyword details
- **Monetization**: Free tier with limited access, paid tier for full features

## Tech Stack

- **Backend**: Python 3.11, FastAPI
- **Frontend**: Next.js (App Router), TypeScript
- **Database**: PostgreSQL
- **Deployment**: DigitalOcean

## Project Structure

```
├── backend/          # Python backend application
├── frontend/         # Next.js frontend application
├── docs/             # Additional documentation
├── PROJECT_STATE.md  # Current project status
├── BUILD_SPEC.md     # Technical specifications
└── TODO.md           # Implementation tasks
```

## Getting Started

### Quick Start

See [QUICK_START.md](./QUICK_START.md) for local development setup.

### Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (built into Python) - **No setup needed for MVP!**
- PostgreSQL 14+ (optional, for production)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn src.app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start dev server
npm run dev
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment guide to DigitalOcean (includes both MVP and Production setups).

## Documentation

- See `BUILD_SPEC.md` for complete technical specifications
- See `PROJECT_STATE.md` for current implementation status
- See `TODO.md` for task tracking

## License

Private repository - All rights reserved
