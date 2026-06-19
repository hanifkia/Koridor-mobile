"""
Seed RBAC Roles — Creates system roles.
"""

import asyncio
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, role_uuid

ROLES = [
    {"name": "ADMIN", "description": "Administrator with full system access"},
    {"name": "COURIER", "description": "Courier user for delivery operations"},
    {"name": "RECIPIENT", "description": "Recipient user for parcel deliveries"},
]

# ✅ FIXED: Removed CAST for enum, pass string directly
INSERT_ROLE_SQL = text(
    """
    INSERT INTO roles (id, name, description, created_at, updated_at)
    VALUES (CAST(:id AS uuid), :name, :description, :now, :now)
    ON CONFLICT DO NOTHING
"""
)

# ✅ FIXED: Removed CAST from WHERE clause
CHECK_ROLE_SQL = text("SELECT id FROM roles WHERE name = :name")


async def seed_roles() -> bool:
    """Seed initial roles."""
    print("🔑 Seeding roles...")
    seeded = skipped = 0

    async with AsyncSessionLocal() as session:
        for role in ROLES:
            try:
                result = await session.execute(CHECK_ROLE_SQL, {"name": role["name"]})
                if result.fetchone():
                    print(f"   ⏭️  '{role['name']}' already exists — skipping")
                    skipped += 1
                    continue

                await session.execute(
                    INSERT_ROLE_SQL,
                    {
                        "id": role_uuid(role["name"]),
                        "name": role["name"],  # ✅ Pass string, SQLAlchemy converts it
                        "description": role["description"],
                        "now": NOW,
                    },
                )
                await session.commit()
                print(f"   ✅ '{role['name']}' created")
                seeded += 1

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ '{role['name']}' failed: {exc}")

    print(f"   Roles — created: {seeded}, skipped: {skipped}\n")
    return seeded > 0 or skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_roles())
