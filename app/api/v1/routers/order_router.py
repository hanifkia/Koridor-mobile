# app/adapters/http/routers/order_router.py
"""
Order routes - Refactored with service layer
"""

import logging
import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_filter import FilterDepends

from app.api.v1.schemas.order_schemas import (
    CreateOrderRequest,
    UpdateOrderRequest,
    OrderResponse,
    PostponeOrdersRequest,
    RecipientSchema,
    CoordinatesSchema,
    AddressSchema,
)
from app.api.v1.schemas._shared import PaginatedResponse
from app.adapters.filters.order_filter import OrderFilter
from app.config.dependencies import get_order_service
from app.config.security import get_current_user
from app.core.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Order with barcode already exists"},
        status.HTTP_404_NOT_FOUND: {"description": "Courier, Hub, or Shift not found"},
    },
)
async def create_order(
    terminal_id: UUID,
    shift_id: UUID,
    order_request: CreateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> OrderResponse:
    """
    Create a new order

    **Authorization:** Current user must match user_id

    **Request body:**
    - name: Order name
    - barcode: Unique order barcode
    - weight_occupation: Weight in kg
    - volume_occupation: Volume in m³
    - expected_delivery_date: Expected delivery date
    - is_return: Is return order
    - recipient: Recipient details with location and address

    **Returns:** Created order (status 201)

    **Errors:**
    - 403: User not authorized
    - 404: Courier, Hub, or Shift not found
    - 409: Barcode already exists
    """
    try:
        # Create order through service
        created_order = await order_service.create_order(
            user_id=current_user["user_id"],
            terminal_id=terminal_id,
            shift_id=shift_id,
            order_request=order_request,
        )

        logger.info(f"✅ Order created via API: {created_order.id}")
        return OrderResponse.from_orm(created_order)

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"⚠️  Validation error: {error_msg}")

        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        elif "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    except Exception as e:
        logger.error(f"❌ Error creating order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


@router.get(
    "/courier",
    response_model=PaginatedResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
)
async def get_courier_all_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[OrderResponse]:
    """
    Get all orders for a courier

    **Authorization:** Current user must match user_id

    **Query parameters:**
    - page: Page number (default: 1)
    - limit: Number of records to return (default: 10, max: 100)

    **Returns:** List of orders
    """
    try:
        skip = (page - 1) * limit

        # Get orders through service
        orders, recipients, users, total_count = await order_service.get_courier_orders(
            user_id=current_user["user_id"],
            skip=skip,
            limit=limit,
        )

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        logger.info(
            f"✅ Retrieved {len(orders)} orders for user {current_user['user_id']}"
        )

        # Create lookup dictionaries for efficient mapping
        recipients_map = {r.id: r for r in recipients}
        users_map = {u.id: u for u in users}

        # Build response data
        response_data = []
        for order in orders:
            recipient_data = recipients_map.get(order.recipient_id)
            user_data = (
                users_map.get(recipient_data.user_id) if recipient_data else None
            )

            recipient_schema = None
            if recipient_data and user_data:
                recipient_schema = RecipientSchema(
                    name=f"{user_data.first_name} {user_data.last_name}",
                    phone_number=user_data.phone_number,
                    email=user_data.email,
                    location=(
                        CoordinatesSchema.from_orm(recipient_data.location)
                        if recipient_data.location
                        else None
                    ),
                    address=(
                        AddressSchema.from_orm(recipient_data.address)
                        if recipient_data.address
                        else None
                    ),
                )

            response_data.append(
                OrderResponse(
                    id=order.id,
                    terminal_id=order.terminal_id,
                    shift_id=order.shift_id,
                    courier_id=order.courier_id,
                    recipient_id=order.recipient_id,
                    name=order.name,
                    barcode=order.barcode,
                    status=order.status,
                    time_window=order.time_window,
                    weight_occupation=order.weight_occupation,
                    volume_occupation=order.volume_occupation,
                    is_return=order.is_return,
                    original_delivery_date=(
                        order.original_delivery_date.date()
                        if order.original_delivery_date
                        else None
                    ),
                    expected_delivery_date=(
                        order.expected_delivery_date.date()
                        if order.expected_delivery_date
                        else None
                    ),
                    actual_delivery_date=(
                        order.actual_delivery_date.date()
                        if order.actual_delivery_date
                        else None
                    ),
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    recipient=recipient_schema,
                )
            )

        return PaginatedResponse(
            data=response_data,
            total_count=total_count,
            total_pages=total_pages,
            current_page=page,
            per_page=limit,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error getting orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders",
        )


@router.get(
    "/courier/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order_by_id(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> OrderResponse:
    """
    Get order by ID

    **Authorization:** Current user must match user_id

    **Path parameters:**
    - user_id: User UUID
    - order_id: Order UUID

    **Returns:** Order details
    """
    try:

        order, recipient, user = await order_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        logger.info(f"✅ Retrieved order: {order_id}")

        recipientSchema = None
        if recipient and user:
            recipientSchema = RecipientSchema(
                name=f"{user.first_name} {user.last_name}",
                phone_number=user.phone_number,
                email=user.email,
                location=(
                    CoordinatesSchema.from_orm(recipient.location)
                    if recipient.location
                    else None
                ),
                address=(
                    AddressSchema.from_orm(recipient.address)
                    if recipient.address
                    else None
                ),
            )
        return OrderResponse(
            id=order.id,
            terminal_id=order.terminal_id,
            shift_id=order.shift_id,
            courier_id=order.courier_id,
            recipient_id=order.recipient_id,
            name=order.name,
            barcode=order.barcode,
            status=order.status,
            time_window=order.time_window,
            weight_occupation=order.weight_occupation,
            volume_occupation=order.volume_occupation,
            is_return=order.is_return,
            original_delivery_date=(
                order.original_delivery_date.date()
                if order.original_delivery_date
                else None
            ),
            expected_delivery_date=(
                order.expected_delivery_date.date()
                if order.expected_delivery_date
                else None
            ),
            actual_delivery_date=(
                order.actual_delivery_date.date()
                if order.actual_delivery_date
                else None
            ),
            created_at=order.created_at,
            updated_at=order.updated_at,
            recipient=recipientSchema,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order",
        )


@router.get(
    "/search",
    response_model=PaginatedResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
)
async def filter_orders(
    filter_params: OrderFilter = FilterDepends(OrderFilter),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[OrderResponse]:
    """
    Filter orders with advanced parameters

    **Authorization:** Current user must match user_id

    **Query parameters:**
    - Filter parameters from OrderFilter
    - page: Page number
    - limit: Number of records to return

    **Returns:** Filtered orders
    """
    try:
        skip = (page - 1) * limit

        orders, recipients, users, total_count = await order_service.filter_orders(
            filter_params=filter_params,
            skip=skip,
            limit=limit,
        )

        logger.info(
            f"✅ Retrieved {len(orders)} filtered orders (total: {total_count})"
        )
        # Create lookup dictionaries for efficient mapping
        recipients_map = {r.id: r for r in recipients}
        users_map = {u.id: u for u in users}

        # Build response data
        response_data = []
        for order in orders:
            recipient_data = recipients_map.get(order.recipient_id)
            user_data = (
                users_map.get(recipient_data.user_id) if recipient_data else None
            )

            recipient_schema = None
            if recipient_data and user_data:
                recipient_schema = RecipientSchema(
                    name=f"{user_data.first_name} {user_data.last_name}",
                    phone_number=user_data.phone_number,
                    email=user_data.email,
                    location=(
                        CoordinatesSchema.from_orm(recipient_data.location)
                        if recipient_data.location
                        else None
                    ),
                    address=(
                        AddressSchema.from_orm(recipient_data.address)
                        if recipient_data.address
                        else None
                    ),
                )

            response_data.append(
                OrderResponse(
                    id=order.id,
                    terminal_id=order.terminal_id,
                    shift_id=order.shift_id,
                    courier_id=order.courier_id,
                    recipient_id=order.recipient_id,
                    name=order.name,
                    barcode=order.barcode,
                    status=order.status,
                    time_window=order.time_window,
                    weight_occupation=order.weight_occupation,
                    volume_occupation=order.volume_occupation,
                    is_return=order.is_return,
                    original_delivery_date=(
                        order.original_delivery_date.date()
                        if order.original_delivery_date
                        else None
                    ),
                    expected_delivery_date=(
                        order.expected_delivery_date.date()
                        if order.expected_delivery_date
                        else None
                    ),
                    actual_delivery_date=(
                        order.actual_delivery_date.date()
                        if order.actual_delivery_date
                        else None
                    ),
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    recipient=recipient_schema,
                )
            )

        return PaginatedResponse(
            data=response_data,
            total_count=total_count,
            total_pages=math.ceil(total_count / limit) if total_count > 0 else 1,
            current_page=page,
            per_page=limit,
            has_next=page < math.ceil(total_count / limit) if total_count > 0 else 1,
            has_previous=page > 1,
        )

    except Exception as e:
        logger.error(f"❌ Error filtering orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter orders",
        )


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def update_order(
    order_id: UUID,
    order_request: UpdateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> OrderResponse:
    """
    Update an order

    **Authorization:** Current user must match user_id and be the recipient

    **Path parameters:**
    - user_id: User UUID
    - order_id: Order UUID

    **Request body:**
    - name: Order name (optional)
    - barcode: Order barcode (optional)
    - weight_occupation: Weight in kg (optional)
    - volume_occupation: Volume in m³ (optional)
    - expected_delivery_date: Expected delivery date (optional)
    - is_return: Is return order (optional)
    - recipient: Recipient details (optional)

    **Returns:** Updated order

    **Errors:**
    - 403: User not authorized
    - 404: Order or recipient not found
    - 400: Order cannot be updated in current state
    """
    try:

        # Update order through service
        updated_order = await order_service.update_order(
            order_id=order_id,
            order_request=order_request,
            user_id=current_user["user_id"],
        )

        logger.info(f"✅ Order updated: {order_id}")
        return OrderResponse.from_orm(updated_order)

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"⚠️  Validation error: {error_msg}")

        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        elif "not authorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        elif "cannot update" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    except Exception as e:
        logger.error(f"❌ Error updating order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order",
        )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Delete an order

    **Authorization:** Current user must match user_id and be the recipient

    **Path parameters:**
    - user_id: User UUID
    - order_id: Order UUID

    **Returns:** 204 No Content

    **Errors:**
    - 403: User not authorized
    - 404: Order not found
    - 400: Order cannot be deleted in current state
    """
    try:

        # Delete order through service
        deleted = await order_service.delete_order(
            order_id=order_id,
            user_id=current_user["user_id"],
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete order",
            )

        logger.info(f"✅ Order deleted: {order_id}")

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"⚠️  Validation error: {error_msg}")

        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        elif "not authorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )
        elif "cannot delete" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order",
        )


@router.get(
    "/unassigned",
    response_model=PaginatedResponse[OrderResponse],
)
async def get_unassigned_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[OrderResponse]:
    """
    Get unassigned orders for a courier

    **Authorization:** Current user must match user_id

    **Query parameters:**
    - user_id: User UUID (required)
    - page: Page number (default: 1)
    - limit: Items per page (default: 10)

    **Returns:** List of unassigned orders
    """
    try:
        skip = (page - 1) * limit

        orders, total_count = await order_service.get_unassigned_orders(
            user_id=current_user["user_id"],  # TODO: Note: Should be courier_id
            skip=skip,
            limit=limit,
        )

        if not orders:
            logger.info(
                f"ℹ️  No unassigned orders found for courier {current_user['user_id']}"
            )
            return PaginatedResponse[OrderResponse](
                data=[], total=0, page=page, limit=limit
            )

        logger.info(f"✅ Retrieved {len(orders)} unassigned orders for courier")
        return PaginatedResponse(
            data=[OrderResponse.from_orm(o) for o in orders],
            total_count=total_count,
            total_pages=math.ceil(total_count / limit) if total_count > 0 else 1,
            current_page=page,
            per_page=limit,
            has_next=page < math.ceil(total_count / limit) if total_count > 0 else 1,
            has_previous=page > 1,
        )

    except Exception as e:
        logger.error(f"❌ Error getting unassigned orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve unassigned orders",
        )


@router.post(
    "/postpone",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
)
async def postpone_orders(
    request: PostponeOrdersRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
) -> list[OrderResponse]:
    """
    Postpone multiple orders to a new delivery date

    **Authorization:** Current user must match user_id

    **Path parameters:**
    - user_id: User UUID

    **Request body:**
    - order_ids: List of order UUIDs
    - terminal_id: Hub UUID
    - shift_id: Shift UUID
    - new_delivery_date: New delivery date

    **Returns:** List of postponed orders

    **Errors:**
    - 403: User not authorized
    - 404: Hub or shift not found
    - 400: Invalid date or shift time passed
    """
    try:

        # Postpone orders through service
        postponed_orders = await order_service.postpone_orders(
            request=request,
            user_id=current_user["user_id"],
        )

        logger.info(f"✅ Postponed {len(postponed_orders)} orders")
        return [OrderResponse.from_orm(o) for o in postponed_orders]

    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"⚠️  Validation error: {error_msg}")

        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        elif (
            "date has passed" in error_msg.lower()
            or "time has passed" in error_msg.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        elif "does not belong" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error postponing orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to postpone orders",
        )
