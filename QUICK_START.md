# Quick Start Guide

Get the application running locally for development.

## Prerequisites

- Python 3.11+
- Node.js 18+
- SQLite (built into Python) - **No setup needed for MVP!**
- PostgreSQL 14+ (optional, for production)
- Git

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Minimum required variables:**

```bash
# SQLite (default - no setup needed!)
DATABASE_URL=sqlite:///./data.db
# OR PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/tiktok_keywords

SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Set Up Database

**SQLite (MVP - Recommended):**

```bash
# No setup needed! Just run migrations
alembic upgrade head
# Database file (data.db) will be created automatically
```

**PostgreSQL (Optional):**

```bash
# Create database
createdb tiktok_keywords

# Run migrations
alembic upgrade head
```

### 5. Start Backend

```bash
uvicorn src.app.main:app --reload
```

Backend will be available at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
# Edit .env.local
```

**Required variables:**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Frontend

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Testing the Application

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Get keywords
curl http://localhost:8000/api/keywords?limit=10
```

### 2. Test Pipeline (Optional)

```bash
cd backend
python -m scripts.run_daily_pipeline --max-keywords 5
```

### 3. Test Authentication

```bash
# Request magic link
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Development Tips

- Backend auto-reloads on code changes (--reload flag)
- Frontend hot-reloads automatically
- Use `DEBUG=True` to disable scheduler in development
- Check logs in terminal for errors
- Use Postman or curl to test API endpoints

## Common Issues

**Database connection error:**

- SQLite: Check file permissions, ensure directory exists
- PostgreSQL: Verify PostgreSQL is running, check DATABASE_URL format, ensure database exists

**Port already in use:**

- Change port in uvicorn command
- Kill process using port: `lsof -ti:8000 | xargs kill`

**Module not found:**

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

- See `DEPLOYMENT.md` for production deployment
- See `BUILD_SPEC.md` for full specifications
- See `PROJECT_STATE.md` for current status
