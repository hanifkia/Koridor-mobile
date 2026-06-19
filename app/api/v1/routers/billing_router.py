"""
Billing router with service layer
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from uuid import UUID
import logging

from app.api.v1.schemas.billing_schemas import (
    PlanPriceSchema,
    PlanResponseSchema,
    PlanListResponseSchema,
    BillingCustomerResponseSchema,
    UpdateBillingInfoSchema,
    SubscriptionResponseSchema,
    CreateSubscriptionRequest,
    ChangeSubscriptionRequest,
    CancelSubscriptionRequest,
    UsageSummarySchema,
    PaymentResponseSchema,
    InvoiceResponseSchema,
    CreateCheckoutSessionRequest,
    CheckoutSessionResponseSchema,
    CreatePortalSessionRequest,
    PortalSessionResponseSchema,
    BillingOverviewSchema,
)
from app.core.services.billing_service import BillingService
from app.config.dependencies import get_billing_service
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


# ============================================================================
# PLANS ENDPOINTS (Public)
# ============================================================================


@router.get(
    "/plans",
    response_model=List[PlanListResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_available_plans(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all available subscription plans

    **Returns:** List of active plans with tier info and limits
    """
    try:
        plans = await billing_service.get_active_plans()
        return [PlanListResponseSchema.from_orm(p) for p in plans]

    except Exception as e:
        logger.error(f"❌ Failed to get plans: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans",
        )


@router.get(
    "/plans/{plan_tier}",
    response_model=PlanResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_plan_details(
    plan_tier: str,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get plan details by tier with pricing

    **Parameters:**
    - plan_tier: Plan tier name (FREE, STARTER, PROFESSIONAL, ENTERPRISE)

    **Returns:** Plan details with all currency prices
    """
    try:
        plan, prices = await billing_service.get_plan_by_tier(plan_tier)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan not found: {plan_tier}",
            )
        plan_response = PlanResponseSchema.model_validate(plan)
        plan_response.prices = (
            [PlanPriceSchema.model_validate(price) for price in prices]
            if prices
            else []
        )
        return plan_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan",
        )


# ============================================================================
# BILLING OVERVIEW
# ============================================================================


@router.get(
    "/overview",
    response_model=BillingOverviewSchema,
    status_code=status.HTTP_200_OK,
)
async def get_billing_overview(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get complete billing overview for current user

    **Returns:** Customer info, subscription, usage, recent invoices/payments
    """
    try:
        overview = await billing_service.get_billing_overview(
            user_id=current_user["user_id"]
        )
        return overview

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get billing overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing overview",
        )


# ============================================================================
# BILLING CUSTOMER ENDPOINTS
# ============================================================================


@router.get(
    "/customer",
    response_model=BillingCustomerResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_billing_customer(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Get billing customer info for current user"""
    try:
        customer = await billing_service.get_or_create_billing_customer(
            user_id=current_user["user_id"]
        )
        return BillingCustomerResponseSchema.from_orm(customer)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get billing customer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing customer",
        )


@router.patch(
    "/customer",
    response_model=BillingCustomerResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_billing_info(
    request: UpdateBillingInfoSchema,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Update billing information"""
    try:
        customer = await billing_service.update_billing_info(
            user_id=current_user["user_id"],
            billing_email=request.billing_email,
            billing_name=request.billing_name,
            tax_id=request.tax_id,
            country_code=request.country_code,
        )
        logger.info(f"✅ Billing info updated for user: {current_user['user_id']}")
        return BillingCustomerResponseSchema.from_orm(customer)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to update billing info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update billing information",
        )


# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================


@router.get(
    "/subscription",
    response_model=SubscriptionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_current_subscription(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Get current active subscription"""
    try:
        subscription = await billing_service.get_active_subscription(
            user_id=current_user["user_id"]
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found",
            )
        return SubscriptionResponseSchema.from_orm(subscription)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription",
        )


@router.post(
    "/subscription",
    response_model=CheckoutSessionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    request: CreateCheckoutSessionRequest,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new subscription via Stripe Checkout

    **Flow:**
    1. Creates/gets Stripe Customer
    2. Creates Stripe Checkout Session
    3. Returns checkout URL for redirect

    **Returns:** Checkout session URL and ID
    """
    try:
        result = await billing_service.create_checkout_session(
            user_id=current_user["user_id"],
            plan_tier=request.plan_tier,
            currency=request.currency,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        logger.info(f"✅ Checkout session created for user: {current_user['user_id']}")
        return CheckoutSessionResponseSchema(
            checkout_url=result["checkout_url"],
            session_id=result["session_id"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to create checkout session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post(
    "/subscription/change",
    response_model=SubscriptionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def change_subscription_plan(
    request: ChangeSubscriptionRequest,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Change subscription plan (upgrade/downgrade)

    **Note:** Pro-ration is handled by Stripe
    """
    try:
        subscription = await billing_service.change_plan(
            user_id=current_user["user_id"],
            new_plan_tier=request.new_plan_tier,
        )
        logger.info(
            f"✅ Plan changed to {request.new_plan_tier} for user: {current_user['user_id']}"
        )
        return SubscriptionResponseSchema.from_orm(subscription)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to change plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change subscription plan",
        )


@router.post(
    "/subscription/cancel",
    response_model=SubscriptionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel subscription

    **Options:**
    - cancel_immediately=false: Cancel at end of billing period (default)
    - cancel_immediately=true: Cancel immediately (no refund)
    """
    try:
        subscription = await billing_service.cancel_subscription(
            user_id=current_user["user_id"],
            cancel_immediately=request.cancel_immediately,
        )
        logger.info(f"✅ Subscription cancelled for user: {current_user['user_id']}")
        return SubscriptionResponseSchema.from_orm(subscription)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to cancel subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )


@router.post(
    "/subscription/reactivate",
    response_model=SubscriptionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def reactivate_subscription(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Reactivate a subscription that was set to cancel at period end

    **Note:** Only works if subscription is still active but set to cancel
    """
    try:
        subscription = await billing_service.reactivate_subscription(
            user_id=current_user["user_id"]
        )
        logger.info(f"✅ Subscription reactivated for user: {current_user['user_id']}")
        return SubscriptionResponseSchema.from_orm(subscription)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to reactivate subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription",
        )


# ============================================================================
# USAGE ENDPOINTS
# ============================================================================


@router.get(
    "/usage",
    response_model=UsageSummarySchema,
    status_code=status.HTTP_200_OK,
)
async def get_current_usage(
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current billing period usage

    **Returns:** Delivery count, limit, overage, and percentage
    """
    try:
        usage = await billing_service.get_current_usage(user_id=current_user["user_id"])
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active usage record found",
            )
        return usage

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get usage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage",
        )


# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================


@router.get(
    "/payments",
    response_model=List[PaymentResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_payment_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Get payment history for current user"""
    try:
        payments = await billing_service.get_payment_history(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit,
        )
        return [PaymentResponseSchema.from_orm(p) for p in payments]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get payments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payments",
        )


# ============================================================================
# INVOICE ENDPOINTS
# ============================================================================


@router.get(
    "/invoices",
    response_model=List[InvoiceResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Get invoice history for current user"""
    try:
        invoices = await billing_service.get_invoice_history(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit,
        )
        return [InvoiceResponseSchema.from_orm(i) for i in invoices]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get invoices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices",
        )


@router.get(
    "/invoices/{invoice_id}/pdf",
    status_code=status.HTTP_200_OK,
)
async def get_invoice_pdf_url(
    invoice_id: UUID,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """Get invoice PDF download URL"""
    try:
        pdf_url = await billing_service.get_invoice_pdf(
            user_id=current_user["user_id"],
            invoice_id=invoice_id,
        )
        if not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice PDF not available",
            )
        return {"pdf_url": pdf_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get invoice PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice PDF",
        )


# ============================================================================
# STRIPE PORTAL ENDPOINT
# ============================================================================


@router.post(
    "/portal",
    response_model=PortalSessionResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def create_customer_portal_session(
    request: CreatePortalSessionRequest,
    billing_service: BillingService = Depends(get_billing_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Create Stripe Customer Portal session

    **Portal allows:**
    - Update payment methods
    - View/download invoices
    - Cancel subscription
    - Update billing info
    """
    try:
        portal_url = await billing_service.create_portal_session(
            user_id=current_user["user_id"],
            return_url=request.return_url,
        )
        logger.info(f"✅ Portal session created for user: {current_user['user_id']}")
        return PortalSessionResponseSchema(portal_url=portal_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to create portal session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session",
        )
