"""
Billing service implementation - orchestrates all billing operations
"""

import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from app.core.entities import (
    BillingCustomer,
    Plan,
    PlanPrice,
    Subscription,
    UsageRecord,
    Payment,
    Invoice,
    SubscriptionStatus,
    PlanTier,
    InvoiceStatus,
    PaymentStatus,
    Currency,
)
from app.core.interfaces.repositories.billing_customer_interface import (
    IBillingCustomerRepository,
)
from app.core.interfaces.repositories.subscription_interface import (
    ISubscriptionRepository,
)
from app.core.interfaces.repositories.plan_interface import IPlanRepository
from app.core.interfaces.repositories.plan_price_interface import IPlanPriceRepository
from app.core.interfaces.repositories.usage_record_interface import (
    IUsageRecordRepository,
)
from app.core.interfaces.repositories.payment_interface import IPaymentRepository
from app.core.interfaces.repositories.invoice_interface import IInvoiceRepository
from app.core.interfaces import IUserRepository, ICourierRepository
from app.adapters.clients.stripe.stripe_client import StripeAsyncClient

logger = logging.getLogger(__name__)


class BillingService:
    """Service for managing billing, subscriptions, and payments"""

    def __init__(
        self,
        stripe_client: StripeAsyncClient,
        billing_customer_repo: IBillingCustomerRepository,
        subscription_repo: ISubscriptionRepository,
        plan_repo: IPlanRepository,
        plan_price_repo: IPlanPriceRepository,
        usage_repo: IUsageRecordRepository,
        payment_repo: IPaymentRepository,
        invoice_repo: IInvoiceRepository,
        user_repo: IUserRepository,
        courier_repo: ICourierRepository,
    ):
        self.stripe_client = stripe_client
        self.billing_customer_repo = billing_customer_repo
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.plan_price_repo = plan_price_repo
        self.usage_repo = usage_repo
        self.payment_repo = payment_repo
        self.invoice_repo = invoice_repo
        self.user_repo = user_repo
        self.courier_repo = courier_repo
        logger.info("🔄 BillingService initialized")

    # ========================================================================
    # PLANS
    # ========================================================================

    async def get_active_plans(self) -> List[Plan]:
        """Get all active subscription plans"""
        logger.info("🔄 Fetching active plans")
        plans = await self.plan_repo.get_active_plans()
        logger.info(f"✅ Retrieved {len(plans)} active plans")
        return plans

    async def get_plan_by_tier(self, plan_tier: str) -> Optional[Plan]:
        """Get plan by tier name"""
        logger.info(f"🔄 Fetching plan by tier: {plan_tier}")
        try:
            # tier = PlanTier(plan_tier.upper())
            tier = PlanTier[plan_tier.upper()]
        except ValueError:
            logger.error(f"❌ Invalid plan tier: {plan_tier}")
            raise ValueError(f"Invalid plan tier: {plan_tier}")

        plan = await self.plan_repo.get_by_tier(tier)
        price = await self.plan_price_repo.get_by_plan_id(plan.id) if plan else None
        if plan:
            logger.info(f"✅ Plan found: {plan.name}")
        else:
            logger.warning(f"⚠️  Plan not found for tier: {plan_tier}")

        return plan, price

    async def create_free_subscription_for_new_user(
        self, user_id: UUID
    ) -> Subscription:
        """Create a free trial subscription for a new user"""
        logger.info(f"🔄 Creating free subscription for new user: {user_id}")

        # Get or create billing customer
        customer = await self.get_or_create_billing_customer(user_id)

        # Get free plan and price
        free_plan = await self.plan_repo.get_by_tier(PlanTier.FREE)
        if not free_plan:
            logger.error("❌ Free plan not found")
            raise ValueError("Free plan not found")

        free_price = await self.plan_price_repo.get_by_plan_and_currency(
            free_plan.id, customer.currency
        )
        if not free_price:
            logger.error(
                f"❌ Free price not found for currency: {customer.currency.value}"
            )
            raise ValueError(
                f"Free price not found for currency: {customer.currency.value}"
            )

        # Create local subscription record (no Stripe subscription for free tier)
        subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            billing_customer_id=customer.id,
            plan_id=free_plan.id,
            plan_price_id=free_price.id,
            stripe_subscription_id=None,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=None,  # No end date for free tier
            cancel_at_period_end=False,
        )

        created = await self.subscription_repo.create(subscription)

        usage_record = UsageRecord(
            id=uuid4(),
            billing_customer_id=customer.id,
            subscription_id=created.id,
            period_start=datetime.now(timezone.utc),
            period_end=None,  # No end date for free tier
            delivery_count=0,
            limit=free_plan.monthly_delivery_limit,
            overage_count=0,
        )
        await self.usage_repo.create(usage_record)
        logger.info(f"✅ Free subscription created for user: {user_id}")
        return created

    # ========================================================================
    # BILLING CUSTOMER
    # ========================================================================

    async def get_or_create_billing_customer(self, user_id: UUID) -> BillingCustomer:
        """
        Get existing billing customer or create new one with Stripe

        **Flow:**
        1. Check if billing customer exists locally
        2. If not, fetch user info
        3. Create Stripe Customer
        4. Create local billing customer record
        """
        logger.info(f"🔄 Getting/creating billing customer for user: {user_id}")

        # Check existing
        existing = await self.billing_customer_repo.get_by_user_id(user_id)
        if existing:
            logger.info(f"✅ Billing customer found: {existing.id}")
            return existing

        # Get user info
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        # Create Stripe customer
        try:
            stripe_customer = await self.stripe_client.create_customer(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user_id)},
            )
            logger.info(f"✅ Stripe customer created: {stripe_customer['id']}")
        except Exception as e:
            logger.error(
                f"❌ Failed to create Stripe customer: {str(e)}", exc_info=True
            )
            raise

        # Create local record
        billing_customer = BillingCustomer(
            id=uuid4(),
            user_id=user_id,
            stripe_customer_id=stripe_customer["id"],
            currency=Currency.EUR,
            billing_email=user.email,
            billing_name=user.full_name,
        )

        created = await self.billing_customer_repo.create(billing_customer)
        logger.info(f"✅ Billing customer created: {created.id}")
        return created

    async def update_billing_info(
        self,
        user_id: UUID,
        billing_email: Optional[str] = None,
        billing_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> BillingCustomer:
        """Update billing information"""
        logger.info(f"🔄 Updating billing info for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            logger.error(f"❌ Billing customer not found for user: {user_id}")
            raise ValueError(f"Billing customer not found for user: {user_id}")

        # Update fields
        if billing_email is not None:
            customer.billing_email = billing_email
        if billing_name is not None:
            customer.billing_name = billing_name
        if tax_id is not None:
            customer.tax_id = tax_id
        if country_code is not None:
            customer.country_code = country_code

        # Update Stripe customer too
        try:
            await self.stripe_client.update_customer(
                customer_id=customer.stripe_customer_id,
                email=customer.billing_email,
                name=customer.billing_name,
            )
            logger.info(f"✅ Stripe customer updated: {customer.stripe_customer_id}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to update Stripe customer: {str(e)}")

        updated = await self.billing_customer_repo.update(customer.id, customer)
        logger.info(f"✅ Billing info updated for user: {user_id}")
        return updated

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    async def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get active subscription for user"""
        logger.info(f"🔄 Getting active subscription for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            logger.warning(f"⚠️  No billing customer for user: {user_id}")
            return None

        subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if subscription:
            logger.info(f"✅ Active subscription found: {subscription.id}")
        else:
            logger.info(f"ℹ️  No active subscription for user: {user_id}")
        return subscription

    async def create_checkout_session(
        self,
        user_id: UUID,
        plan_tier: PlanTier,
        currency: Currency,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, str]:
        """
        Create Stripe Checkout Session for new subscription

        **Flow:**
        1. Get/create billing customer
        2. Get plan and price
        3. Check no active subscription exists
        4. Create Stripe Checkout Session
        5. Return checkout URL
        """
        logger.info(
            f"🔄 Creating checkout session for user: {user_id}, tier: {plan_tier.value}"
        )

        # Get/create billing customer
        customer = await self.get_or_create_billing_customer(user_id)

        # Get plan
        plan = await self.plan_repo.get_by_tier(plan_tier)
        if not plan:
            logger.error(f"❌ Plan not found for tier: {plan_tier.value}")
            raise ValueError(f"Plan not found for tier: {plan_tier.value}")

        # Get price
        price = await self.plan_price_repo.get_by_plan_and_currency(plan.id, currency)
        if not price:
            logger.error(f"❌ Price not found for plan {plan.name} in {currency.value}")
            raise ValueError(
                f"Price not found for plan {plan.name} in {currency.value}"
            )

        # Check existing subscription
        existing_sub = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if existing_sub and existing_sub.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        ]:
            logger.error(f"❌ User already has active subscription")
            raise ValueError(
                "User already has an active subscription. Use change plan instead."
            )

        # Create Stripe Checkout Session
        try:
            session = await self.stripe_client.create_checkout_session(
                customer_id=customer.stripe_customer_id,
                price_id=price.stripe_price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user_id),
                    "plan_id": str(plan.id),
                    "plan_price_id": str(price.id),
                },
            )
            logger.info(f"✅ Checkout session created: {session['id']}")
            return {
                "checkout_url": session["url"],
                "session_id": session["id"],
            }
        except Exception as e:
            logger.error(
                f"❌ Failed to create checkout session: {str(e)}", exc_info=True
            )
            raise

    async def change_plan(self, user_id: UUID, new_plan_tier: PlanTier) -> Subscription:
        """
        Change subscription plan (upgrade/downgrade)

        **Flow:**
        1. Get billing customer
        2. Get active subscription
        3. Get new plan and price
        4. Update Stripe subscription
        5. Update local subscription
        """
        logger.info(f"🔄 Changing plan for user: {user_id} to {new_plan_tier.value}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        # Get current subscription
        subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if not subscription:
            raise ValueError("No active subscription found")

        if subscription.status not in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        ]:
            raise ValueError(
                f"Cannot change plan with subscription status: {subscription.status.value}"
            )

        # Get new plan and price
        new_plan = await self.plan_repo.get_by_tier(new_plan_tier)
        if not new_plan:
            raise ValueError(f"Plan not found for tier: {new_plan_tier.value}")

        new_price = await self.plan_price_repo.get_by_plan_and_currency(
            new_plan.id, customer.currency
        )
        if not new_price:
            raise ValueError(
                f"Price not found for plan {new_plan.name} in {customer.currency.value}"
            )

        # Update Stripe subscription
        try:
            updated_stripe_sub = await self.stripe_client.update_subscription(
                subscription_id=subscription.stripe_subscription_id,
                new_price_id=new_price.stripe_price_id,
            )
            logger.info(
                f"✅ Stripe subscription updated: {subscription.stripe_subscription_id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to update Stripe subscription: {str(e)}",
                exc_info=True,
            )
            raise

        # Update local subscription
        subscription.plan_id = new_plan.id
        subscription.plan_price_id = new_price.id

        updated = await self.subscription_repo.update(subscription.id, subscription)
        logger.info(f"✅ Plan changed to {new_plan_tier.value} for user: {user_id}")

        # Update usage limit for current period
        usage = await self.usage_repo.get_current_period(customer.id)
        if usage:
            usage.limit = new_plan.monthly_delivery_limit
            await self.usage_repo.update(usage.id, usage)
            logger.info(f"✅ Usage limit updated to {new_plan.monthly_delivery_limit}")

        return updated

    async def cancel_subscription(
        self, user_id: UUID, cancel_immediately: bool = False
    ) -> Subscription:
        """Cancel subscription"""
        logger.info(
            f"🔄 Cancelling subscription for user: {user_id} "
            f"(immediately={cancel_immediately})"
        )

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if not subscription:
            raise ValueError("No active subscription found")

        # Cancel in Stripe
        try:
            if cancel_immediately:
                await self.stripe_client.cancel_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    immediately=True,
                )
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.now(timezone.utc)
            else:
                await self.stripe_client.cancel_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    immediately=False,
                )
                subscription.cancel_at_period_end = True

            logger.info(
                f"✅ Stripe subscription cancelled: {subscription.stripe_subscription_id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to cancel Stripe subscription: {str(e)}",
                exc_info=True,
            )
            raise

        updated = await self.subscription_repo.update(subscription.id, subscription)
        logger.info(f"✅ Subscription cancelled for user: {user_id}")
        return updated

    async def reactivate_subscription(self, user_id: UUID) -> Subscription:
        """Reactivate subscription that was set to cancel at period end"""
        logger.info(f"🔄 Reactivating subscription for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if not subscription:
            raise ValueError("No subscription found")

        if not subscription.cancel_at_period_end:
            raise ValueError("Subscription is not set to cancel at period end")

        # Reactivate in Stripe
        try:
            await self.stripe_client.reactivate_subscription(
                subscription_id=subscription.stripe_subscription_id,
            )
            subscription.cancel_at_period_end = False
            logger.info(
                f"✅ Stripe subscription reactivated: {subscription.stripe_subscription_id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to reactivate Stripe subscription: {str(e)}",
                exc_info=True,
            )
            raise

        updated = await self.subscription_repo.update(subscription.id, subscription)
        logger.info(f"✅ Subscription reactivated for user: {user_id}")
        return updated

    # ========================================================================
    # USAGE
    # ========================================================================

    async def get_current_usage(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current billing period usage summary"""
        logger.info(f"🔄 Getting current usage for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        usage = await self.usage_repo.get_current_period(customer.id)
        if not usage:
            logger.info(f"ℹ️  No active usage record for user: {user_id}")
            return None

        remaining = max(0, usage.limit - usage.delivery_count)
        percentage = (
            (usage.delivery_count / usage.limit * 100) if usage.limit > 0 else 0
        )

        return {
            "delivery_count": usage.delivery_count,
            "delivery_limit": usage.limit,
            "overage_count": usage.overage_count,
            "usage_percentage": round(percentage, 1),
            "period_start": usage.period_start,
            "period_end": usage.period_end,
            "remaining_deliveries": remaining,
        }

    async def record_delivery(self, user_id: UUID) -> Optional[UsageRecord]:
        """
        Record a delivery for usage tracking.
        Called when a delivery is completed.
        """
        logger.info(f"🔄 Recording delivery for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            logger.warning(f"⚠️  No billing customer for user: {user_id}")
            return None

        usage = await self.usage_repo.increment_delivery_count(customer.id)
        if usage:
            logger.info(
                f"✅ Delivery recorded: {usage.delivery_count}/{usage.limit} "
                f"for user: {user_id}"
            )
        return usage

    async def check_delivery_limit(self, user_id: UUID) -> Dict[str, Any]:
        """
        Check if user has reached delivery limit.
        Returns whether delivery is allowed and remaining count.
        """
        logger.info(f"🔄 Checking delivery limit for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            # No billing customer = free tier with default limit
            return {
                "allowed": True,
                "remaining": 300,
                "at_limit": False,
                "over_limit": False,
            }

        usage = await self.usage_repo.get_current_period(customer.id)
        if not usage:
            return {
                "allowed": True,
                "remaining": 300,
                "at_limit": False,
                "over_limit": False,
            }

        remaining = max(0, usage.limit - usage.delivery_count)
        at_limit = usage.delivery_count >= usage.limit
        over_limit = usage.delivery_count > usage.limit

        return {
            "allowed": not at_limit,  # Block at limit for now
            "remaining": remaining,
            "at_limit": at_limit,
            "over_limit": over_limit,
        }

    async def can_generate_route(self, user_id: UUID, order_length: int) -> bool:
        """Check if user can generate a new route based on delivery limit"""
        logger.info(f"🔄 Checking if user can generate route: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            # No billing customer = free tier with default limit
            logger.info(
                f"✅ No billing customer, allowing route generation for user: {user_id}"
            )
            return True

        usage = await self.usage_repo.get_current_period(customer.id)
        if not usage:
            logger.info(
                f"✅ No active usage record, allowing route generation for user: {user_id}"
            )
            return True

        logger.info(
            f"Current usage for user {user_id}: {usage.delivery_count}/{usage.limit} deliveries"
        )
        at_limit = usage.delivery_count + order_length > usage.limit
        if at_limit:
            logger.warning(
                f"⚠️  User has reached delivery limit: {usage.delivery_count}/{usage.limit}"
            )
        return not at_limit

    # ========================================================================
    # PAYMENTS & INVOICES
    # ========================================================================

    async def get_payment_history(
        self, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Payment]:
        """Get payment history for user"""
        logger.info(f"🔄 Getting payment history for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        payments = await self.payment_repo.get_by_billing_customer_id(
            customer.id, skip=skip, limit=limit
        )
        logger.info(f"✅ Retrieved {len(payments)} payments for user: {user_id}")
        return payments

    async def get_invoice_history(
        self, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Invoice]:
        """Get invoice history for user"""
        logger.info(f"🔄 Getting invoice history for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        invoices = await self.invoice_repo.get_by_billing_customer_id(
            customer.id, skip=skip, limit=limit
        )
        logger.info(f"✅ Retrieved {len(invoices)} invoices for user: {user_id}")
        return invoices

    async def get_invoice_pdf(self, user_id: UUID, invoice_id: UUID) -> Optional[str]:
        """Get invoice PDF URL"""
        logger.info(f"🔄 Getting invoice PDF for invoice: {invoice_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        invoice = await self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            return None

        # Verify ownership
        if invoice.billing_customer_id != customer.id:
            raise ValueError("Invoice does not belong to this user")

        return invoice.invoice_pdf_url

    # ========================================================================
    # STRIPE PORTAL
    # ========================================================================

    async def create_portal_session(self, user_id: UUID, return_url: str) -> str:
        """Create Stripe Customer Portal session"""
        logger.info(f"🔄 Creating portal session for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            raise ValueError(f"Billing customer not found for user: {user_id}")

        try:
            session = await self.stripe_client.create_portal_session(
                customer_id=customer.stripe_customer_id,
                return_url=return_url,
            )
            logger.info(f"✅ Portal session created for user: {user_id}")
            return session["url"]
        except Exception as e:
            logger.error(f"❌ Failed to create portal session: {str(e)}", exc_info=True)
            raise

    # ========================================================================
    # BILLING OVERVIEW
    # ========================================================================

    async def get_billing_overview(self, user_id: UUID) -> Dict[str, Any]:
        """Get complete billing overview for dashboard"""
        logger.info(f"🔄 Getting billing overview for user: {user_id}")

        customer = await self.billing_customer_repo.get_by_user_id(user_id)
        if not customer:
            # Return minimal overview for users without billing setup
            return {
                "customer": None,
                "subscription": None,
                "current_plan": None,
                "usage": None,
                "recent_invoices": [],
                "recent_payments": [],
            }

        # Get subscription
        subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )

        # Get plan if subscription exists
        current_plan = None
        if subscription:
            current_plan = await self.plan_repo.get_by_id(subscription.plan_id)

        # Get usage
        usage = await self.get_current_usage(user_id)

        # Get recent invoices and payments
        recent_invoices = await self.invoice_repo.get_by_billing_customer_id(
            customer.id, skip=0, limit=5
        )
        recent_payments = await self.payment_repo.get_by_billing_customer_id(
            customer.id, skip=0, limit=5
        )

        logger.info(f"✅ Billing overview compiled for user: {user_id}")
        return {
            "customer": customer,
            "subscription": subscription,
            "current_plan": current_plan,
            "usage": usage,
            "recent_invoices": recent_invoices,
            "recent_payments": recent_payments,
        }

    # ========================================================================
    # STRIPE WEBHOOK HANDLER
    # ========================================================================

    async def handle_stripe_webhook(
        self, payload: bytes, signature: str
    ) -> Dict[str, Any]:
        """
        Process Stripe webhook event

        **Verifies signature and dispatches to appropriate handler**
        """
        logger.info("🔄 Processing Stripe webhook")

        # Verify and construct event
        try:
            event = await self.stripe_client.construct_webhook_event(
                payload=payload,
                signature=signature,
            )
        except ValueError as e:
            logger.error(f"❌ Webhook signature verification failed: {str(e)}")
            raise

        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"🔄 Processing webhook event: {event_type}")

        # Dispatch to handler
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(data)
            logger.info(f"✅ Webhook event handled: {event_type}")
        else:
            logger.info(f"ℹ️  Unhandled webhook event type: {event_type}")

        return {"event_type": event_type, "handled": handler is not None}

    # ========================================================================
    # WEBHOOK EVENT HANDLERS (Private)
    # ========================================================================

    async def _handle_checkout_completed(self, data: Dict[str, Any]) -> None:
        """Handle checkout.session.completed - create subscription"""
        logger.info("🔄 Handling checkout.session.completed")

        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")
        plan_price_id = metadata.get("plan_price_id")
        stripe_subscription_id = data.get("subscription")

        if not all([user_id, plan_id, plan_price_id, stripe_subscription_id]):
            logger.error("❌ Missing metadata in checkout session")
            return

        # Get billing customer
        customer = await self.billing_customer_repo.get_by_user_id(UUID(user_id))
        if not customer:
            logger.error(f"❌ Billing customer not found for user: {user_id}")
            return

        # Get subscription details from Stripe
        try:
            stripe_sub = await self.stripe_client.get_subscription(
                stripe_subscription_id
            )
        except Exception as e:
            logger.error(f"❌ Failed to get Stripe subscription: {str(e)}")
            return

        # Create local subscription
        current_subscription = await self.subscription_repo.get_by_billing_customer_id(
            customer.id
        )
        if current_subscription:
            logger.warning(
                f"⚠️  User already has a subscription, updating subscription: {customer.id}"
            )
            subscription = Subscription(
                id=current_subscription.id,
                user_id=UUID(user_id),
                billing_customer_id=customer.id,
                plan_id=UUID(plan_id),
                plan_price_id=UUID(plan_price_id),
                stripe_subscription_id=stripe_subscription_id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.fromtimestamp(
                    stripe_sub.get("current_period_start", 0), tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_sub.get("current_period_end", 0), tz=timezone.utc
                ),
                cancel_at_period_end=False,
            )
            await self.subscription_repo.update(subscription.id, subscription)
            logger.info(
                f"✅ Subscription updated: {subscription.id} "
                f"(stripe: {stripe_subscription_id})"
            )
        else:
            logger.info(f"🔄 Creating new subscription for user: {customer.id}")

            subscription = Subscription(
                id=uuid4(),
                user_id=UUID(user_id) if user_id else None,
                billing_customer_id=customer.id,
                plan_id=UUID(plan_id),
                plan_price_id=UUID(plan_price_id),
                stripe_subscription_id=stripe_subscription_id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.fromtimestamp(
                    stripe_sub.get("current_period_start", 0), tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_sub.get("current_period_end", 0), tz=timezone.utc
                ),
                cancel_at_period_end=False,
            )

            created_sub = await self.subscription_repo.create(subscription)
            logger.info(
                f"✅ Subscription created: {created_sub.id} "
                f"(stripe: {stripe_subscription_id})"
            )

        # Create usage record for this billing period
        plan = await self.plan_repo.get_by_id(UUID(plan_id))
        delivery_limit = plan.monthly_delivery_limit if plan else 300

        usage_record = UsageRecord(
            id=uuid4(),
            billing_customer_id=customer.id,
            subscription_id=created_sub.id,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            delivery_count=0,
            limit=delivery_limit,
            overage_count=0,
        )
        await self.usage_repo.create(usage_record)
        logger.info(
            f"✅ Usage record created for period "
            f"{subscription.current_period_start} - {subscription.current_period_end}"
        )

    async def _handle_subscription_updated(self, data: Dict[str, Any]) -> None:
        """Handle customer.subscription.updated - sync subscription status"""
        logger.info("🔄 Handling customer.subscription.updated")

        stripe_subscription_id = data.get("id")
        if not stripe_subscription_id:
            logger.error("❌ No subscription ID in webhook data")
            return

        # Find local subscription
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(
            stripe_subscription_id
        )
        if not subscription:
            logger.warning(
                f"⚠️  Subscription not found locally: {stripe_subscription_id}"
            )
            return

        # Map Stripe status to local status
        stripe_status = data.get("status", "")
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID,
            "trialing": SubscriptionStatus.TRIALING,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        }

        new_status = status_map.get(stripe_status)
        if new_status:
            subscription.status = new_status

        # Update period
        current_period_start = data.get("current_period_start")
        current_period_end = data.get("current_period_end")

        if current_period_start:
            subscription.current_period_start = datetime.fromtimestamp(
                current_period_start, tz=timezone.utc
            )
        if current_period_end:
            subscription.current_period_end = datetime.fromtimestamp(
                current_period_end, tz=timezone.utc
            )

        subscription.cancel_at_period_end = data.get("cancel_at_period_end", False)

        canceled_at = data.get("canceled_at")
        if canceled_at:
            subscription.canceled_at = datetime.fromtimestamp(
                canceled_at, tz=timezone.utc
            )

        await self.subscription_repo.update(subscription.id, subscription)
        logger.info(f"✅ Subscription updated: {subscription.id} -> {stripe_status}")

        # If period changed, create new usage record
        if current_period_start and current_period_end:
            existing_usage = await self.usage_repo.get_current_period(
                subscription.billing_customer_id
            )
            if not existing_usage:
                plan = await self.plan_repo.get_by_id(subscription.plan_id)
                delivery_limit = plan.monthly_delivery_limit if plan else 300

                usage_record = UsageRecord(
                    id=uuid4(),
                    billing_customer_id=subscription.billing_customer_id,
                    subscription_id=subscription.id,
                    period_start=subscription.current_period_start,
                    period_end=subscription.current_period_end,
                    delivery_count=0,
                    limit=delivery_limit,
                    overage_count=0,
                )
                await self.usage_repo.create(usage_record)
                logger.info("✅ New usage record created for new billing period")

    async def _handle_subscription_deleted(self, data: Dict[str, Any]) -> None:
        """Handle customer.subscription.deleted - mark subscription canceled"""
        logger.info("🔄 Handling customer.subscription.deleted")

        stripe_subscription_id = data.get("id")
        if not stripe_subscription_id:
            logger.error("❌ No subscription ID in webhook data")
            return

        subscription = await self.subscription_repo.get_by_stripe_subscription_id(
            stripe_subscription_id
        )
        if not subscription:
            logger.warning(
                f"⚠️  Subscription not found locally: {stripe_subscription_id}"
            )
            return

        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.now(timezone.utc)

        await self.subscription_repo.update(subscription.id, subscription)
        logger.info(f"✅ Subscription marked as canceled: {subscription.id}")

    async def _handle_invoice_paid(self, data: Dict[str, Any]) -> None:
        """Handle invoice.paid - record successful invoice payment"""
        logger.info("🔄 Handling invoice.paid")

        stripe_invoice_id = data.get("id")
        stripe_customer_id = data.get("customer")
        amount_paid = Decimal(str(data.get("amount_paid", 0))) / 100  # cents to euros
        currency_str = data.get("currency", "eur").upper()

        if not stripe_invoice_id or not stripe_customer_id:
            logger.error("❌ Missing invoice ID or customer ID")
            return

        # Get billing customer
        customer = await self.billing_customer_repo.get_by_stripe_customer_id(
            stripe_customer_id
        )
        if not customer:
            logger.warning(
                f"⚠️  Billing customer not found for stripe: {stripe_customer_id}"
            )
            return

        # Get subscription ID if available
        stripe_subscription_id = data.get("subscription")
        subscription_id = None
        if stripe_subscription_id:
            sub = await self.subscription_repo.get_by_stripe_subscription_id(
                stripe_subscription_id
            )
            if sub:
                subscription_id = sub.id

        # Get currency
        try:
            currency = Currency(currency_str)
        except ValueError:
            currency = Currency.EUR

        # Upsert invoice
        existing_invoice = await self.invoice_repo.get_by_stripe_invoice_id(
            stripe_invoice_id
        )
        if existing_invoice:
            existing_invoice.status = InvoiceStatus.PAID
            existing_invoice.amount_paid = amount_paid
            existing_invoice.paid_at = datetime.now(timezone.utc)
            existing_invoice.invoice_pdf_url = data.get("invoice_pdf")
            await self.invoice_repo.update(existing_invoice.id, existing_invoice)
            logger.info(f"✅ Invoice updated to PAID: {existing_invoice.id}")
        else:
            invoice = Invoice(
                id=uuid4(),
                billing_customer_id=customer.id,
                subscription_id=subscription_id,
                stripe_invoice_id=stripe_invoice_id,
                amount_due=Decimal(str(data.get("amount_due", 0))) / 100,
                amount_paid=amount_paid,
                currency=currency,
                status=InvoiceStatus.PAID,
                invoice_pdf_url=data.get("invoice_pdf"),
                due_date=None,
                paid_at=datetime.now(timezone.utc),
            )
            await self.invoice_repo.create(invoice)
            logger.info(f"✅ Invoice created (PAID): {invoice.id}")

    async def _handle_invoice_payment_failed(self, data: Dict[str, Any]) -> None:
        """Handle invoice.payment_failed - record failed payment"""
        logger.info("🔄 Handling invoice.payment_failed")

        stripe_invoice_id = data.get("id")
        stripe_customer_id = data.get("customer")

        if not stripe_invoice_id or not stripe_customer_id:
            logger.error("❌ Missing invoice ID or customer ID")
            return

        customer = await self.billing_customer_repo.get_by_stripe_customer_id(
            stripe_customer_id
        )
        if not customer:
            logger.warning(
                f"⚠️  Billing customer not found for stripe: {stripe_customer_id}"
            )
            return

        # Get currency
        currency_str = data.get("currency", "eur").upper()
        try:
            currency = Currency(currency_str)
        except ValueError:
            currency = Currency.EUR

        # Upsert invoice
        existing_invoice = await self.invoice_repo.get_by_stripe_invoice_id(
            stripe_invoice_id
        )
        if existing_invoice:
            existing_invoice.status = InvoiceStatus.OPEN
            await self.invoice_repo.update(existing_invoice.id, existing_invoice)
            logger.info(
                f"✅ Invoice marked as OPEN (payment failed): {existing_invoice.id}"
            )
        else:
            invoice = Invoice(
                id=uuid4(),
                billing_customer_id=customer.id,
                subscription_id=None,
                stripe_invoice_id=stripe_invoice_id,
                amount_due=Decimal(str(data.get("amount_due", 0))) / 100,
                amount_paid=Decimal("0.00"),
                currency=currency,
                status=InvoiceStatus.OPEN,
                invoice_pdf_url=data.get("invoice_pdf"),
                due_date=None,
                paid_at=None,
            )
            await self.invoice_repo.create(invoice)
            logger.info(f"✅ Invoice created (OPEN - payment failed): {invoice.id}")

    async def _handle_payment_succeeded(self, data: Dict[str, Any]) -> None:
        """Handle payment_intent.succeeded - record successful payment"""
        logger.info("🔄 Handling payment_intent.succeeded")

        stripe_payment_intent_id = data.get("id")
        stripe_customer_id = data.get("customer")
        amount = Decimal(str(data.get("amount", 0))) / 100
        currency_str = data.get("currency", "eur").upper()

        if not stripe_payment_intent_id or not stripe_customer_id:
            logger.error("❌ Missing payment intent ID or customer ID")
            return

        customer = await self.billing_customer_repo.get_by_stripe_customer_id(
            stripe_customer_id
        )
        if not customer:
            logger.warning(
                f"⚠️  Billing customer not found for stripe: {stripe_customer_id}"
            )
            return

        # Check if payment already exists
        existing = await self.payment_repo.get_by_stripe_payment_intent_id(
            stripe_payment_intent_id
        )
        if existing:
            existing.status = PaymentStatus.SUCCEEDED
            existing.paid_at = datetime.now(timezone.utc)
            await self.payment_repo.update(existing.id, existing)
            logger.info(f"✅ Payment updated to SUCCEEDED: {existing.id}")
            return

        # Get currency
        try:
            currency = Currency(currency_str)
        except ValueError:
            currency = Currency.EUR

        payment = Payment(
            id=uuid4(),
            billing_customer_id=customer.id,
            subscription_id=None,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.SUCCEEDED,
            paid_at=datetime.now(timezone.utc),
            failure_reason=None,
        )
        await self.payment_repo.create(payment)
        logger.info(f"✅ Payment recorded (SUCCEEDED): {payment.id}")

    async def _handle_payment_failed(self, data: Dict[str, Any]) -> None:
        """Handle payment_intent.payment_failed - record failed payment"""
        logger.info("🔄 Handling payment_intent.payment_failed")

        stripe_payment_intent_id = data.get("id")
        stripe_customer_id = data.get("customer")
        amount = Decimal(str(data.get("amount", 0))) / 100
        currency_str = data.get("currency", "eur").upper()

        if not stripe_payment_intent_id or not stripe_customer_id:
            logger.error("❌ Missing payment intent ID or customer ID")
            return

        customer = await self.billing_customer_repo.get_by_stripe_customer_id(
            stripe_customer_id
        )
        if not customer:
            logger.warning(
                f"⚠️  Billing customer not found for stripe: {stripe_customer_id}"
            )
            return

        # Get failure reason
        last_error = data.get("last_payment_error", {})
        failure_reason = last_error.get("message", "Payment failed")

        # Check if payment already exists
        existing = await self.payment_repo.get_by_stripe_payment_intent_id(
            stripe_payment_intent_id
        )
        if existing:
            existing.status = PaymentStatus.FAILED
            existing.failure_reason = failure_reason
            await self.payment_repo.update(existing.id, existing)
            logger.info(f"✅ Payment updated to FAILED: {existing.id}")
            return

        # Get currency
        try:
            currency = Currency(currency_str)
        except ValueError:
            currency = Currency.EUR

        payment = Payment(
            id=uuid4(),
            billing_customer_id=customer.id,
            subscription_id=None,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.FAILED,
            paid_at=None,
            failure_reason=failure_reason,
        )
        await self.payment_repo.create(payment)
        logger.info(f"✅ Payment recorded (FAILED): {payment.id}")
