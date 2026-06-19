"""
Courier repository implementation
"""

from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.core.entities import Courier, VehicleType
from app.core.interfaces import ICourierRepository
from app.adapters.database.models import CourierORM, UserORM, VehicleORM, HubORM

logger = logging.getLogger(__name__)


class CourierRepositoryImp(ICourierRepository):
    """Courier repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Courier) -> Courier:
        """Create a new courier"""
        try:
            courier_orm = CourierORM(
                id=entity.id,
                user_id=entity.user_id,
                vehicle_type=entity.vehicle_type,
                country=entity.country,
                state=entity.state,
                city=entity.city,
            )
            self.session.add(courier_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Courier created for user: {entity.user_id}")
            return await self._orm_to_entity(courier_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating courier: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Courier]:
        """Get courier by ID"""
        try:
            query = (
                select(CourierORM)
                .where(CourierORM.id == entity_id)
                .options(
                    joinedload(CourierORM.user),
                    joinedload(CourierORM.hubs),
                    joinedload(CourierORM.vehicles),
                )
            )
            result = await self.session.execute(query)
            courier_orm = result.unique().scalar_one_or_none()
            if not courier_orm:
                return None
            return await self._orm_to_entity(courier_orm)
        except Exception as e:
            logger.error(f"Error getting courier by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Courier]:
        """Get all couriers with pagination"""
        try:
            query = (
                select(CourierORM)
                .offset(skip)
                .limit(limit)
                .options(
                    joinedload(CourierORM.user),
                    joinedload(CourierORM.hubs),
                    joinedload(CourierORM.vehicles),
                )
            )
            result = await self.session.execute(query)
            couriers_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(c) for c in couriers_orm]
        except Exception as e:
            logger.error(f"Error getting all couriers: {str(e)}", exc_info=True)
            return []

    async def update(self, entity_id: UUID, entity: Courier) -> Optional[Courier]:
        """Update an existing courier"""
        try:
            courier_orm = await self.session.get(CourierORM, entity_id)
            if not courier_orm:
                return None

            courier_orm.vehicle_type = entity.vehicle_type
            courier_orm.country = entity.country
            courier_orm.state = entity.state
            courier_orm.city = entity.city

            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Courier updated: {entity_id}")
            return await self._orm_to_entity(courier_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating courier: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a courier"""
        try:
            courier_orm = await self.session.get(CourierORM, entity_id)
            if not courier_orm:
                return False
            await self.session.delete(courier_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Courier deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting courier: {str(e)}", exc_info=True)
            return False

    async def get_by_vehicle_type(
        self, vehicle_type: VehicleType, skip: int = 0, limit: int = 100
    ) -> List[Courier]:
        """Get couriers by vehicle type"""
        try:
            query = (
                select(CourierORM)
                .where(CourierORM.vehicle_type == vehicle_type)
                .offset(skip)
                .limit(limit)
                .options(
                    joinedload(CourierORM.user),
                    joinedload(CourierORM.hubs),
                    joinedload(CourierORM.vehicles),
                )
            )
            result = await self.session.execute(query)
            couriers_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(c) for c in couriers_orm]
        except Exception as e:
            logger.error(
                f"Error getting couriers by vehicle type: {str(e)}", exc_info=True
            )
            return []

    async def get_available_couriers(
        self, terminal_id: UUID, vehicle_type: VehicleType
    ) -> List[Courier]:
        """Get available couriers for hub and vehicle type"""
        try:
            query = (
                select(CourierORM)
                .where((CourierORM.vehicle_type == vehicle_type))
                .join(CourierORM.hubs)
                .where(HubORM.id == terminal_id)
                .options(
                    joinedload(CourierORM.user),
                    joinedload(CourierORM.hubs),
                    joinedload(CourierORM.vehicles),
                )
            )
            result = await self.session.execute(query)
            couriers_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(c) for c in couriers_orm]
        except Exception as e:
            logger.error(f"Error getting available couriers: {str(e)}", exc_info=True)
            return []

    async def _orm_to_entity(self, courier_orm: CourierORM) -> Courier:
        """Convert ORM model to domain entity"""
        try:
            return Courier(
                id=courier_orm.id,
                user_id=courier_orm.user_id,
                vehicle_type=courier_orm.vehicle_type,
                country=courier_orm.country,
                state=courier_orm.state,
                city=courier_orm.city,
                created_at=courier_orm.created_at,
                updated_at=courier_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"Error converting ORM to entity: {str(e)}", exc_info=True)
            raise

    async def get_by_user_id(self, user_id: UUID) -> Optional[Courier]:
        try:
            query = (
                select(CourierORM)
                .where(CourierORM.user_id == user_id)
                .options(
                    joinedload(CourierORM.user),
                    joinedload(CourierORM.hubs),
                    joinedload(CourierORM.vehicles),
                )
            )
            result = await self.session.execute(query)
            courier_orm = result.unique().scalar_one_or_none()
            if not courier_orm:
                return None
            return await self._orm_to_entity(courier_orm)
        except Exception as e:
            logger.error(f"Error getting courier by id: {str(e)}", exc_info=True)
            return None
