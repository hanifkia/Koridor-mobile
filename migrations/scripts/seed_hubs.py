"""
Seed Hubs — Creates distribution center hubs for couriers.
"""

import asyncio
from datetime import timedelta, time
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, hub_uuid, courier_uuid, user_uuid

HUBS = [
    {
        "name": "Main Hub",
        "courier_username": "courier_john",
        "lat": 40.7128,
        "lon": -74.0060,
        "address": "123 Main Street, New York, NY 10001",
        "setup_time": timedelta(minutes=15),
        "service_time": timedelta(minutes=5),
        # ✅ FIXED: Use time objects instead of strings
        "shifts": [
            {"start_time": time(8, 0), "finish_time": time(18, 0)},
            {"start_time": time(18, 0), "finish_time": time(22, 0)},
        ],
    },
    {
        "name": "Downtown Hub",
        "courier_username": "courier_maria",
        "lat": 34.0522,
        "lon": -118.2437,
        "address": "456 Downtown Ave, Los Angeles, CA 90001",
        "setup_time": timedelta(minutes=20),
        "service_time": timedelta(minutes=5),
        # ✅ FIXED: Use time objects instead of strings
        "shifts": [
            {"start_time": time(6, 0), "finish_time": time(16, 0)},
        ],
    },
    {
        "name": "Central Hub",
        "courier_username": "courier_ahmed",
        "lat": 51.5074,
        "lon": -0.1278,
        "address": "789 Central Road, London, England",
        "setup_time": timedelta(minutes=10),
        "service_time": timedelta(minutes=5),
        # ✅ FIXED: Use time objects instead of strings
        "shifts": [
            {"start_time": time(7, 0), "finish_time": time(19, 0)},
        ],
    },
]

INSERT_HUB_SQL = text(
    """
    INSERT INTO hubs (
        id, courier_id, name, lat, lon, address,
        setup_time, service_time, return_to_hub,
        created_at, updated_at
    ) VALUES (
        CAST(:id AS uuid),
        CAST(:courier_id AS uuid),
        :name,
        :lat,
        :lon,
        :address,
        CAST(:setup_time AS interval),
        CAST(:service_time AS interval),
        :return_to_hub,
        :created_at,
        :updated_at
    )
    ON CONFLICT DO NOTHING
"""
)

# ✅ FIXED: Removed CAST for time values - pass time objects directly
INSERT_HUB_SHIFT_SQL = text(
    """
    INSERT INTO hub_shifts (id, terminal_id, start_time, finish_time, created_at, updated_at)
    VALUES (
        CAST(:id AS uuid),
        CAST(:terminal_id AS uuid),
        :start_time,
        :finish_time,
        :created_at,
        :updated_at
    )
    ON CONFLICT DO NOTHING
"""
)

CHECK_HUB_SQL = text("SELECT id FROM hubs WHERE name = :name")


async def seed_hubs() -> bool:
    """Seed distribution hubs."""
    print("🏢 Seeding hubs...")
    seeded = skipped = 0

    async with AsyncSessionLocal() as session:
        for hub in HUBS:
            try:
                result = await session.execute(CHECK_HUB_SQL, {"name": hub["name"]})
                if result.fetchone():
                    print(f"   ⏭️  Hub '{hub['name']}' already exists — skipping")
                    skipped += 1
                    continue

                terminal_id = hub_uuid(hub["name"])

                await session.execute(
                    INSERT_HUB_SQL,
                    {
                        "id": terminal_id,
                        "courier_id": courier_uuid(hub["courier_username"]),
                        "name": hub["name"],
                        "lat": hub["lat"],
                        "lon": hub["lon"],
                        "address": hub["address"],
                        "setup_time": hub["setup_time"],
                        "service_time": hub["service_time"],
                        "return_to_hub": True,
                        "created_at": NOW,
                        "updated_at": NOW,
                    },
                )

                # Insert shifts
                for i, shift in enumerate(hub.get("shifts", [])):
                    await session.execute(
                        INSERT_HUB_SHIFT_SQL,
                        {
                            "id": hub_uuid(f"{hub['name']}_shift_{i}"),
                            "terminal_id": terminal_id,
                            "start_time": shift[
                                "start_time"
                            ],  # ✅ time object, not string
                            "finish_time": shift[
                                "finish_time"
                            ],  # ✅ time object, not string
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )

                await session.commit()
                print(f"   ✅ Hub '{hub['name']}' ({hub['lat']}, {hub['lon']}) created")
                seeded += 1

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ Hub '{hub['name']}' failed: {exc}")

    print(f"   Hubs — created: {seeded}, skipped: {skipped}\n")
    return seeded > 0 or skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_hubs())
