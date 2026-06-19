# app/adapters/clients/stripe/stripe_client.py
"""
Stripe async client wrapper
"""

import logging
from typing import Dict, Any, Optional

import stripe
from app.config.settings import settings

logger = logging.getLogger(__name__)


class StripeAsyncClient:
    """Async wrapper for Stripe API operations"""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        logger.info("🔄 StripeAsyncClient initialized")

    # ========================================================================
    # CUSTOMER
    # ========================================================================

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Stripe Customer"""
        logger.info(f"🔄 Creating Stripe customer: {email}")
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            logger.info(f"✅ Stripe customer created: {customer.id}")
            return {"id": customer.id, "email": customer.email}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error creating customer: {str(e)}")
            raise

    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a Stripe Customer"""
        logger.info(f"🔄 Updating Stripe customer: {customer_id}")
        try:
            params = {}
            if email:
                params["email"] = email
            if name:
                params["name"] = name

            customer = stripe.Customer.modify(customer_id, **params)
            logger.info(f"✅ Stripe customer updated: {customer_id}")
            return {"id": customer.id}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error updating customer: {str(e)}")
            raise

    # ========================================================================
    # CHECKOUT SESSION
    # ========================================================================

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout Session"""
        logger.info(f"🔄 Creating checkout session for customer: {customer_id}")
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            logger.info(f"✅ Checkout session created: {session.id}")
            return {"id": session.id, "url": session.url}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error creating checkout: {str(e)}")
            raise

    # ========================================================================
    # SUBSCRIPTION
    # ========================================================================

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get Stripe Subscription details"""
        logger.info(f"🔄 Getting Stripe subscription: {subscription_id}")
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error getting subscription: {str(e)}")
            raise

    async def update_subscription(
        self, subscription_id: str, new_price_id: str
    ) -> Dict[str, Any]:
        """Update Stripe Subscription (change plan)"""
        logger.info(f"🔄 Updating Stripe subscription: {subscription_id}")
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            updated_sub = stripe.Subscription.modify(
                subscription_id,
                items=[
                    {
                        "id": sub["items"]["data"][0].id,
                        "price": new_price_id,
                    }
                ],
                proration_behavior="create_prorations",
            )
            logger.info(f"✅ Stripe subscription updated: {subscription_id}")
            return {"id": updated_sub.id, "status": updated_sub.status}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error updating subscription: {str(e)}")
            raise

    async def cancel_subscription(
        self, subscription_id: str, immediately: bool = False
    ) -> Dict[str, Any]:
        """Cancel Stripe Subscription"""
        logger.info(
            f"🔄 Cancelling Stripe subscription: {subscription_id} "
            f"(immediately={immediately})"
        )
        try:
            if immediately:
                sub = stripe.Subscription.delete(subscription_id)
            else:
                sub = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            logger.info(f"✅ Stripe subscription cancelled: {subscription_id}")
            return {"id": sub.id, "status": sub.status}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error cancelling subscription: {str(e)}")
            raise

    async def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Reactivate Stripe Subscription (undo cancel at period end)"""
        logger.info(f"🔄 Reactivating Stripe subscription: {subscription_id}")
        try:
            sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
            )
            logger.info(f"✅ Stripe subscription reactivated: {subscription_id}")
            return {"id": sub.id, "status": sub.status}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error reactivating subscription: {str(e)}")
            raise

    # ========================================================================
    # CUSTOMER PORTAL
    # ========================================================================

    async def create_portal_session(
        self, customer_id: str, return_url: str
    ) -> Dict[str, Any]:
        """Create Stripe Customer Portal Session"""
        logger.info(f"🔄 Creating portal session for customer: {customer_id}")
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"✅ Portal session created: {session.id}")
            return {"id": session.id, "url": session.url}
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe error creating portal session: {str(e)}")
            raise

    # ========================================================================
    # WEBHOOK
    # ========================================================================

    async def construct_webhook_event(
        self, payload: bytes, signature: str
    ) -> Dict[str, Any]:
        """Verify and construct webhook event from Stripe"""
        logger.info("🔄 Verifying webhook signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self.webhook_secret,
            )
            logger.info(f"✅ Webhook verified: {event['type']}")
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Webhook signature verification failed: {str(e)}")
            raise ValueError(f"Invalid webhook signature: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Webhook construction failed: {str(e)}")
            raise
