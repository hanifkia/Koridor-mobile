# app/api/v1/routers/terminal_router.py
"""
Terminal router with service layer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import logging

from app.api.v1.schemas.courier_schemas import (
    CourierCreateSchema,
    CourierUpdateSchema,
    CourierResponseSchema,
)
from app.core.entities import Courier
from app.core.services.courier_service import CourierService
from app.config.dependencies import (
    get_courier_service,
)
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/courier", tags=["Courier"])
logger = logging.getLogger(__name__)


# ============================================================================
# COURIER ENDPOINTS
# ============================================================================


@router.post(
    "/setup", status_code=status.HTTP_201_CREATED, response_model=CourierResponseSchema
)
async def setup_courier(
    request: CourierCreateSchema,
    courier_service: CourierService = Depends(get_courier_service),
    current_user: dict = Depends(get_current_user),
):
    """Setup courier profile"""
    try:
        courier: Courier = await courier_service.setup_courier(
            user_id=current_user.get("user_id"),
            vehicle_type=request.vehicle_type,
            country=request.country,
            state=request.state,
            city=request.city,
        )
        logger.info(f"✅ Courier created: {courier.id}")
        return CourierResponseSchema.from_orm(courier)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup courier",
        )


@router.patch(
    "/update", status_code=status.HTTP_200_OK, response_model=CourierResponseSchema
)
async def update_courier(
    request: CourierUpdateSchema,
    courier_service: CourierService = Depends(get_courier_service),
    current_user: dict = Depends(get_current_user),
):
    """Update courier profile"""
    try:
        courier: Courier = await courier_service.update_courier(
            user_id=current_user.get("user_id"),
            vehicle_type=request.vehicle_type,
            country=request.country,
            state=request.state,
            city=request.city,
        )
        logger.info(f"✅ Courier updated: {courier.id}")
        return CourierResponseSchema.from_orm(courier)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update courier",
        )


@router.get("/", status_code=status.HTTP_200_OK, response_model=CourierResponseSchema)
async def get_courier(
    courier_service: CourierService = Depends(get_courier_service),
    current_user: dict = Depends(get_current_user),
):
    """Get courier profile"""

    try:
        courier: Courier = await courier_service.get_courier(
            current_user.get("user_id")
        )
        return CourierResponseSchema.from_orm(courier)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
