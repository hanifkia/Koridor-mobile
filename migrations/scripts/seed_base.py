"""
Shared seed utilities.
"""

from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_DNS
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Get database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ecolos_db",
)

if "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

NOW = datetime.now(timezone.utc)


def deterministic_uuid(namespace: str, name: str) -> str:
    """Generate deterministic UUID using UUID5."""
    return str(uuid5(NAMESPACE_DNS, f"{namespace}.seed.{name}"))


def role_uuid(role_name: str) -> str:
    """Generate UUID for role."""
    return deterministic_uuid("ecolos", f"role.{role_name.lower()}")


def user_uuid(username: str) -> str:
    """Generate UUID for user."""
    return deterministic_uuid("ecolos", f"user.{username}")


def permission_uuid(code: str) -> str:
    """Generate UUID for permission."""
    return deterministic_uuid("ecolos", f"permission.{code}")


def courier_uuid(username: str) -> str:
    """Generate UUID for courier."""
    return deterministic_uuid("ecolos", f"courier.{username}")


def hub_uuid(name: str) -> str:
    """Generate UUID for hub."""
    return deterministic_uuid("ecolos", f"hub.{name.lower()}")


def vehicle_uuid(username: str, vehicle_number: int = 1) -> str:
    """Generate UUID for vehicle."""
    return deterministic_uuid("ecolos", f"vehicle.{username}.{vehicle_number}")


def billing_customer_uuid(username: str) -> str:
    """Generate UUID for billing customer."""
    return deterministic_uuid("ecolos", f"billing_customer.{username}")


def plan_uuid(tier: str) -> str:
    """Generate UUID for plan."""
    return deterministic_uuid("ecolos", f"plan.{tier.lower()}")


def plan_price_uuid(tier: str, currency: str) -> str:
    """Generate UUID for plan price."""
    return deterministic_uuid("ecolos", f"plan_price.{tier.lower()}.{currency.lower()}")
