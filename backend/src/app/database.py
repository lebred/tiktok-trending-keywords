"""
Database connection and session management.

Supports both SQLite (for MVP) and PostgreSQL (for production).

SQLite Configuration:
- check_same_thread=False: Required for FastAPI multi-threading
- StaticPool: Single connection pool for file-based SQLite
- PRAGMA foreign_keys=ON: Enforced on every connection
- WAL mode: Recommended for better concurrency (set via PRAGMA journal_mode=WAL)

PostgreSQL Configuration:
- pool_pre_ping: Verify connections before using
- Standard connection pooling
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool, NullPool

from app.config import settings
from app.models.base import Base

# Configure SQLite for foreign key support and thread safety
if settings.database_url.startswith("sqlite"):
    # Enable foreign keys for SQLite (must be done per connection)
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas on connection."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # Enable WAL mode for better concurrency (optional but recommended)
        # cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    # SQLite configuration for FastAPI
    # StaticPool: Single connection pool (appropriate for file-based SQLite)
    # check_same_thread=False: Required for FastAPI's async/threading model
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Single connection pool for SQLite
        pool_pre_ping=False,  # Not needed for SQLite
        echo=settings.debug,
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)
