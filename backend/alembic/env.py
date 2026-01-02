"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the Base and models
from app.models.base import Base
from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.models.user import User
from app.models.subscription import Subscription
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with the actual database URL from settings
# Supports both SQLite and PostgreSQL
database_url = settings.database_url

# SQLite requires special handling for Alembic
if database_url.startswith("sqlite"):
    # Use check_same_thread=False for SQLite
    config.set_main_option("sqlalchemy.url", database_url.replace("sqlite:///", "sqlite:///./"))
else:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    
    # SQLite-specific configuration
    if url.startswith("sqlite"):
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            render_as_batch=True,  # Required for SQLite
        )
    else:
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.get_main_option("sqlalchemy.url")
    
    # SQLite requires special connection args
    if url and url.startswith("sqlite"):
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args={"check_same_thread": False},
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        # SQLite-specific configuration
        if url and url.startswith("sqlite"):
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,  # Required for SQLite
            )
        else:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

