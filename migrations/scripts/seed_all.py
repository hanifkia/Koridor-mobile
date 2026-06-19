"""
Seed All — Master orchestrator for database seeding.
"""

import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

# Import seed functions
from .seed_roles import seed_roles
from .seed_permissions import seed_permissions
from .seed_users import seed_users
from .seed_couriers import seed_couriers
from .seed_hubs import seed_hubs
from .seed_billing import seed_billing  # ✅ NEW

DIV = "=" * 80

SEED_STEPS = [
    ("1 / 6", "🔑 Roles", seed_roles),
    ("2 / 6", "🔒 Permissions", seed_permissions),
    ("3 / 6", "👥 Users", seed_users),
    ("4 / 6", "🚚 Couriers", seed_couriers),
    ("5 / 6", "🏢 Hubs", seed_hubs),
    ("6 / 6", "💳 Billing", seed_billing),  # ✅ NEW
]

TEST_ACCOUNTS = [
    ("admin_user", "AdminPass@123!", "ADMIN"),
    ("courier_john", "CourierPass@123!", "COURIER"),
    ("courier_maria", "CourierPass@123!", "COURIER"),
    ("courier_ahmed", "CourierPass@123!", "COURIER"),
    ("recipient_jane", "RecipientPass@123!", "RECIPIENT"),
]


async def seed_all() -> bool:
    """Execute all seed scripts in order."""
    print(f"\n{DIV}")
    print("🌱 Full Database Seed")
    print(DIV)

    results = []

    for step_num, step_name, step_func in SEED_STEPS:
        print(f"\n{DIV}")
        print(f"STEP {step_num} — {step_name}")
        print(DIV)

        try:
            success = await step_func()
            results.append((step_name, success))
        except Exception as e:
            logger.error(f"❌ {step_name} failed: {str(e)}", exc_info=True)
            results.append((step_name, False))

    # Summary
    print(f"\n{DIV}")
    failed = [name for name, success in results if not success]

    if failed:
        print(f"❌ {len(failed)} step(s) failed:")
        for name in failed:
            print(f"   • {name}")
        print(DIV)
        return False

    print("✅ Seeding complete!")
    print(f"\n🔐 Test Accounts:")
    for username, password, role in TEST_ACCOUNTS:
        print(f"   {username:<20} / {password:<20} ({role})")

    print(f"\n💳 Billing Plans:")
    print(f"   {'FREE':<15} — 50 deliveries/mo   (€0.00)")
    print(f"   {'STARTER':<15} — 300 deliveries/mo  (€29.00)")
    print(f"   {'PROFESSIONAL':<15} — 5000 deliveries/mo (€79.00)")
    print(f"   {'ENTERPRISE':<15} — unlimited          (€299.00)")

    print(DIV + "\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(seed_all())
    sys.exit(0 if success else 1)
