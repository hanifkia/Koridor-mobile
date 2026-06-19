"""ORM Models package - centralized imports."""

# IMPORTANT: Import order matters!
# 1. First import base to avoid circular dependencies
from app.adapters.database.models.base import (
    Base,
    TimeStampMixin,
    _now,
)

# 2. Then import all model modules
# Each module uses string references, so no circular imports
from app.adapters.database.models.auth import (
    PermissionORM,
    RoleORM,
    PermissionRoleORM,
    UserORM,
    UserAvatarORM,
    RefreshTokenORM,
    PasswordResetCodeORM,
    UserVerificationTokenORM,
)

from app.adapters.database.models.courier import (
    CourierORM,
    CourierCurrentStateORM,
)

from app.adapters.database.models.hub import (
    HubORM,
    HubShiftORM,
)

from app.adapters.database.models.order import (
    OrderORM,
    RecipientORM,
)

from app.adapters.database.models.route import (
    RouteORM,
)

from app.adapters.database.models.mission import (
    MissionORM,
)

from app.adapters.database.models.vehicle import (
    VehicleORM,
)

from app.adapters.database.models.billing import (
    BillingCustomerORM,
    PlanORM,
    PlanPriceORM,
    SubscriptionORM,
    UsageRecordORM,
    PaymentORM,
    InvoiceORM,
)

__all__ = [
    # Base
    "Base",
    "TimeStampMixin",
    "_now",
    # Auth
    "PermissionORM",
    "RoleORM",
    "PermissionRoleORM",
    "UserORM",
    "UserAvatarORM",
    "RefreshTokenORM",
    "PasswordResetCodeORM",
    "UserVerificationTokenORM",
    # Courier
    "CourierORM",
    "CourierCurrentStateORM",
    # Hub
    "HubORM",
    "HubShiftORM",
    # Order
    "OrderORM",
    "RecipientORM",
    # Route
    "RouteORM",
    # Mission
    "MissionORM",
    # Vehicle
    "VehicleORM",
    # Billing
    "BillingCustomerORM",
    "PlanORM",
    "PlanPriceORM",
    "SubscriptionORM",
    "UsageRecordORM",
    "PaymentORM",
    "InvoiceORM",
]
