"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.utils.logging import setup_logging
from app.api import keywords, archive, auth, stripe

# Setup logging
logger = setup_logging()

app = FastAPI(
    title="TikTok Keyword Momentum Tracker API",
    description="API for tracking TikTok keyword momentum",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware
# In production, restrict to actual domain
# In development, allow localhost
allowed_origins = []
if settings.debug:
    # Development: allow localhost
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
else:
    # Production: restrict to domain
    allowed_origins = [
        "https://trendearly.xyz",
        "https://www.trendearly.xyz",
        # Also allow frontend_url if set (for magic links)
        settings.frontend_url,
    ]
    # Remove duplicates and filter out localhost in production
    allowed_origins = [
        origin
        for origin in set(allowed_origins)
        if origin and not origin.startswith("http://localhost")
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
app.include_router(keywords.router)
app.include_router(archive.router)
app.include_router(auth.router)
app.include_router(stripe.router)

# Scheduler instance (will be initialized on startup if enabled)
scheduler = None


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting TikTok Keyword Momentum Tracker API")

    # Start scheduler if enabled (can be disabled for development)
    if settings.debug:
        logger.info("Scheduler disabled in debug mode")
    else:
        try:
            from app.scheduler import start_scheduler

            global scheduler
            scheduler = start_scheduler()
            logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    if scheduler:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "ok", "message": "TikTok Keyword Momentum Tracker API"}


@app.get("/health")
async def health():
    """Health check endpoint (legacy, use /api/health)."""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    """API health check endpoint for monitoring."""
    return {"status": "healthy", "service": "api"}
