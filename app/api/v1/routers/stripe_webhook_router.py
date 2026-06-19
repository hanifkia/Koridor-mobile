"""
Stripe webhook handler
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status

from app.core.services.billing_service import BillingService
from app.config.dependencies import get_billing_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    billing_service: BillingService = Depends(get_billing_service),
):
    """
    Handle Stripe webhook events

    **Events handled:**
    - checkout.session.completed → Create subscription
    - customer.subscription.updated → Update subscription status
    - customer.subscription.deleted → Mark subscription canceled
    - invoice.paid → Record payment & update invoice
    - invoice.payment_failed → Record failed payment
    - payment_intent.succeeded → Record successful payment
    - payment_intent.payment_failed → Record failed payment

    **Security:** Validates Stripe webhook signature
    """
    try:
        # Read raw body for signature verification
        payload = await request.body()

        if not stripe_signature:
            logger.warning("⚠️  Webhook received without signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header",
            )

        # Process webhook (signature verification inside service)
        result = await billing_service.handle_stripe_webhook(
            payload=payload,
            signature=stripe_signature,
        )

        logger.info(f"✅ Webhook processed: {result.get('event_type', 'unknown')}")
        return {"status": "ok", "event_type": result.get("event_type")}

    except ValueError as e:
        logger.error(f"❌ Webhook signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
