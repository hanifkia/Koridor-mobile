"""
Billing request/response schemas
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from app.core.entities import (
    SubscriptionStatus,
    PlanTier,
    InvoiceStatus,
    PaymentStatus,
    Currency,
)


# ============================================================================
# PLAN SCHEMAS
# ============================================================================


class PlanPriceSchema(BaseModel):
    """Plan price response"""

    id: UUID
    plan_id: UUID
    currency: Currency
    amount: Decimal
    stripe_price_id: str
    billing_interval: str
    is_active: bool

    class Config:
        from_attributes = True


class PlanResponseSchema(BaseModel):
    """Plan response"""

    id: UUID
    name: str
    tier: PlanTier
    monthly_delivery_limit: int
    is_active: bool
    prices: Optional[List[PlanPriceSchema]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlanListResponseSchema(BaseModel):
    """Plan list for display"""

    id: UUID
    name: str
    tier: PlanTier
    monthly_delivery_limit: int
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# BILLING CUSTOMER SCHEMAS
# ============================================================================


class BillingCustomerResponseSchema(BaseModel):
    """Billing customer response"""

    id: UUID
    user_id: UUID
    stripe_customer_id: str
    currency: Currency
    billing_email: Optional[str] = None
    billing_name: Optional[str] = None
    tax_id: Optional[str] = None
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateBillingInfoSchema(BaseModel):
    """Update billing information"""

    billing_email: Optional[str] = Field(None, max_length=255)
    billing_name: Optional[str] = Field(None, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=100)
    country_code: Optional[str] = Field(None, max_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "billing_email": "billing@company.com",
                "billing_name": "Logistics Company AB",
                "tax_id": "SE123456789001",
                "country_code": "SE",
            }
        }


# ============================================================================
# SUBSCRIPTION SCHEMAS
# ============================================================================


class SubscriptionResponseSchema(BaseModel):
    """Subscription response"""

    id: UUID
    billing_customer_id: UUID
    plan_id: UUID
    plan_price_id: UUID
    stripe_subscription_id: str
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    """Create subscription request"""

    plan_tier: PlanTier = Field(..., description="Plan tier to subscribe to")
    currency: Currency = Field(
        default=Currency.EUR, description="Preferred billing currency"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_tier": "STARTER",
                "currency": "EUR",
            }
        }


class ChangeSubscriptionRequest(BaseModel):
    """Change subscription plan"""

    new_plan_tier: PlanTier = Field(..., description="New plan tier")

    class Config:
        json_schema_extra = {
            "example": {
                "new_plan_tier": "PROFESSIONAL",
            }
        }


class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription request"""

    cancel_immediately: bool = Field(
        default=False,
        description="If true, cancel immediately. Otherwise cancel at period end.",
    )


# ============================================================================
# USAGE SCHEMAS
# ============================================================================


class UsageResponseSchema(BaseModel):
    """Usage record response"""

    id: UUID
    billing_customer_id: UUID
    subscription_id: UUID
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    delivery_count: int
    delivery_limit: int
    overage_count: int
    usage_percentage: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsageSummarySchema(BaseModel):
    """Usage summary for dashboard"""

    delivery_count: int = Field(..., description="Deliveries used this period")
    delivery_limit: int = Field(..., description="Maximum deliveries allowed")
    overage_count: int = Field(default=0, description="Deliveries over limit")
    usage_percentage: float = Field(..., description="Usage percentage (0-100)")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    remaining_deliveries: int = Field(..., description="Remaining deliveries")

    class Config:
        json_schema_extra = {
            "example": {
                "delivery_count": 150,
                "delivery_limit": 300,
                "overage_count": 0,
                "usage_percentage": 50.0,
                "remaining_deliveries": 150,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
            }
        }


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================


class PaymentResponseSchema(BaseModel):
    """Payment response"""

    id: UUID
    billing_customer_id: UUID
    subscription_id: Optional[UUID] = None
    stripe_payment_intent_id: str
    amount: Decimal
    currency: Currency
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================


class InvoiceResponseSchema(BaseModel):
    """Invoice response"""

    id: UUID
    billing_customer_id: UUID
    subscription_id: Optional[UUID] = None
    stripe_invoice_id: str
    amount_due: Decimal
    amount_paid: Decimal
    currency: Currency
    status: InvoiceStatus
    invoice_pdf_url: Optional[str] = None
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# CHECKOUT / PORTAL SCHEMAS
# ============================================================================


class CreateCheckoutSessionRequest(BaseModel):
    """Create Stripe Checkout Session"""

    plan_tier: PlanTier = Field(..., description="Plan tier to subscribe to")
    currency: Currency = Field(default=Currency.EUR, description="Billing currency")
    success_url: str = Field(..., description="Redirect URL on success")
    cancel_url: str = Field(..., description="Redirect URL on cancel")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_tier": "STARTER",
                "currency": "EUR",
                "success_url": "https://app.example.com/billing/success",
                "cancel_url": "https://app.example.com/billing/cancel",
            }
        }


class CheckoutSessionResponseSchema(BaseModel):
    """Checkout session response"""

    checkout_url: str = Field(..., description="Stripe Checkout Session URL")
    session_id: str = Field(..., description="Stripe Checkout Session ID")


class CreatePortalSessionRequest(BaseModel):
    """Create Stripe Customer Portal Session"""

    return_url: str = Field(..., description="URL to redirect back to after portal")

    class Config:
        json_schema_extra = {
            "example": {
                "return_url": "https://app.example.com/billing",
            }
        }


class PortalSessionResponseSchema(BaseModel):
    """Portal session response"""

    portal_url: str = Field(..., description="Stripe Customer Portal URL")


# ============================================================================
# BILLING OVERVIEW SCHEMA
# ============================================================================


class BillingOverviewSchema(BaseModel):
    """Complete billing overview for dashboard"""

    customer: Optional[BillingCustomerResponseSchema] = None
    subscription: Optional[SubscriptionResponseSchema] = None
    current_plan: Optional[PlanResponseSchema] = None
    usage: Optional[UsageSummarySchema] = None
    recent_invoices: List[InvoiceResponseSchema] = []
    recent_payments: List[PaymentResponseSchema] = []
