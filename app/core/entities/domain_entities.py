from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, date
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional, List

from app.core.entities import (
    UserStatus,
    RoleType,
    PermissionAction,
    VehicleType,
    FuelType,
    OrderStatusTypes,
    MissionStatusType,
    RouteStatesType,
    RouteCreatedType,
    MissionPostponedType,
    CourierStatesType,
    SubscriptionStatus,
    PlanTier,
    Currency,
    InvoiceStatus,
    PaymentStatus,
)


@dataclass
class Permission:
    """Permission domain entity"""

    id: UUID = field(default_factory=uuid4)
    table_name: str | None = None
    actions: list[PermissionAction] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def name(self) -> str:
        """Generate permission name from table and actions"""
        actions_str = "".join([a.value[0].upper() for a in self.actions])
        return f"{self.table_name}_{actions_str}" if actions_str else self.table_name


@dataclass
class Role:
    """Role domain entity for RBAC"""

    id: UUID = field(default_factory=uuid4)
    name: RoleType = RoleType.COURIER
    permissions: list[Permission] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def has_permission(self, table_name: str, action: PermissionAction) -> bool:
        """Check if role has specific permission"""
        return any(
            p.table_name == table_name and action in p.actions for p in self.permissions
        )

    def has_any_permission(self, table_name: str) -> bool:
        """Check if role has any permission on table"""
        return any(p.table_name == table_name for p in self.permissions)


@dataclass
class PermissionRole:
    """Composite domain entity for role-permission association"""

    role: Role
    permission: Permission
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None

    def __hash__(self) -> int:
        """Make dataclass hashable"""
        return hash((self.role.id, self.permission.id))

    def __eq__(self, other: object) -> bool:
        """Compare by role and permission IDs"""
        if not isinstance(other, PermissionRole):
            return NotImplemented
        return (
            self.role.id == other.role.id and self.permission.id == other.permission.id
        )

    def __repr__(self) -> str:
        return f"<PermissionRole(role={self.role.name.value}, permission={self.permission.name})>"


@dataclass
class UserAvatar:
    """User avatar domain entity"""

    # Required field FIRST (no default)
    user_id: UUID

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    file_name: str = ""
    file_path: str = ""
    file_type: str = ""
    file_size: int | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class User:
    """User domain entity with auth"""

    # Required fields FIRST (no defaults)
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone_number: str

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    middle_name: str | None = None
    status: UserStatus = UserStatus.INACTIVE
    role: Role | None = None
    avatar: UserAvatar | None = None
    timezone: str = "UTC"
    currency: str = "EUR"
    is_email_verified: bool = False
    email_verified_at: datetime | None = None
    is_terminal_setup_completed: bool = False
    is_courier_profile_completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def full_name(self) -> str:
        """Get user full name"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE

    def has_permission(self, table_name: str, action: PermissionAction) -> bool:
        """Check if user has permission through role"""
        if not self.role:
            return False
        return self.role.has_permission(table_name, action)


@dataclass
class UserVerificationToken:
    """User verification token domain entity for email verification"""

    user_id: UUID
    token: str
    expires_at: datetime

    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        from datetime import timezone

        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return f"<UserVerificationToken(user_id={self.user_id}, is_expired={self.is_expired()})>"


@dataclass
class Courier:
    """Courier domain entity"""

    # Required fields FIRST
    user_id: UUID
    vehicle_type: VehicleType

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    country: str | None = None
    state: str | None = None
    city: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Hub:
    """Hub (distribution center) domain entity"""

    # Required fields FIRST
    courier_id: UUID
    name: str

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    lat: float = 0.0
    lon: float = 0.0
    address: str | None = None
    setup_time: timedelta = field(default_factory=lambda: timedelta(minutes=0))
    service_time: timedelta = field(default_factory=lambda: timedelta(minutes=0))
    return_to_hub: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if not (-180 <= self.lat <= 180):
            raise ValueError("Latitude must be between -180 and 180")
        if not (-90 <= self.lon <= 90):
            raise ValueError("Longitude must be between -90 and 90")
        if self.setup_time < timedelta(0):
            raise ValueError("Setup time cannot be negative")


@dataclass
class HubShifts:
    """Hub shifts domain entity"""

    # Required fields FIRST
    terminal_id: UUID
    start_time: time
    finish_time: time

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Vehicle:
    """Vehicle domain entity"""

    # Required fields FIRST
    courier_id: UUID
    vehicle_type: VehicleType

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)

    # Physical capacity
    weight_capacity: float | None = None
    volume_capacity: float | None = None

    # Costs
    loading_cost: Decimal = field(default_factory=lambda: Decimal("0.00"))
    travel_cost_per_km: Decimal = field(default_factory=lambda: Decimal("0.00"))
    travel_cost_per_hour: Decimal = field(default_factory=lambda: Decimal("0.00"))

    # Time & speed
    loading_time: int | None = 0  # seconds
    average_speed: int = 0  # km/h
    max_duration: int | None = None
    max_distance: int | None = None

    # Fuel
    fuel_consumption_per_100_km: int = 0  # liters
    fuel_type: FuelType = FuelType.PETROL

    # Constraints
    max_tasks: int | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Validate vehicle properties"""
        if (
            self.weight_capacity is None
            or self.average_speed is None
            or self.loading_cost is None
        ):
            pass
        else:
            if self.weight_capacity < 0:
                raise ValueError("Weight capacity cannot be negative")
            if self.average_speed < 0:
                raise ValueError("Average speed cannot be negative")
            if self.loading_cost < 0:
                raise ValueError("Loading cost cannot be negative")


@dataclass
class RefreshToken:
    """Refresh token domain entity for JWT token management"""

    # Required fields FIRST
    user_id: UUID
    token: str
    expires_at: datetime

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)
    is_revoked: bool = False
    revoked_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        from datetime import timezone

        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_revoked and not self.is_expired()

    def revoke(self) -> None:
        """Revoke the refresh token"""
        from datetime import timezone

        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<RefreshToken(user_id={self.user_id}, is_revoked={self.is_revoked}, is_expired={self.is_expired()})>"


@dataclass
class Coordinates:
    """Geographic coordinates"""

    lat: float
    lon: float

    def __post_init__(self):
        """Validate latitude and longitude"""
        if not (-90 <= self.lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= self.lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")

    def __repr__(self) -> str:
        return f"Coordinates(lat={self.lat}, lon={self.lon})"


@dataclass
class Address:
    """Physical address"""

    street: str
    city: str
    state: str
    country: str
    postal_code: str | None = None

    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        return ", ".join(str(p) for p in parts if p)

    def __repr__(self) -> str:
        return f"Address({self.full_address})"


@dataclass
class TimeWindow:
    """Delivery time window"""

    earliest: time
    latest: time

    def __post_init__(self):
        """Validate time window"""
        if self.earliest >= self.latest:
            raise ValueError("Earliest time must be before latest time")

    @property
    def duration(self) -> int:
        """Get duration in minutes"""
        return int((self.latest - self.earliest).total_seconds() / 60)

    def __repr__(self) -> str:
        return f"TimeWindow({self.earliest} -> {self.latest})"


@dataclass
class Recipient:
    user_id: UUID
    id: UUID = field(default_factory=uuid4)

    # Location
    location: Coordinates | None = None
    address: Address | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Order:
    """Order domain entity"""

    # Identifiers
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    recipient_id: UUID

    # Order details
    name: str
    barcode: str
    id: UUID = field(default_factory=uuid4)
    status: OrderStatusTypes = OrderStatusTypes.REGISTERED
    geo_location_provided: bool = False

    # Time window
    time_window: TimeWindow | None = None

    # Capacity
    weight_occupation: float = 0.0
    volume_occupation: float = 0.0

    # Delivery tracking
    is_return: bool = False
    original_delivery_date: date | None = None
    expected_delivery_date: date | None = None
    actual_delivery_date: date | None = None

    moved_as: UUID | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Validate order properties"""
        if self.weight_occupation < 0:
            raise ValueError("Weight occupation cannot be negative")
        if self.volume_occupation < 0:
            raise ValueError("Volume occupation cannot be negative")

    def mark_delivered(self, actual_date: datetime) -> None:
        """Mark order as delivered"""
        if self.status == OrderStatusTypes.DELIVERED:
            raise ValueError("Order already delivered")
        if actual_date < self.expected_delivery_date:
            raise ValueError("Actual delivery date cannot be before expected date")

        self.status = OrderStatusTypes.DELIVERED
        self.actual_delivery_date = actual_date

    def can_be_assigned(self) -> bool:
        """Check if order can be assigned"""
        return self.status == OrderStatusTypes.REGISTERED

    def cancel(self) -> None:
        """Cancel order"""
        self.status = OrderStatusTypes.CANCELLED

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, barcode={self.barcode}, status={self.status.value})>"
        )


@dataclass
class Route:
    """Route domain entity representing a courier's delivery route"""

    # Required fields FIRST
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    vehicle_id: UUID
    route_name: str
    start_time: time
    finish_time: time
    status: RouteStatesType
    color: str
    must_return: bool
    number_of_missions: int

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)

    # Actual execution times
    actual_start_time: time | None = None
    actual_finish_time: time | None = None

    # Route metrics
    cost: Decimal | None = None
    duration: int | None = None  # minutes
    distance: int | None = None  # meters or km

    # Current state
    current_mission_id: UUID | None = None

    # Mission aggregates
    total_waiting_time: int | None = None  # minutes
    total_actual_waiting_time: int | None = None  # minutes
    total_number_of_orders: int | None = None
    total_number_of_stops: int | None = None

    # Hub interaction
    loading_time_start: datetime | None = None
    arrived_at_hub_time: datetime | None = None

    # Route metadata
    lock: bool | None = None
    created_type: RouteCreatedType | None = None
    modification_time: time | None = None
    courier_score: int | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Validate route properties"""
        if self.start_time >= self.finish_time:
            raise ValueError("Start time must be before finish time")
        if self.actual_start_time and self.actual_finish_time:
            if self.actual_start_time >= self.actual_finish_time:
                raise ValueError("Actual start time must be before actual finish time")
        if self.number_of_missions < 0:
            raise ValueError("Number of missions cannot be negative")
        if self.duration is not None and self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if self.distance is not None and self.distance < 0:
            raise ValueError("Distance cannot be negative")

    @property
    def is_completed(self) -> bool:
        """Check if route is completed"""
        return self.status == RouteStatesType.FINISHED

    @property
    def is_active(self) -> bool:
        """Check if route is currently active"""
        return self.status in [RouteStatesType.LOADING, RouteStatesType.ONGOING]

    def __repr__(self) -> str:
        return (
            f"<Route(id={self.id}, name={self.route_name}, status={self.status.value})>"
        )


@dataclass
class Mission:
    """Mission domain entity representing a single delivery task within a route"""

    # Required fields FIRST
    route_id: UUID
    order_id: UUID
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    is_return: bool

    # Optional/default fields AFTER
    id: UUID = field(default_factory=uuid4)

    # Location information
    location: Coordinates | None = None
    address: Address | None = None

    # Planned times and distances
    arrival_time: time | None = None
    cumulative_duration: int | None = None  # minutes
    cumulative_distance: int | None = None  # meters or km
    service_time: int | None = None  # minutes

    # Actual execution times and distances
    actual_arrival_time: time | None = None
    actual_cumulative_duration: int | None = None  # minutes
    actual_cumulative_distance: int | None = None  # meters or km
    actual_service_time: int | None = None  # minutes
    actual_mission_start_time: time | None = None
    actual_mission_finish_time: time | None = None

    # Mission status
    status: MissionStatusType | None = None
    postponed: MissionPostponedType | None = None

    # Route positioning
    position_in_route: int | None = None

    # Waiting times
    waiting_time: int | None = None  # minutes (planned)
    actual_waiting_time: int | None = None  # minutes (actual)

    # Parcel scanning
    loading_scan_parcel_time: datetime | None = None
    delivery_scan_parcel_time: datetime | None = None
    delivery_scan_parcel_barcode: str | None = None

    # Additional information
    courier_comment: str | None = None

    # Audit
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        """Validate mission properties"""
        if self.cumulative_duration is not None and self.cumulative_duration < 0:
            raise ValueError("Cumulative duration cannot be negative")
        if self.cumulative_distance is not None and self.cumulative_distance < 0:
            raise ValueError("Cumulative distance cannot be negative")
        if self.service_time is not None and self.service_time < 0:
            raise ValueError("Service time cannot be negative")
        if (
            self.actual_cumulative_duration is not None
            and self.actual_cumulative_duration < 0
        ):
            raise ValueError("Actual cumulative duration cannot be negative")
        if (
            self.actual_cumulative_distance is not None
            and self.actual_cumulative_distance < 0
        ):
            raise ValueError("Actual cumulative distance cannot be negative")
        if self.actual_service_time is not None and self.actual_service_time < 0:
            raise ValueError("Actual service time cannot be negative")
        if self.position_in_route is not None and self.position_in_route < 0:
            raise ValueError("Position in route cannot be negative")
        if self.waiting_time is not None and self.waiting_time < 0:
            raise ValueError("Waiting time cannot be negative")
        if self.actual_waiting_time is not None and self.actual_waiting_time < 0:
            raise ValueError("Actual waiting time cannot be negative")

    @property
    def is_delivered(self) -> bool:
        """Check if mission has been delivered"""
        return self.status in [
            MissionStatusType.DELIVERED,
            MissionStatusType.DELIVERED_WITH_DELAY,
        ]

    @property
    def is_failed(self) -> bool:
        """Check if mission delivery failed"""
        return self.status in [
            MissionStatusType.UNDELIVERED_UNREACHABLE_ADDRESS,
            MissionStatusType.UNDELIVERED_UNREACHABLE_CUSTOMER,
            MissionStatusType.UNDELIVERED_UNREACHABLE_DISPATCH,
            MissionStatusType.CANCELLED,
        ]

    @property
    def has_delay(self) -> bool:
        """Check if mission was delivered with delay"""
        return self.status == MissionStatusType.DELIVERED_WITH_DELAY

    def __repr__(self) -> str:
        return f"<Mission(id={self.id}, order_id={self.order_id}, status={self.status.value if self.status else 'pending'})>"


@dataclass
class CourierCurrentState:

    courier_id: UUID
    state: CourierStatesType
    id: UUID = field(default_factory=uuid4)
    delivered_order_ids: List[UUID] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# --------------------------------------------------------
# --------------- Billing Entities -----------------------
# --------------------------------------------------------


@dataclass
class BillingCustomer:
    """Billing customer domain entity representing a customer in the billing system"""

    user_id: UUID
    stripe_customer_id: str  # cus_xxxxx

    id: UUID = field(default_factory=uuid4)
    currency: Currency = Currency.EUR
    billing_email: str | None = None
    billing_name: str | None = None
    tax_id: str | None = None  # VAT number for EU
    country_code: str | None = None  # ISO2: SE, US, ...

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Plan:
    """Plan domain entity representing a plan in the billing system"""

    name: str
    tier: PlanTier

    id: UUID = field(default_factory=uuid4)
    stripe_product_id: str | None = None  # prod_xxxxx
    monthly_delivery_limit: int = 300
    is_active: bool = True

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PlanPrice:
    """Price of a plan in a specific currency — mapped with Stripe Price"""

    plan_id: UUID
    currency: Currency
    amount: Decimal  # Amount in the smallest unit (öre, cent, ...)
    stripe_price_id: str  # price_xxxxx

    id: UUID = field(default_factory=uuid4)
    billing_interval: str = "month"  # month | year
    is_active: bool = True

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Subscription:
    """Subscription domain entity representing a subscription in the billing system"""

    billing_customer_id: UUID
    plan_id: UUID
    plan_price_id: UUID
    stripe_subscription_id: str  # sub_xxxxx
    status: SubscriptionStatus

    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class UsageRecord:
    """Usage record domain entity representing a usage record in the billing system"""

    billing_customer_id: UUID
    subscription_id: UUID

    id: UUID = field(default_factory=uuid4)
    period_start: datetime | None = None
    period_end: datetime | None = None
    delivery_count: int = 0
    limit: int = 300
    overage_count: int = 0  # delivery_count - limit if > 0

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_over_limit(self) -> bool:
        return self.delivery_count > self.limit

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.delivery_count)


@dataclass
class Payment:
    """Payment domain entity representing a payment in the billing system"""

    billing_customer_id: UUID
    subscription_id: UUID | None
    stripe_payment_intent_id: str  # pi_xxxxx

    id: UUID = field(default_factory=uuid4)
    amount: Decimal = Decimal("0.00")
    currency: Currency = Currency.EUR
    status: PaymentStatus = PaymentStatus.PENDING

    paid_at: datetime | None = None
    failure_reason: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Invoice:
    """Invoice domain entity representing an invoice in the billing system"""

    billing_customer_id: UUID
    subscription_id: UUID | None
    stripe_invoice_id: str  # in_xxxxx

    id: UUID = field(default_factory=uuid4)
    amount_due: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")
    currency: Currency = Currency.EUR
    status: InvoiceStatus = InvoiceStatus.DRAFT
    invoice_pdf_url: str | None = None

    due_date: datetime | None = None
    paid_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
