"""Alembic environment configuration.

This file is run when the alembic command is executed.
It needs to:
1. Import all ORM models so Base.metadata includes them
2. Compare database schema with Base.metadata to detect changes
3. Generate migration files
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Add app to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# CRITICAL: Import all models BEFORE using Base.metadata
from app.adapters.database.models import Base

# Get config
config = context.config
target_metadata = Base.metadata

# Logging
if config.config_file_name is not None:
    from logging.config import fileConfig

    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ecolos_db",
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without executing)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_sync_migrations(connection) -> None:
    """Execute migrations in sync context (called via run_sync)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations asynchronously (uses asyncpg)."""
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        echo=False,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_sync_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against live database)."""
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_async_migrations())


# Execute based on environment
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
