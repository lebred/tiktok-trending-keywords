"""
Application configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    # For MVP: Use SQLite (sqlite:///data.db)
    # For Production: Use PostgreSQL (postgresql://...)
    database_url: str = "sqlite:///./data.db"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email (for magic links)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id: Optional[str] = None

    # App
    app_name: str = "TikTok Keyword Momentum Tracker"
    debug: bool = False

    # Frontend URL (for magic links)
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
