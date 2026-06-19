# app/core/services/courier_service.py
"""
Courier service implementation
"""
from typing import Optional
import logging
from uuid import UUID, uuid4

from app.core.entities import Courier, Vehicle, VehicleType, User
from app.core.entities.constants import VehicleDefaultConstants
from app.core.interfaces import (
    ICourierRepository,
    IUserRepository,
    IVehicleRepository,
)

logger = logging.getLogger(__name__)


class CourierService:
    """Service for courier operations"""

    def __init__(
        self,
        courier_repo: ICourierRepository,
        user_repo: IUserRepository,
        vehicle_repo: IVehicleRepository,
    ):
        self.courier_repo = courier_repo
        self.user_repo = user_repo
        self.vehicle_repo = vehicle_repo

    async def setup_courier(
        self,
        user_id: UUID,
        vehicle_type: VehicleType,
        country: str,
        state: str,
        city: str,
    ) -> Courier:
        """
        Setup courier profile and create default vehicle

        **Validation:**
        1. Verify user exists
        2. Check courier doesn't already exist
        3. Create courier
        4. Create default vehicle

        **Returns:**
        - Created courier entity

        **Raises:**
        - ValueError: If user not found or courier already exists
        - Exception: If creation fails
        """

        # TODO: session transaction and rollback handling

        logger.info(f"🔄 Setting up courier for user: {user_id}")

        # Verify user exists
        user: User = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User verified: {user.email}")

        # Check courier doesn't already exist
        existing_courier = await self.courier_repo.get_by_user_id(user_id)
        if existing_courier:
            logger.error(f"❌ Courier already exists for user: {user.username}")
            raise ValueError(f"Courier already exists for user: {user.username}")

        logger.info(f"✅ No existing courier found")

        # Create courier
        try:
            logger.info(f"🔄 Creating courier profile")

            courier = Courier(
                id=uuid4(),
                user_id=user_id,
                vehicle_type=vehicle_type,
                country=country,
                state=state,
                city=city,
            )

            created_courier = await self.courier_repo.create(courier)
            logger.info(f"✅ Courier created: {created_courier.id}")

            # Create default vehicle
            await self._create_default_vehicle(created_courier.id, vehicle_type)

            logger.info(f"✅ Courier setup completed")

            user.is_courier_profile_completed = True
            await self.user_repo.update(user_id, user)

            logger.info(f"✅ User courier profile marked as completed")

            return created_courier

        except Exception as e:
            logger.error(f"❌ Error creating courier: {str(e)}", exc_info=True)
            raise

    async def _create_default_vehicle(
        self, courier_id: UUID, vehicle_type: VehicleType
    ) -> Vehicle:
        """Create default vehicle for courier based on vehicle type"""
        try:
            logger.info(f"🔄 Creating default vehicle for courier: {courier_id}")

            vehicle_defaults = VehicleDefaultConstants[vehicle_type.name].value

            vehicle = Vehicle(
                id=uuid4(),
                courier_id=courier_id,
                vehicle_type=vehicle_type,
                weight_capacity=vehicle_defaults.weight_capacity,
                volume_capacity=vehicle_defaults.volume_capacity,
                loading_cost=vehicle_defaults.loading_cost,
                travel_cost_per_km=vehicle_defaults.travel_cost_per_km,
                travel_cost_per_hour=vehicle_defaults.travel_cost_per_hour,
                loading_time=vehicle_defaults.loading_time,
                average_speed=vehicle_defaults.average_speed,
                max_duration=vehicle_defaults.max_duration,
                fuel_consumption_per_100_km=vehicle_defaults.fuel_consumption_per_100_km,
                fuel_type=vehicle_defaults.fuel_type,
                max_tasks=vehicle_defaults.max_tasks,
            )

            created_vehicle = await self.vehicle_repo.create(vehicle)
            logger.info(f"✅ Default vehicle created: {created_vehicle.id}")

            return created_vehicle

        except Exception as e:
            logger.error(f"❌ Error creating default vehicle: {str(e)}", exc_info=True)
            raise

    async def update_courier(
        self,
        user_id: UUID,
        vehicle_type: Optional[VehicleType] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Courier:
        """
        Update courier profile

        **Validation:**
        1. Verify user exists
        2. Fetch courier
        3. Update courier

        **Returns:**
        - Updated courier entity

        **Raises:**
        - ValueError: If user or courier not found
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating courier for user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User verified: {user.email}")

        # Fetch courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Update courier
        try:
            courier.vehicle_type = vehicle_type or courier.vehicle_type
            courier.country = country or courier.country
            courier.state = state or courier.state
            courier.city = city or courier.city

            updated_courier = await self.courier_repo.update(courier.id, courier)
            logger.info(f"✅ Courier updated: {courier.id}")

            vehicle = await self.vehicle_repo.get_by_courier_id(courier.id)
            if vehicle and vehicle_type:
                vehicle[0].vehicle_type = vehicle_type
                await self.vehicle_repo.update(vehicle[0].id, vehicle[0])
                logger.info(f"✅ Vehicle updated with new type: {vehicle[0].id}")

            return updated_courier

        except Exception as e:
            logger.error(f"❌ Error updating courier: {str(e)}", exc_info=True)
            raise

    async def get_courier(self, user_id: UUID) -> Courier:
        """
        Get courier for a user

        **Returns:**
        - Courier entity

        **Raises:**
        - ValueError: If courier not found
        """
        logger.info(f"🔄 Getting courier for user: {user_id}")

        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier retrieved: {courier.id}")
        return courier
