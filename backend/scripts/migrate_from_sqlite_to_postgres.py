#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL.

Usage:
    python -m scripts.migrate_from_sqlite_to_postgres sqlite:///data.db postgresql://...
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.models.user import User
from app.models.subscription import Subscription

def migrate_data(sqlite_url: str, postgres_url: str):
    """
    Migrate all data from SQLite to PostgreSQL.
    
    Args:
        sqlite_url: SQLite database URL
        postgres_url: PostgreSQL database URL
    """
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_db = SQLiteSession()
    postgres_db = PostgresSession()
    
    try:
        # Create tables in PostgreSQL
        Base.metadata.create_all(bind=postgres_engine)
        
        # Migrate keywords
        print("Migrating keywords...")
        keywords = sqlite_db.query(Keyword).all()
        for keyword in keywords:
            postgres_db.merge(Keyword(id=keyword.id, keyword=keyword.keyword))
        postgres_db.commit()
        print(f"Migrated {len(keywords)} keywords")
        
        # Migrate users
        print("Migrating users...")
        users = sqlite_db.query(User).all()
        for user in users:
            postgres_db.merge(User(
                id=user.id,
                email=user.email,
                subscription_tier=user.subscription_tier,
                stripe_customer_id=user.stripe_customer_id,
            ))
        postgres_db.commit()
        print(f"Migrated {len(users)} users")
        
        # Migrate subscriptions
        print("Migrating subscriptions...")
        subscriptions = sqlite_db.query(Subscription).all()
        for sub in subscriptions:
            postgres_db.merge(Subscription(
                id=sub.id,
                user_id=sub.user_id,
                stripe_subscription_id=sub.stripe_subscription_id,
                status=sub.status,
                current_period_end=sub.current_period_end,
            ))
        postgres_db.commit()
        print(f"Migrated {len(subscriptions)} subscriptions")
        
        # Migrate daily snapshots
        print("Migrating daily snapshots...")
        snapshots = sqlite_db.query(DailySnapshot).all()
        for snapshot in snapshots:
            postgres_db.merge(DailySnapshot(
                id=snapshot.id,
                keyword_id=snapshot.keyword_id,
                snapshot_date=snapshot.snapshot_date,
                momentum_score=snapshot.momentum_score,
                raw_score=snapshot.raw_score,
                lift_value=snapshot.lift_value,
                acceleration_value=snapshot.acceleration_value,
                novelty_value=snapshot.novelty_value,
                noise_value=snapshot.noise_value,
                google_trends_data=snapshot.google_trends_data,
            ))
        postgres_db.commit()
        print(f"Migrated {len(snapshots)} snapshots")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        postgres_db.rollback()
        raise
    finally:
        sqlite_db.close()
        postgres_db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.migrate_from_sqlite_to_postgres <sqlite_url> <postgres_url>")
        sys.exit(1)
    
    sqlite_url = sys.argv[1]
    postgres_url = sys.argv[2]
    
    migrate_data(sqlite_url, postgres_url)

