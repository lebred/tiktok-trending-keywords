#!/usr/bin/env python3
"""
Script to run database migrations.

Usage:
    python -m scripts.migrate [upgrade|downgrade] [revision]
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alembic.config import Config
from alembic import command
from app.config import settings

def main():
    """Run database migrations."""
    alembic_cfg = Config("alembic.ini")
    
    # Override sqlalchemy.url with actual database URL
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        command.downgrade(alembic_cfg, revision)
    else:
        revision = sys.argv[1] if len(sys.argv) > 1 else "head"
        command.upgrade(alembic_cfg, revision)

if __name__ == "__main__":
    main()

