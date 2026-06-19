"""
Vehicle repository implementation
"""

from typing import List, Optional
import logging
from decimal import Decimal
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.core.entities import Vehicle, VehicleType, FuelType
from app.core.interfaces import IVehicleRepository
from app.adapters.database.models import VehicleORM, CourierORM

logger = logging.getLogger(__name__)


class VehicleRepositoryImp(IVehicleRepository):
    """Vehicle repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Vehicle) -> Vehicle:
        """Create a new vehicle"""
        try:
            logger.info(
                f"🔄 Creating vehicle for courier: {entity.courier_id} "
                f"({entity.vehicle_type.value})"
            )

            vehicle_orm = VehicleORM(
                id=entity.id,
                courier_id=entity.courier_id,
                vehicle_type=entity.vehicle_type,
                weight_capacity=entity.weight_capacity,
                volume_capacity=entity.volume_capacity,
                loading_cost=entity.loading_cost,
                travel_cost_per_km=entity.travel_cost_per_km,
                travel_cost_per_hour=entity.travel_cost_per_hour,
                loading_time=entity.loading_time,
                average_speed=entity.average_speed,
                max_duration=entity.max_duration,
                fuel_consumption_per_100_km=entity.fuel_consumption_per_100_km,
                fuel_type=entity.fuel_type,
                max_tasks=entity.max_tasks,
            )
            self.session.add(vehicle_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Vehicle created: {entity.id}")
            return await self._orm_to_entity(vehicle_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error creating vehicle: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        try:
            query = (
                select(VehicleORM)
                .where(VehicleORM.id == entity_id)
                .options(joinedload(VehicleORM.courier))
            )
            result = await self.session.execute(query)
            vehicle_orm = result.unique().scalar_one_or_none()
            if not vehicle_orm:
                logger.debug(f"Vehicle not found: {entity_id}")
                return None
            return await self._orm_to_entity(vehicle_orm)
        except Exception as e:
            logger.error(f"❌ Error getting vehicle by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get all vehicles with pagination"""
        try:
            query = (
                select(VehicleORM)
                .offset(skip)
                .limit(limit)
                .options(joinedload(VehicleORM.courier))
            )
            result = await self.session.execute(query)
            vehicles_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(v) for v in vehicles_orm]
        except Exception as e:
            logger.error(f"❌ Error getting all vehicles: {str(e)}", exc_info=True)
            return []

    async def update(self, entity_id: UUID, entity: Vehicle) -> Optional[Vehicle]:
        """Update an existing vehicle"""
        try:
            logger.info(f"🔄 Updating vehicle: {entity_id}")

            vehicle_orm = await self.session.get(VehicleORM, entity_id)
            if not vehicle_orm:
                logger.warning(f"❌ Vehicle not found: {entity_id}")
                return None

            # Update all fields
            vehicle_orm.vehicle_type = entity.vehicle_type or vehicle_orm.vehicle_type
            vehicle_orm.weight_capacity = (
                entity.weight_capacity or vehicle_orm.weight_capacity
            )
            vehicle_orm.volume_capacity = (
                entity.volume_capacity or vehicle_orm.volume_capacity
            )
            vehicle_orm.loading_cost = entity.loading_cost or vehicle_orm.loading_cost
            vehicle_orm.travel_cost_per_km = (
                entity.travel_cost_per_km or vehicle_orm.travel_cost_per_km
            )
            vehicle_orm.travel_cost_per_hour = (
                entity.travel_cost_per_hour or vehicle_orm.travel_cost_per_hour
            )
            vehicle_orm.loading_time = entity.loading_time or vehicle_orm.loading_time
            vehicle_orm.average_speed = (
                entity.average_speed or vehicle_orm.average_speed
            )
            vehicle_orm.max_duration = entity.max_duration or vehicle_orm.max_duration
            vehicle_orm.fuel_consumption_per_100_km = (
                entity.fuel_consumption_per_100_km
                or vehicle_orm.fuel_consumption_per_100_km
            )
            vehicle_orm.fuel_type = entity.fuel_type or vehicle_orm.fuel_type
            vehicle_orm.max_tasks = entity.max_tasks or vehicle_orm.max_tasks

            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Vehicle updated: {entity_id}")
            return await self._orm_to_entity(vehicle_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error updating vehicle: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a vehicle"""
        try:
            logger.info(f"🔄 Deleting vehicle: {entity_id}")

            vehicle_orm = await self.session.get(VehicleORM, entity_id)
            if not vehicle_orm:
                logger.warning(f"❌ Vehicle not found: {entity_id}")
                return False

            await self.session.delete(vehicle_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Vehicle deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error deleting vehicle: {str(e)}", exc_info=True)
            return False

    async def get_by_courier_id(self, courier_id: UUID) -> List[Vehicle]:
        """Get all vehicles by courier ID"""
        try:
            logger.info(f"🔄 Getting vehicles for courier: {courier_id}")

            query = (
                select(VehicleORM)
                .where(VehicleORM.courier_id == courier_id)
                .options(joinedload(VehicleORM.courier))
                .order_by(VehicleORM.vehicle_type)
            )
            result = await self.session.execute(query)
            vehicles_orm = result.unique().scalars().all()

            if not vehicles_orm:
                logger.debug(f"No vehicles found for courier: {courier_id}")
                return []

            logger.info(
                f"✅ Found {len(vehicles_orm)} vehicles for courier: {courier_id}"
            )
            return [await self._orm_to_entity(v) for v in vehicles_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting vehicles by courier id: {str(e)}", exc_info=True
            )
            return []

    async def get_by_vehicle_type(
        self, courier_id: UUID, vehicle_type: VehicleType
    ) -> Optional[Vehicle]:
        """Get vehicle by courier ID and vehicle type"""
        try:
            logger.info(
                f"🔄 Getting {vehicle_type.value} vehicle for courier: {courier_id}"
            )

            query = (
                select(VehicleORM)
                .where(
                    (VehicleORM.courier_id == courier_id)
                    & (VehicleORM.vehicle_type == vehicle_type)
                )
                .options(joinedload(VehicleORM.courier))
            )
            result = await self.session.execute(query)
            vehicle_orm = result.unique().scalar_one_or_none()

            if not vehicle_orm:
                logger.debug(
                    f"Vehicle type {vehicle_type.value} not found for courier: {courier_id}"
                )
                return None

            logger.info(f"✅ Found {vehicle_type.value} vehicle for courier")
            return await self._orm_to_entity(vehicle_orm)

        except Exception as e:
            logger.error(f"❌ Error getting vehicle by type: {str(e)}", exc_info=True)
            return None

    async def get_vehicles_with_capacity(
        self,
        courier_id: UUID,
        weight: float,
        volume: float,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Vehicle]:
        """Get vehicles for a courier that can handle the specified weight and volume"""
        try:
            logger.info(
                f"🔄 Getting vehicles for courier {courier_id} "
                f"with capacity: weight={weight}, volume={volume}"
            )

            query = (
                select(VehicleORM)
                .where(
                    (VehicleORM.courier_id == courier_id)
                    & (VehicleORM.weight_capacity >= weight)
                    & (VehicleORM.volume_capacity >= volume)
                )
                .options(joinedload(VehicleORM.courier))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            vehicles_orm = result.unique().scalars().all()

            if not vehicles_orm:
                logger.debug(
                    f"No vehicles found with required capacity for courier: {courier_id}"
                )
                return []

            logger.info(f"✅ Found {len(vehicles_orm)} vehicles with required capacity")
            return [await self._orm_to_entity(v) for v in vehicles_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting vehicles with capacity: {str(e)}", exc_info=True
            )
            return []

    async def get_available_vehicles(
        self, courier_id: UUID, vehicle_type: VehicleType
    ) -> List[Vehicle]:
        """Get available vehicles for a courier by type"""
        try:
            logger.info(
                f"🔄 Getting available {vehicle_type.value} vehicles for courier: {courier_id}"
            )

            vehicles = await self.get_by_courier_id(courier_id)
            available = [
                v for v in vehicles if v.vehicle_type == vehicle_type and v.max_tasks
            ]

            logger.info(f"✅ Found {len(available)} available vehicles")
            return available

        except Exception as e:
            logger.error(
                f"❌ Error getting available vehicles: {str(e)}", exc_info=True
            )
            return []

    async def _orm_to_entity(self, vehicle_orm: VehicleORM) -> Vehicle:
        """Convert ORM model to domain entity"""
        try:
            return Vehicle(
                id=vehicle_orm.id,
                courier_id=vehicle_orm.courier_id,
                vehicle_type=vehicle_orm.vehicle_type,
                weight_capacity=vehicle_orm.weight_capacity,
                volume_capacity=vehicle_orm.volume_capacity,
                loading_cost=vehicle_orm.loading_cost,
                travel_cost_per_km=vehicle_orm.travel_cost_per_km,
                travel_cost_per_hour=vehicle_orm.travel_cost_per_hour,
                loading_time=(
                    vehicle_orm.loading_time.total_seconds()
                    if vehicle_orm.loading_time
                    else 0
                ),
                average_speed=vehicle_orm.average_speed,
                max_duration=(
                    vehicle_orm.max_duration.total_seconds()
                    if vehicle_orm.max_duration
                    else 0
                ),
                fuel_consumption_per_100_km=vehicle_orm.fuel_consumption_per_100_km,
                fuel_type=vehicle_orm.fuel_type,
                max_tasks=vehicle_orm.max_tasks,
                created_at=vehicle_orm.created_at,
                updated_at=vehicle_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise
