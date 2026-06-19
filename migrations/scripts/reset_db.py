"""
Reset Database — Drops and recreates ALL tables.

⚠️  WARNING: Destroys all data. Development/CI only.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.adapters.database.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ecolos_db",
)


async def reset_database() -> None:
    """Reset the database."""
    print("⚠️  WARNING: This will permanently delete ALL data!")
    confirm = input("Type 'yes' to continue: ").strip()

    if confirm.lower() != "yes":
        print("❌ Cancelled — no changes made.")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)

    try:
        print("\n🗑️  Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("   ✅ Done.")

        print("🔨 Re-creating all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   ✅ Done.")

        print("\n✅ Database reset complete.")
        print("   Next steps:")
        print("     python seed_all.py  — seed initial data")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_database())
