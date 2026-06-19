"""
Seed Users — Creates test user accounts with authentication.
"""

import asyncio
import bcrypt
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, user_uuid, role_uuid


def _hash(plain: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()


USERS = [
    {
        "username": "admin_user",
        "email": "admin@ecolos.local",
        "password": "AdminPass@123!",
        "first_name": "System",
        "last_name": "Administrator",
        "phone_number": "+1-555-0001",
        "role_name": "ADMIN",
        "timezone": "UTC",
    },
    {
        "username": "courier_john",
        "email": "john@courier.local",
        "password": "CourierPass@123!",
        "first_name": "John",
        "last_name": "Smith",
        "phone_number": "+1-555-0002",
        "role_name": "COURIER",
        "timezone": "America/New_York",
    },
    {
        "username": "courier_maria",
        "email": "maria@courier.local",
        "password": "CourierPass@123!",
        "first_name": "Maria",
        "last_name": "Garcia",
        "phone_number": "+1-555-0003",
        "role_name": "COURIER",
        "timezone": "America/Los_Angeles",
    },
    {
        "username": "courier_ahmed",
        "email": "ahmed@courier.local",
        "password": "CourierPass@123!",
        "first_name": "Ahmed",
        "last_name": "Hassan",
        "phone_number": "+1-555-0004",
        "role_name": "COURIER",
        "timezone": "Europe/London",
    },
    {
        "username": "recipient_jane",
        "email": "jane@recipient.local",
        "password": "RecipientPass@123!",
        "first_name": "Jane",
        "last_name": "Doe",
        "phone_number": "+1-555-0005",
        "role_name": "RECIPIENT",
        "timezone": "Europe/London",
    },
]

# ✅ FIXED: Removed CAST for status enum
INSERT_USER_SQL = text(
    """
    INSERT INTO users (
        id, username, email, password_hash,
        first_name, last_name, middle_name, phone_number,
        status, timezone, currency,
        is_email_verified, role_id,
        created_at, updated_at
    ) VALUES (
        CAST(:id AS uuid),
        :username,
        :email,
        :password_hash,
        :first_name,
        :last_name,
        :middle_name,
        :phone_number,
        :status,
        :timezone,
        :currency,
        :is_email_verified,
        CAST(:role_id AS uuid),
        :created_at,
        :updated_at
    )
    ON CONFLICT (username) DO NOTHING
"""
)

CHECK_USER_SQL = text("SELECT id FROM users WHERE username = :username")


async def seed_users() -> bool:
    """Seed test users."""
    print("👥 Seeding users...")
    seeded = skipped = 0

    async with AsyncSessionLocal() as session:
        for user in USERS:
            try:
                result = await session.execute(
                    CHECK_USER_SQL, {"username": user["username"]}
                )
                if result.fetchone():
                    print(f"   ⏭️  '{user['username']}' already exists — skipping")
                    skipped += 1
                    continue

                await session.execute(
                    INSERT_USER_SQL,
                    {
                        "id": user_uuid(user["username"]),
                        "username": user["username"],
                        "email": user["email"],
                        "password_hash": _hash(user["password"]),
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "middle_name": None,
                        "phone_number": user["phone_number"],
                        "status": "ACTIVE",  # ✅ Pass string directly
                        "timezone": user["timezone"],
                        "currency": "USD",
                        "is_email_verified": True,
                        "role_id": role_uuid(user["role_name"]),
                        "created_at": NOW,
                        "updated_at": NOW,
                    },
                )
                await session.commit()
                print(f"   ✅ '{user['username']}' ({user['role_name']}) created")
                seeded += 1

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ '{user['username']}' failed: {exc}")

    print(f"   Users — created: {seeded}, skipped: {skipped}\n")
    return seeded > 0 or skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_users())
