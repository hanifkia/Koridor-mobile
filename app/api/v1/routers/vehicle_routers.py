"""
Terminal router with service layer
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import logging

from app.api.v1.schemas.vehicle_schemas import (
    VehicleUpdateSchema,
    VehicleResponseSchema,
)
from app.core.entities import Vehicle
from app.core.services.vehicle_service import VehicleService
from app.config.dependencies import (
    get_vehicle_service,
)
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/vehicle", tags=["Vehicle"])
logger = logging.getLogger(__name__)


@router.get(
    "/vehicles",
    status_code=status.HTTP_200_OK,
    response_model=list[VehicleResponseSchema],
)
async def get_vehicles(
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    current_user: dict = Depends(get_current_user),
):
    """Get all vehicles for user"""

    try:
        vehicles: List[Vehicle] = await vehicle_service.get_user_vehicles(
            user_id=current_user["user_id"]
        )
        return [VehicleResponseSchema.from_orm(vehicle) for vehicle in vehicles]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_200_OK,
    response_model=VehicleResponseSchema,
)
async def update_vehicle(
    vehicle_id: UUID,
    request: VehicleUpdateSchema,
    vehicle_service: VehicleService = Depends(get_vehicle_service),
    current_user: dict = Depends(get_current_user),
):
    """Update vehicle"""

    try:
        vehicle: Vehicle = await vehicle_service.update_vehicle(
            user_id=current_user["user_id"],
            vehicle_id=vehicle_id,
            vehicle_type=request.vehicle_type,
            weight_capacity=request.weight_capacity,
            volume_capacity=request.volume_capacity,
            loading_cost=request.loading_cost,
            travel_cost_per_km=request.travel_cost_per_km,
            travel_cost_per_hour=request.travel_cost_per_hour,
            loading_time=request.loading_time,
            average_speed=request.average_speed,
            max_duration=request.max_duration,
            fuel_consumption_per_100_km=request.fuel_consumption_per_100_km,
            fuel_type=request.fuel_type,
            max_tasks=request.max_tasks,
        )
        logger.info(f"✅ Vehicle updated: {vehicle.id}")
        return VehicleResponseSchema.from_orm(vehicle)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
