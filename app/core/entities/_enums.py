from enum import Enum


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class RoleType(str, Enum):
    """System roles for RBAC"""

    ADMIN = "admin"
    COURIER = "courier"
    RECIPIENT = "recipient"


class PermissionAction(str, Enum):
    """CRUD operations for permission model"""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class VehicleType(str, Enum):
    """Vehicle classifications for routing"""

    BIKE = "bike"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"
    TRAILER = "trailer"
    E_CAR = "e-car"
    E_BIKE = "e-bike"
    COLD_CAR = "cold-car"


class FuelType(str, Enum):
    """Vehicle fuel types"""

    DIESEL = "diesel"
    PETROL = "petrol"
    ELECTRICAL = "electrical"
    HYBRID = "hybrid"


class EmissionFactor(int, Enum):
    """CO2 emissions per km"""

    DIESEL = 2640
    PETROL = 2392
    ELECTRICAL = 0
    HYBRID = 1236


class OrderStatusTypes(Enum):
    REGISTERED = "registered"
    SCHEDULED = "scheduled"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    UNASSIGNED = "unassigned"


class RouteStatesType(Enum):
    SCHEDULED = "scheduled"
    LOADING = "loading"
    ONGOING = "ongoing"
    RETURNTOHUB = "return_to_hub"
    FINISHED = "finished"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value


class RouteCreatedType(Enum):
    SUGGESTED = "suggested"
    RECALCULATED = "recalculated"
    VROOM = "vroom"
    MANUAL = "manual"
    CUSTOM = "custom"
    TRENDROUTE = "trendroute"

    def __str__(self) -> str:
        return self.value


class MissionStatusType(Enum):
    """Mission status/outcome"""

    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    DELIVERED = "delivered"
    DELIVERED_WITH_DELAY = "delivered_with_delay"
    UNDELIVERED_UNREACHABLE_ADDRESS = "undelivered_unreachable_address"
    UNDELIVERED_UNREACHABLE_CUSTOMER = "undelivered_unreachable_customer"
    UNDELIVERED_UNREACHABLE_DISPATCH = "undelivered_unreachable_dispatch"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value


class MissionPostponedType(Enum):
    BY_ADDRESS = "by_address"
    BY_CUSTOMER = "by_customer"
    BY_DISPATCH = "by_dispatch"

    def __str__(self) -> str:
        return self.value


class CostFunctionPlanType(Enum):
    Minimizing_Completion_Time = "Minimizing_Completion_Time"
    Minimizing_Eco_Routing = "Minimizing_Eco_Routing"
    Minimizing_Cost = "Minimizing_Cost"

    def __str__(self) -> str:
        return self.value


class CourierStatesType(Enum):
    IDLE = "idle"
    ARRIVEDATHUB = "arrived_at_hub"
    STARTLOADING = "start_loading"
    STARTROUTE = "start_route"
    ARRIVEDATDELIVERY = "arrived_at_delivery"  # mission
    DELIVERED = "delivered"  # mission
    UNDELIVERED = "undelivered"  # mission
    STARTNEXTDELIVERY = "start_next_delivery"
    RETURNTOHUB = "return_to_hub"
    FINISHROUTE = "finish_route"

    def __str__(self) -> str:
        return self.value


class UndeliveredMissionStatus(Enum):
    Undelivered_Unreachable_Address = "Undelivered_Unreachable_Address"
    Undelivered_Unreachable_Customer = "Undelivered_Unreachable_Customer"
    Undelivered_Unreachable_Dispatch = "Undelivered_Unreachable_Dispatch"


# ------------------------------------------------------------------------
# -------------------- Billing and Subscription Enums --------------------
# ------------------------------------------------------------------------


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    PAUSED = "paused"


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class Currency(str, Enum):
    SEK = "sek"
    EUR = "eur"
    USD = "usd"
    GBP = "gbp"
    NOK = "nok"
    DKK = "dkk"
    OMR = "omr"
    UAD = "uad"
