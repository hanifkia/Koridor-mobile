"""
Seed RBAC Permissions — Creates resource permissions.
"""

import asyncio
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, permission_uuid

PERMISSIONS = [
    # Users
    {
        "table_name": "users",
        "actions": ["read", "create", "update", "delete"],
    },
    # Roles
    {
        "table_name": "roles",
        "actions": ["read", "create", "update", "delete"],
    },
    # Permissions
    {
        "table_name": "permissions",
        "actions": ["read", "manage"],
    },
    # Couriers
    {
        "table_name": "couriers",
        "actions": ["read", "create", "update", "delete"],
    },
    # Hubs
    {
        "table_name": "hubs",
        "actions": ["read", "create", "update", "delete"],
    },
    # Vehicles
    {
        "table_name": "vehicles",
        "actions": ["read", "create", "update", "delete"],
    },
]

INSERT_PERM_SQL = text(
    """
    INSERT INTO permissions (id, table_name, actions, created_at, updated_at)
    VALUES (CAST(:id AS uuid), :table_name, :actions, :now, :now)
    ON CONFLICT (table_name) DO NOTHING
"""
)

CHECK_PERM_SQL = text("SELECT id FROM permissions WHERE table_name = :table_name")


async def seed_permissions() -> bool:
    """Seed permissions."""
    print("🔒 Seeding permissions...")
    seeded = skipped = 0

    async with AsyncSessionLocal() as session:
        for perm in PERMISSIONS:
            try:
                result = await session.execute(
                    CHECK_PERM_SQL, {"table_name": perm["table_name"]}
                )
                if result.fetchone():
                    print(f"   ⏭️  '{perm['table_name']}' already exists — skipping")
                    skipped += 1
                    continue

                await session.execute(
                    INSERT_PERM_SQL,
                    {
                        "id": permission_uuid(perm["table_name"]),
                        "table_name": perm["table_name"],
                        "actions": perm["actions"],
                        "now": NOW,
                    },
                )
                await session.commit()
                print(f"   ✅ '{perm['table_name']}' created")
                seeded += 1

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ '{perm['table_name']}' failed: {exc}")

    print(f"   Permissions — created: {seeded}, skipped: {skipped}\n")
    return seeded > 0 or skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_permissions())
