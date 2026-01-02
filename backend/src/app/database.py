"""
Database connection and session management.

Supports both SQLite (for MVP) and PostgreSQL (for production).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from app.config import settings
from app.models.base import Base

# Configure SQLite for foreign key support
if settings.database_url.startswith("sqlite"):
    # Enable foreign keys for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Use check_same_thread=False for SQLite (required for FastAPI)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
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

