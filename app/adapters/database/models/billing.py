# adapters/database/models/billing.py
"""Billing ORM models."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
import uuid

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum,
    Integer,
    Boolean,
    DECIMAL,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import (
    SubscriptionStatus,
    PlanTier,
    InvoiceStatus,
    PaymentStatus,
    Currency,
)
from app.adapters.database.models.base import Base, TimeStampMixin


class BillingCustomerORM(Base, TimeStampMixin):
    """Billing customer ORM - links User to Stripe Customer"""

    __tablename__ = "billing_customers"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency), default=Currency.EUR, nullable=False
    )
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relationships
    user: Mapped["UserORM"] = relationship("UserORM", backref="billing_customer")
    subscriptions: Mapped[list["SubscriptionORM"]] = relationship(
        "SubscriptionORM",
        back_populates="billing_customer",
        cascade="all, delete-orphan",
    )
    usage_records: Mapped[list["UsageRecordORM"]] = relationship(
        "UsageRecordORM",
        back_populates="billing_customer",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["PaymentORM"]] = relationship(
        "PaymentORM",
        back_populates="billing_customer",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[list["InvoiceORM"]] = relationship(
        "InvoiceORM",
        back_populates="billing_customer",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_billing_customer_user_id", "user_id"),
        Index("idx_billing_customer_stripe_id", "stripe_customer_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingCustomerORM(user_id={self.user_id}, stripe={self.stripe_customer_id})>"


class PlanORM(Base, TimeStampMixin):
    """Subscription plan ORM"""

    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), nullable=False, unique=True)
    stripe_product_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    monthly_delivery_limit: Mapped[int] = mapped_column(
        Integer, default=300, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    prices: Mapped[list["PlanPriceORM"]] = relationship(
        "PlanPriceORM",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["SubscriptionORM"]] = relationship(
        "SubscriptionORM",
        back_populates="plan",
    )

    __table_args__ = (
        Index("idx_plan_tier", "tier"),
        Index("idx_plan_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<PlanORM(name={self.name}, tier={self.tier.value})>"


class PlanPriceORM(Base, TimeStampMixin):
    """Plan price per currency ORM - maps to Stripe Price"""

    __tablename__ = "plan_prices"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    billing_interval: Mapped[str] = mapped_column(
        String(20), default="month", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    plan: Mapped["PlanORM"] = relationship("PlanORM", back_populates="prices")

    __table_args__ = (
        Index("idx_plan_price_plan_id", "plan_id"),
        Index("idx_plan_price_currency", "currency"),
        Index("idx_plan_price_plan_currency", "plan_id", "currency"),
    )

    def __repr__(self) -> str:
        return f"<PlanPriceORM(plan_id={self.plan_id}, {self.amount} {self.currency.value})>"


class SubscriptionORM(Base, TimeStampMixin):
    """Active subscription ORM - maps to Stripe Subscription"""

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("billing_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    plan_price_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plan_prices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), nullable=False
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    billing_customer: Mapped["BillingCustomerORM"] = relationship(
        "BillingCustomerORM", back_populates="subscriptions"
    )
    plan: Mapped["PlanORM"] = relationship("PlanORM", back_populates="subscriptions")
    plan_price: Mapped["PlanPriceORM"] = relationship("PlanPriceORM")
    usage_records: Mapped[list["UsageRecordORM"]] = relationship(
        "UsageRecordORM",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    user: Mapped["UserORM"] = relationship("UserORM", backref="subscriptions")

    __table_args__ = (
        Index("idx_subscription_customer_id", "billing_customer_id"),
        Index("idx_subscription_plan_id", "plan_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_stripe_id", "stripe_subscription_id"),
    )

    def __repr__(self) -> str:
        return f"<SubscriptionORM(id={self.id}, status={self.status.value})>"


class UsageRecordORM(Base, TimeStampMixin):
    """Delivery usage tracking per billing period"""

    __tablename__ = "usage_records"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("billing_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_limit: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    overage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    billing_customer: Mapped["BillingCustomerORM"] = relationship(
        "BillingCustomerORM", back_populates="usage_records"
    )
    subscription: Mapped["SubscriptionORM"] = relationship(
        "SubscriptionORM", back_populates="usage_records"
    )

    __table_args__ = (
        Index("idx_usage_customer_id", "billing_customer_id"),
        Index("idx_usage_subscription_id", "subscription_id"),
        Index("idx_usage_period", "period_start", "period_end"),
    )

    def __repr__(self) -> str:
        return (
            f"<UsageRecordORM(customer={self.billing_customer_id}, "
            f"count={self.delivery_count}/{self.delivery_limit})>"
        )


class PaymentORM(Base, TimeStampMixin):
    """Payment record ORM - maps to Stripe PaymentIntent"""

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("billing_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    stripe_payment_intent_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency), default=Currency.EUR, nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    billing_customer: Mapped["BillingCustomerORM"] = relationship(
        "BillingCustomerORM", back_populates="payments"
    )

    __table_args__ = (
        Index("idx_payment_customer_id", "billing_customer_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_stripe_id", "stripe_payment_intent_id"),
    )

    def __repr__(self) -> str:
        return f"<PaymentORM(amount={self.amount} {self.currency.value}, status={self.status.value})>"


class InvoiceORM(Base, TimeStampMixin):
    """Invoice ORM - synced with Stripe Invoice"""

    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_customer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("billing_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    stripe_invoice_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    amount_due: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency), default=Currency.EUR, nullable=False
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False
    )
    invoice_pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    billing_customer: Mapped["BillingCustomerORM"] = relationship(
        "BillingCustomerORM", back_populates="invoices"
    )

    __table_args__ = (
        Index("idx_invoice_customer_id", "billing_customer_id"),
        Index("idx_invoice_status", "status"),
        Index("idx_invoice_stripe_id", "stripe_invoice_id"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceORM(amount_due={self.amount_due} {self.currency.value}, status={self.status.value})>"
