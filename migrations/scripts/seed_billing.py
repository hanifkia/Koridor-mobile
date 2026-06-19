"""
Seed Billing — Creates subscription plans and prices.
"""

import asyncio
from decimal import Decimal
from sqlalchemy import text
from .seed_base import AsyncSessionLocal, NOW, plan_uuid, plan_price_uuid


# ──────────────────────────────────────────────
# Plans
# ──────────────────────────────────────────────
PLANS = [
    {
        "tier": "FREE",
        "name": "Free",
        "monthly_delivery_limit": 50,
        "is_active": True,
        "prices": [
            {
                "currency": "EUR",
                "amount": Decimal("0.00"),
                "stripe_price_id": "price_free_eur_monthly",
            },
            {
                "currency": "USD",
                "amount": Decimal("0.00"),
                "stripe_price_id": "price_free_usd_monthly",
            },
        ],
    },
    {
        "tier": "STARTER",
        "name": "Starter",
        "monthly_delivery_limit": 300,
        "is_active": True,
        "prices": [
            {
                "currency": "EUR",
                "amount": Decimal("29.00"),
                "stripe_price_id": "price_starter_eur_monthly",
            },
            {
                "currency": "USD",
                "amount": Decimal("32.00"),
                "stripe_price_id": "price_starter_usd_monthly",
            },
        ],
    },
    {
        "tier": "PROFESSIONAL",
        "name": "Professional",
        "monthly_delivery_limit": 5000,
        "is_active": True,
        "prices": [
            {
                "currency": "EUR",
                "amount": Decimal("79.00"),
                "stripe_price_id": "price_pro_eur_monthly",
            },
            {
                "currency": "USD",
                "amount": Decimal("87.00"),
                "stripe_price_id": "price_pro_usd_monthly",
            },
        ],
    },
    {
        "tier": "ENTERPRISE",
        "name": "Enterprise",
        "monthly_delivery_limit": 99999,
        "is_active": True,
        "prices": [
            {
                "currency": "EUR",
                "amount": Decimal("299.00"),
                "stripe_price_id": "price_ent_eur_monthly",
            },
            {
                "currency": "USD",
                "amount": Decimal("349.00"),
                "stripe_price_id": "price_ent_usd_monthly",
            },
        ],
    },
]


# ──────────────────────────────────────────────
# SQL Statements
# ──────────────────────────────────────────────
CHECK_PLAN_SQL = text("SELECT id FROM plans WHERE tier = :tier")

INSERT_PLAN_SQL = text(
    """
    INSERT INTO plans (
        id, name, tier, stripe_product_id,
        monthly_delivery_limit, is_active,
        created_at, updated_at
    ) VALUES (
        CAST(:id AS uuid),
        :name,
        :tier,
        :stripe_product_id,
        :monthly_delivery_limit,
        :is_active,
        :created_at,
        :updated_at
    )
    ON CONFLICT DO NOTHING
"""
)

CHECK_PRICE_SQL = text(
    "SELECT id FROM plan_prices WHERE stripe_price_id = :stripe_price_id"
)

INSERT_PRICE_SQL = text(
    """
    INSERT INTO plan_prices (
        id, plan_id, currency, amount,
        stripe_price_id, billing_interval, is_active,
        created_at, updated_at
    ) VALUES (
        CAST(:id AS uuid),
        CAST(:plan_id AS uuid),
        :currency,
        :amount,
        :stripe_price_id,
        :billing_interval,
        :is_active,
        :created_at,
        :updated_at
    )
    ON CONFLICT DO NOTHING
"""
)


async def seed_billing() -> bool:
    """Seed billing plans and prices."""
    print("💳 Seeding billing plans...")
    plans_seeded = plans_skipped = 0
    prices_seeded = prices_skipped = 0

    async with AsyncSessionLocal() as session:
        for plan in PLANS:
            try:
                # Check if plan exists
                result = await session.execute(CHECK_PLAN_SQL, {"tier": plan["tier"]})
                existing = result.fetchone()

                if existing:
                    print(
                        f"   ⏭️  Plan '{plan['name']}' ({plan['tier']}) already exists — skipping"
                    )
                    plans_skipped += 1
                    pid = str(existing[0])
                else:
                    pid = plan_uuid(plan["tier"])

                    await session.execute(
                        INSERT_PLAN_SQL,
                        {
                            "id": pid,
                            "name": plan["name"],
                            "tier": plan["tier"],
                            "stripe_product_id": f"prod_{plan['tier'].lower()}",
                            "monthly_delivery_limit": plan["monthly_delivery_limit"],
                            "is_active": plan["is_active"],
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )
                    await session.commit()
                    print(f"   ✅ Plan '{plan['name']}' ({plan['tier']}) created")
                    plans_seeded += 1

                # Seed prices for this plan
                for price in plan["prices"]:
                    try:
                        result = await session.execute(
                            CHECK_PRICE_SQL,
                            {"stripe_price_id": price["stripe_price_id"]},
                        )
                        if result.fetchone():
                            print(
                                f"      ⏭️  Price {price['amount']} {price['currency']} "
                                f"already exists — skipping"
                            )
                            prices_skipped += 1
                            continue

                        await session.execute(
                            INSERT_PRICE_SQL,
                            {
                                "id": plan_price_uuid(plan["tier"], price["currency"]),
                                "plan_id": pid,
                                "currency": price["currency"],
                                "amount": price["amount"],
                                "stripe_price_id": price["stripe_price_id"],
                                "billing_interval": "month",
                                "is_active": True,
                                "created_at": NOW,
                                "updated_at": NOW,
                            },
                        )
                        await session.commit()
                        print(
                            f"      ✅ Price {price['amount']} {price['currency']} created"
                        )
                        prices_seeded += 1

                    except Exception as exc:
                        await session.rollback()
                        print(
                            f"      ❌ Price {price['amount']} {price['currency']} "
                            f"failed: {exc}"
                        )

            except Exception as exc:
                await session.rollback()
                print(f"   ❌ Plan '{plan['name']}' failed: {exc}")

    print(f"   Plans  — created: {plans_seeded}, skipped: {plans_skipped}")
    print(f"   Prices — created: {prices_seeded}, skipped: {prices_skipped}\n")
    return plans_seeded > 0 or plans_skipped > 0


if __name__ == "__main__":
    asyncio.run(seed_billing())
