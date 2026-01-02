# Backend

Python 3.11 backend for TikTok Keyword Momentum Tracker.

## Structure

```
backend/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database connection
│   │   └── models/          # SQLAlchemy models
│   │   └── api/             # API routes
│   │   └── services/        # Business logic
│   │   └── utils/           # Utilities
│   └── scripts/             # Management scripts
├── tests/                   # Test files
├── alembic/                 # Database migrations
└── requirements.txt
```

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start development server:
```bash
uvicorn src.app.main:app --reload
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Secret key for JWT tokens
- `SMTP_HOST` - SMTP server for magic links
- `SMTP_PORT` - SMTP port
- `SMTP_USER` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret

