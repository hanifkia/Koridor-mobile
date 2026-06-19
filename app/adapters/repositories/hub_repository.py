"""
Hub repository implementation
"""

from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.core.entities import Hub
from app.core.interfaces import IHubRepository
from app.adapters.database.models import HubORM, CourierORM

logger = logging.getLogger(__name__)


class HubRepositoryImp(IHubRepository):
    """Hub repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Hub) -> Hub:
        """Create a new hub"""
        try:
            hub_orm = HubORM(
                id=entity.id,
                courier_id=entity.courier_id,
                name=entity.name,
                lat=entity.lat,
                lon=entity.lon,
                address=entity.address,
                setup_time=entity.setup_time,
                service_time=entity.service_time,
                return_to_hub=entity.return_to_hub,
            )
            self.session.add(hub_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Hub created: {entity.name}")
            return await self._orm_to_entity(hub_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating hub: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Hub]:
        """Get hub by ID"""
        try:
            query = (
                select(HubORM)
                .where(HubORM.id == entity_id)
                .options(joinedload(HubORM.courier))
            )
            result = await self.session.execute(query)
            hub_orm = result.unique().scalar_one_or_none()
            if not hub_orm:
                return None
            return await self._orm_to_entity(hub_orm)
        except Exception as e:
            logger.error(f"Error getting hub by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Hub]:
        """Get all hubs with pagination"""
        try:
            query = (
                select(HubORM)
                .offset(skip)
                .limit(limit)
                .options(joinedload(HubORM.courier))
            )
            result = await self.session.execute(query)
            hubs_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(h) for h in hubs_orm]
        except Exception as e:
            logger.error(f"Error getting all hubs: {str(e)}", exc_info=True)
            return []

    async def update(self, entity_id: UUID, entity: Hub) -> Optional[Hub]:
        """Update an existing hub"""
        try:
            hub_orm = await self.session.get(HubORM, entity_id)
            if not hub_orm:
                return None

            hub_orm.name = entity.name
            hub_orm.lat = entity.lat
            hub_orm.lon = entity.lon
            hub_orm.address = entity.address
            hub_orm.setup_time = entity.setup_time
            hub_orm.service_time = entity.service_time
            hub_orm.return_to_hub = entity.return_to_hub

            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Hub updated: {entity_id}")
            return await self._orm_to_entity(hub_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating hub: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a hub"""
        try:
            hub_orm = await self.session.get(HubORM, entity_id)
            if not hub_orm:
                return False
            await self.session.delete(hub_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"Hub deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting hub: {str(e)}", exc_info=True)
            return False

    async def get_by_name(self, name: str) -> Optional[Hub]:
        """Get hub by name"""
        try:
            query = (
                select(HubORM)
                .where(HubORM.name == name)
                .options(joinedload(HubORM.courier))
            )
            result = await self.session.execute(query)
            hub_orm = result.unique().scalar_one_or_none()
            if not hub_orm:
                return None
            return await self._orm_to_entity(hub_orm)
        except Exception as e:
            logger.error(f"Error getting hub by name: {str(e)}", exc_info=True)
            return None

    async def get_nearby_hubs(
        self, lat: float, lon: float, radius_km: float
    ) -> List[Hub]:
        """Get hubs within radius of coordinates using PostGIS"""
        try:
            from sqlalchemy import text

            # Using PostGIS distance formula (simplified Euclidean for now)
            # For production, use proper PostGIS ST_Distance
            query = text(
                """
                SELECT * FROM hubs
                WHERE earth_distance(
                    ll_to_earth(:lat, :lon),
                    ll_to_earth(lat, lon)
                ) < :radius_meters
            """
            )

            result = await self.session.execute(
                query,
                {
                    "lat": lat,
                    "lon": lon,
                    "radius_meters": radius_km * 1000,
                },
            )
            hubs_orm = result.scalars().all()
            return [await self._orm_to_entity(h) for h in hubs_orm]
        except Exception as e:
            logger.warning(f"PostGIS not available, using basic distance: {str(e)}")
            # Fallback to simple distance calculation
            query = select(HubORM).options(joinedload(HubORM.courier))
            result = await self.session.execute(query)
            hubs_orm = result.unique().scalars().all()

            nearby = []
            for hub_orm in hubs_orm:
                # Haversine distance (simplified)
                import math

                dlat = math.radians(hub_orm.lat - lat)
                dlon = math.radians(hub_orm.lon - lon)
                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(math.radians(lat))
                    * math.cos(math.radians(hub_orm.lat))
                    * math.sin(dlon / 2) ** 2
                )
                c = 2 * math.asin(math.sqrt(a))
                distance_km = 6371 * c

                if distance_km <= radius_km:
                    nearby.append(await self._orm_to_entity(hub_orm))

            return nearby

    async def get_by_courier_id(self, courier_id: UUID) -> List[Hub]:
        """Get hubs by courier ID"""
        try:
            query = (
                select(HubORM)
                .where(HubORM.courier_id == courier_id)
                .options(joinedload(HubORM.courier))
            )
            result = await self.session.execute(query)
            hubs_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(h) for h in hubs_orm]
        except Exception as e:
            logger.error(f"Error getting hubs by courier id: {str(e)}", exc_info=True)
            return []

    async def _orm_to_entity(self, hub_orm: HubORM) -> Hub:
        """Convert ORM model to domain entity"""
        try:
            return Hub(
                id=hub_orm.id,
                courier_id=hub_orm.courier_id,
                name=hub_orm.name,
                lat=hub_orm.lat,
                lon=hub_orm.lon,
                address=hub_orm.address,
                setup_time=hub_orm.setup_time,
                service_time=hub_orm.service_time,
                return_to_hub=hub_orm.return_to_hub,
                created_at=hub_orm.created_at,
                updated_at=hub_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"Error converting ORM to entity: {str(e)}", exc_info=True)
            raise
