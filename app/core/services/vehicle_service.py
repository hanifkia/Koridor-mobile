# app/core/services/vehicle_service.py
"""
Vehicle service implementation
"""
from datetime import timedelta
from typing import Optional, List
import logging
from uuid import UUID

from app.core.entities import Vehicle, VehicleType
from app.core.interfaces import (
    IVehicleRepository,
    ICourierRepository,
    IUserRepository,
)

logger = logging.getLogger(__name__)


class VehicleService:
    """Service for vehicle operations"""

    def __init__(
        self,
        vehicle_repo: IVehicleRepository,
        courier_repo: ICourierRepository,
        user_repo: IUserRepository,
    ):
        self.vehicle_repo = vehicle_repo
        self.courier_repo = courier_repo
        self.user_repo = user_repo

    async def update_vehicle(
        self,
        user_id: UUID,
        vehicle_id: UUID,
        vehicle_type: Optional[VehicleType] = None,
        weight_capacity: Optional[float] = None,
        volume_capacity: Optional[float] = None,
        loading_cost: Optional[float] = None,
        travel_cost_per_km: Optional[float] = None,
        travel_cost_per_hour: Optional[float] = None,
        loading_time: Optional[int] = None,
        average_speed: Optional[float] = None,
        max_duration: Optional[int] = None,
        fuel_consumption_per_100_km: Optional[float] = None,
        fuel_type: Optional[str] = None,
        max_tasks: Optional[int] = None,
    ) -> Vehicle:
        """
        Update vehicle details

        **Validation:**
        1. Verify user exists
        2. Verify vehicle exists
        3. Verify vehicle belongs to user's courier
        4. Update vehicle

        **Returns:**
        - Updated vehicle entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating vehicle: {vehicle_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User verified: {user.email}")

        # Verify vehicle exists
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            logger.error(f"❌ Vehicle not found: {vehicle_id}")
            raise ValueError(f"Vehicle not found: {vehicle_id}")

        logger.info(f"✅ Vehicle found: {vehicle_id}")

        # Verify vehicle belongs to user's courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier or vehicle.courier_id != courier.id:
            logger.error(f"❌ Vehicle {vehicle_id} does not belong to user {user_id}")
            raise ValueError("Vehicle does not belong to your courier")

        logger.info(f"✅ Vehicle ownership verified")

        # Update vehicle
        try:
            vehicle.vehicle_type = vehicle_type or vehicle.vehicle_type
            vehicle.weight_capacity = weight_capacity or vehicle.weight_capacity
            vehicle.volume_capacity = volume_capacity or vehicle.volume_capacity
            vehicle.loading_cost = loading_cost or vehicle.loading_cost
            vehicle.travel_cost_per_km = (
                travel_cost_per_km or vehicle.travel_cost_per_km
            )
            vehicle.travel_cost_per_hour = (
                travel_cost_per_hour or vehicle.travel_cost_per_hour
            )
            vehicle.loading_time = (
                timedelta(seconds=loading_time)
                if loading_time is not None
                else vehicle.loading_time
            )
            vehicle.average_speed = average_speed or vehicle.average_speed
            vehicle.max_duration = (
                timedelta(seconds=max_duration)
                if max_duration is not None
                else vehicle.max_duration
            )
            vehicle.fuel_consumption_per_100_km = (
                fuel_consumption_per_100_km or vehicle.fuel_consumption_per_100_km
            )
            vehicle.fuel_type = fuel_type or vehicle.fuel_type
            vehicle.max_tasks = max_tasks or vehicle.max_tasks

            updated_vehicle = await self.vehicle_repo.update(vehicle_id, vehicle)
            logger.info(f"✅ Vehicle updated: {vehicle_id}")

            courier.vehicle_type = vehicle.vehicle_type
            await self.courier_repo.update(courier.id, courier)

            return updated_vehicle

        except Exception as e:
            logger.error(f"❌ Error updating vehicle: {str(e)}", exc_info=True)
            raise

    async def get_user_vehicles(self, user_id: UUID) -> List[Vehicle]:
        """
        Get all vehicles for a user's courier

        **Returns:**
        - List of vehicle entities

        **Raises:**
        - ValueError: If courier not found
        """
        logger.info(f"🔄 Getting vehicles for user: {user_id}")

        # Fetch courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Fetch vehicles
        vehicles = await self.vehicle_repo.get_by_courier_id(courier.id)
        logger.info(f"✅ Retrieved {len(vehicles)} vehicles")

        return vehicles

    async def get_active_vehicles(self, user_id: UUID) -> List[Vehicle]:
        """
        Get all active vehicles for a user's courier

        **Returns:**
        - List of vehicle entities

        **Raises:**
        - ValueError: If courier not found
        """
        logger.info(f"🔄 Getting active vehicles for user: {user_id}")

        # Fetch courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Fetch active vehicles
        vehicles = await self.vehicle_repo.get_active_by_courier_id(courier.id)
        logger.info(f"✅ Retrieved {len(vehicles)} active vehicles")

        return vehicles

    async def deactivate_vehicle(self, user_id: UUID, vehicle_id: UUID) -> bool:
        """
        Deactivate a vehicle

        **Validation:**
        1. Verify vehicle exists and belongs to user

        **Returns:**
        - True if deactivated

        **Raises:**
        - ValueError: If validation fails
        """
        logger.info(f"🔄 Deactivating vehicle: {vehicle_id}")

        # Verify vehicle exists and belongs to user
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle not found: {vehicle_id}")

        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier or vehicle.courier_id != courier.id:
            raise ValueError("Vehicle does not belong to your courier")

        success = await self.vehicle_repo.deactivate(vehicle_id)
        if not success:
            raise ValueError(f"Failed to deactivate vehicle: {vehicle_id}")

        logger.info(f"✅ Vehicle deactivated: {vehicle_id}")
        return True

    async def activate_vehicle(self, user_id: UUID, vehicle_id: UUID) -> bool:
        """
        Activate a vehicle

        **Validation:**
        1. Verify vehicle exists and belongs to user

        **Returns:**
        - True if activated

        **Raises:**
        - ValueError: If validation fails
        """
        logger.info(f"🔄 Activating vehicle: {vehicle_id}")

        # Verify vehicle exists and belongs to user
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle not found: {vehicle_id}")

        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier or vehicle.courier_id != courier.id:
            raise ValueError("Vehicle does not belong to your courier")

        success = await self.vehicle_repo.activate(vehicle_id)
        if not success:
            raise ValueError(f"Failed to activate vehicle: {vehicle_id}")

        logger.info(f"✅ Vehicle activated: {vehicle_id}")
        return True
