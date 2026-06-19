"""
Seed Couriers — Creates courier profiles linked to users.
"""

import asyncio
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, courier_uuid, user_uuid

COURIERS = [
    {
        "username": "courier_john",
        "vehicle_type": "BIKE",
        "country": "United States",
        "state": "NY",
        "city": "New York",
    },
    {
        "username": "courier_maria",
        "vehicle_type": "CAR",
        "country": "United States",
        "state": "CA",
        "city": "Los Angeles",
    },
    {
        "username": "courier_ahmed",
        "vehicle_type": "VAN",
        "country": "United Kingdom",
        "state": "England",
        "city": "London",
    },
]

# ✅ FIXED: Removed CAST for vehicle_type enum
INSERT_COURIER_SQL = text(
    """
    INSERT INTO couriers (id, user_id, vehicle_type, country, state, city, created_at, updated_at)
    VALUES (
        CAST(:id AS uuid),
        CAST(:user_id AS uuid),
        :vehicle_type,
        :country,
        :state,
        :city,
        :created_at,
        :updated_at
    )
    ON CONFLICT (user_id) DO NOTHING
"""
)

CHECK_COURIER_SQL = text(
    "SELECT id FROM couriers WHERE user_id = CAST(:user_id AS uuid)"
)


async def seed_couriers() -> bool:
    """Seed courier profiles."""
    print("🚚 Seeding couriers...")
    seeded = skipped = 0

    async with AsyncSessionLocal() as session:
        for courier in COURIERS:
            try:
                result = await session.execute(
                    CHECK_COURIER_SQL, {"user_id": user_uuid(courier["username"])}
                )
                if result.fetchone():
                    print(f"   ⏭️  '{courier['username']}' already exists — skipping")
                    skipped += 1
                    continue

                await session.execute(
                    INSERT_COURIER_SQL,
                    {
                        "id": courier_uuid(courier["username"]),
                        "user_id": user_uuid(courier["username"]),
                        "vehicle_type": courier[
                            "vehicle_type"
                        ],  # ✅ Pass string directly
                        "country": courier["country"],
                        "state": courier["state"],
                        "city": courier["city"],
                        "created_at": NOW,
                        "updated_at": NOW,
                    },
                )
                await session.commit()
                print(
                    f"   ✅ '{courier['username']}' ({courier['vehicle_type']}) created"
                )
                seeded += 1

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ '{courier['username']}' failed: {exc}")

    print(f"   Couriers — created: {seeded}, skipped: {skipped}\n")
    return seeded > 0 or skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_couriers())
