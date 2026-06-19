"""
Mission repository implementation
"""

import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.entities import Mission, MissionStatusType
from app.core.interfaces import IMissionRepository
from app.adapters.database.models import MissionORM
from app.adapters.filters.mission_filter import MissionFilter

logger = logging.getLogger(__name__)


class MissionRepositoryImp(IMissionRepository):
    """Mission repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Mission, commit: bool = True) -> Mission:
        """Create a new mission"""
        try:
            logger.info(f"🔄 Creating mission for order: {entity.order_id}")

            mission_orm = MissionORM(
                id=entity.id,
                route_id=entity.route_id,
                order_id=entity.order_id,
                terminal_id=entity.terminal_id,
                shift_id=entity.shift_id,
                courier_id=entity.courier_id,
                is_return=entity.is_return,
                latitude=entity.location.lat if entity.location else None,
                longitude=entity.location.lon if entity.location else None,
                street=entity.address.street if entity.address else None,
                city=entity.address.city if entity.address else None,
                state=entity.address.state if entity.address else None,
                country=entity.address.country if entity.address else None,
                postal_code=entity.address.postal_code if entity.address else None,
                arrival_time=entity.arrival_time,
                cumulative_duration=entity.cumulative_duration,
                cumulative_distance=entity.cumulative_distance,
                service_time=entity.service_time,
                actual_arrival_time=entity.actual_arrival_time,
                actual_cumulative_duration=entity.actual_cumulative_duration,
                actual_cumulative_distance=entity.actual_cumulative_distance,
                actual_service_time=entity.actual_service_time,
                actual_mission_start_time=entity.actual_mission_start_time,
                actual_mission_finish_time=entity.actual_mission_finish_time,
                status=entity.status if entity.status else None,
                postponed=entity.postponed if entity.postponed else None,
                position_in_route=entity.position_in_route,
                waiting_time=entity.waiting_time,
                actual_waiting_time=entity.actual_waiting_time,
                loading_scan_parcel_time=entity.loading_scan_parcel_time,
                delivery_scan_parcel_time=entity.delivery_scan_parcel_time,
                delivery_scan_parcel_barcode=entity.delivery_scan_parcel_barcode,
                courier_comment=entity.courier_comment,
            )

            self.session.add(mission_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Mission created and committed: {entity.id}")
            else:
                logger.info(f"✅ Mission created (pending commit): {entity.id}")

            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error creating mission: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Mission]:
        """Get mission by ID"""
        try:
            logger.info(f"🔄 Getting mission by ID: {entity_id}")

            query = (
                select(MissionORM)
                .where(MissionORM.id == entity_id)
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            mission_orm = result.unique().scalar_one_or_none()

            if not mission_orm:
                logger.debug(f"Mission not found: {entity_id}")
                return None

            logger.info(f"✅ Mission retrieved: {entity_id}")
            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            logger.error(f"❌ Error getting mission by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Mission]:
        """Get all missions with pagination"""
        try:
            logger.info(f"🔄 Getting all missions (skip={skip}, limit={limit})")

            query = (
                select(MissionORM)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.created_at.desc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(f"❌ Error getting all missions: {str(e)}", exc_info=True)
            return []

    async def get_by_route_id(
        self, route_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """Get all missions for a specific route"""
        try:
            logger.info(
                f"🔄 Getting missions for route: {route_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(MissionORM)
                .where(MissionORM.route_id == route_id)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.position_in_route.asc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions for route")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(f"❌ Error getting missions by route: {str(e)}", exc_info=True)
            return []

    async def get_by_order_id(self, order_id: UUID) -> Optional[Mission]:
        """Get mission by order ID (one-to-one relationship)"""
        try:
            logger.info(f"🔄 Getting mission for order: {order_id}")

            query = (
                select(MissionORM)
                .where(MissionORM.order_id == order_id)
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            mission_orm = result.unique().scalar_one_or_none()

            if not mission_orm:
                logger.debug(f"Mission not found for order: {order_id}")
                return None

            logger.info(f"✅ Mission found for order: {order_id}")
            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            logger.error(f"❌ Error getting mission by order: {str(e)}", exc_info=True)
            return None

    async def get_by_status(
        self, status: MissionStatusType, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """Get missions by status"""
        try:
            logger.info(f"🔄 Getting missions with status: {status.value}")

            query = (
                select(MissionORM)
                .where(MissionORM.status == status.value)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.created_at.desc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(
                f"✅ Retrieved {len(missions_orm)} missions with status {status.value}"
            )
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting missions by status: {str(e)}", exc_info=True
            )
            return []

    async def get_next_mission_in_route(
        self, route_id: UUID, current_sequence: int
    ) -> Optional[Mission]:
        """Get next mission in route by sequence number"""
        try:
            logger.info(
                f"🔄 Getting next mission in route {route_id} after position {current_sequence}"
            )

            query = (
                select(MissionORM)
                .where(
                    and_(
                        MissionORM.route_id == route_id,
                        MissionORM.position_in_route > current_sequence,
                    )
                )
                .order_by(MissionORM.position_in_route.asc())
                .limit(1)
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            mission_orm = result.unique().scalar_one_or_none()

            if not mission_orm:
                logger.debug(f"No next mission found in route {route_id}")
                return None

            logger.info(
                f"✅ Next mission found: {mission_orm.id} at position {mission_orm.position_in_route}"
            )
            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting next mission in route: {str(e)}", exc_info=True
            )
            return None

    async def get_mission_by_sequence(
        self, route_id: UUID, sequence_number: int
    ) -> Optional[Mission]:
        """Get mission by sequence number within route"""
        try:
            logger.info(
                f"🔄 Getting mission in route {route_id} at sequence {sequence_number}"
            )

            query = (
                select(MissionORM)
                .where(
                    and_(
                        MissionORM.route_id == route_id,
                        MissionORM.position_in_route == sequence_number,
                    )
                )
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            mission_orm = result.unique().scalar_one_or_none()

            if not mission_orm:
                logger.debug(
                    f"Mission not found at sequence {sequence_number} in route {route_id}"
                )
                return None

            logger.info(
                f"✅ Mission found at sequence {sequence_number}: {mission_orm.id}"
            )
            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting mission by sequence: {str(e)}", exc_info=True
            )
            return None

    async def count_by_route_id(self, route_id: UUID) -> int:
        """Count missions in a route"""
        try:
            query = (
                select(func.count())
                .select_from(MissionORM)
                .where(MissionORM.route_id == route_id)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count if count is not None else 0

        except Exception as e:
            logger.error(
                f"❌ Error counting missions by route: {str(e)}", exc_info=True
            )
            return 0

    async def count_by_status(self, status: MissionStatusType) -> int:
        """Count missions by status"""
        try:
            query = (
                select(func.count())
                .select_from(MissionORM)
                .where(MissionORM.status == status.value)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count if count is not None else 0

        except Exception as e:
            logger.error(
                f"❌ Error counting missions by status: {str(e)}", exc_info=True
            )
            return 0

    async def filter_missions(
        self,
        filter_params: MissionFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Mission], int]:
        """Filter missions using advanced filter"""
        try:
            logger.info(f"🔄 Filtering missions with params: {filter_params}")

            # Build base query
            query = select(MissionORM).options(
                joinedload(MissionORM.route),
                joinedload(MissionORM.order),
                joinedload(MissionORM.hub),
                joinedload(MissionORM.shift),
                joinedload(MissionORM.courier),
            )

            # Apply filter
            query = filter_params.filter(query)

            # Get total count before pagination
            count_query = select(func.count()).select_from(MissionORM)
            count_query = filter_params.filter(count_query)
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply pagination
            query = (
                query.offset(skip)
                .limit(limit)
                .order_by(MissionORM.position_in_route.asc())
            )

            # Execute query
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(
                f"✅ Retrieved {len(missions_orm)} missions (total: {total_count})"
            )
            missions = [await self._orm_to_entity(o) for o in missions_orm]

            return missions, total_count

        except Exception as e:
            logger.error(f"❌ Error filtering missions: {str(e)}", exc_info=True)
            return [], 0

    async def update(
        self, entity_id: UUID, entity: Mission, commit: bool = True
    ) -> Optional[Mission]:
        """
        Update an existing mission

        Args:
            entity_id: The mission ID to update
            entity: The mission entity with updated values
            commit: Whether to commit the transaction immediately

        Returns:
            Updated Mission entity or None if not found

        Raises:
            Exception: If update fails
        """
        try:
            logger.info(f"🔄 Updating mission: {entity_id}")

            mission_orm = await self.session.get(MissionORM, entity_id)
            if not mission_orm:
                logger.warning(f"❌ Mission not found: {entity_id}")
                return None

            # Update fields - only update if entity has non-None values
            if entity.arrival_time is not None:
                mission_orm.arrival_time = entity.arrival_time
            if entity.cumulative_duration is not None:
                mission_orm.cumulative_duration = entity.cumulative_duration
            if entity.cumulative_distance is not None:
                mission_orm.cumulative_distance = entity.cumulative_distance
            if entity.service_time is not None:
                mission_orm.service_time = entity.service_time
            if entity.actual_arrival_time is not None:
                mission_orm.actual_arrival_time = entity.actual_arrival_time
            if entity.actual_cumulative_duration is not None:
                mission_orm.actual_cumulative_duration = (
                    entity.actual_cumulative_duration
                )
            if entity.actual_cumulative_distance is not None:
                mission_orm.actual_cumulative_distance = (
                    entity.actual_cumulative_distance
                )
            if entity.actual_service_time is not None:
                mission_orm.actual_service_time = entity.actual_service_time
            if entity.actual_mission_start_time is not None:
                mission_orm.actual_mission_start_time = entity.actual_mission_start_time
            if entity.actual_mission_finish_time is not None:
                mission_orm.actual_mission_finish_time = (
                    entity.actual_mission_finish_time
                )
            if entity.status is not None:
                mission_orm.status = (
                    entity.status if type(entity.status) is str else entity.status.value
                )
            if entity.postponed is not None:
                mission_orm.postponed = str(
                    entity.postponed
                ).lower()  # Store as string in DB
            if entity.position_in_route is not None:
                mission_orm.position_in_route = entity.position_in_route
            if entity.waiting_time is not None:
                mission_orm.waiting_time = entity.waiting_time
            if entity.actual_waiting_time is not None:
                mission_orm.actual_waiting_time = entity.actual_waiting_time
            if entity.loading_scan_parcel_time is not None:
                mission_orm.loading_scan_parcel_time = entity.loading_scan_parcel_time
            if entity.delivery_scan_parcel_time is not None:
                mission_orm.delivery_scan_parcel_time = entity.delivery_scan_parcel_time
            if entity.delivery_scan_parcel_barcode is not None:
                mission_orm.delivery_scan_parcel_barcode = (
                    entity.delivery_scan_parcel_barcode
                )
            if entity.courier_comment is not None:
                mission_orm.courier_comment = entity.courier_comment

            mission_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Mission updated and committed: {entity_id}")
            else:
                logger.info(f"✅ Mission updated (pending commit): {entity_id}")

            return await self._orm_to_entity(mission_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error updating mission: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID, commit: bool = True) -> bool:
        """Delete a mission"""
        try:
            logger.info(f"🔄 Deleting mission: {entity_id}")

            mission_orm = await self.session.get(MissionORM, entity_id)
            if not mission_orm:
                logger.warning(f"❌ Mission not found: {entity_id}")
                return False

            await self.session.delete(mission_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Mission deleted and committed: {entity_id}")
            else:
                logger.info(f"✅ Mission deleted (pending commit): {entity_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error deleting mission: {str(e)}", exc_info=True)
            raise

    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """Get missions by courier ID"""
        try:
            logger.info(
                f"🔄 Getting missions for courier: {courier_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(MissionORM)
                .where(MissionORM.courier_id == courier_id)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.created_at.desc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions for courier")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting missions by courier: {str(e)}", exc_info=True
            )
            return []

    async def get_by_terminal_id(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """Get missions by hub ID"""
        try:
            logger.info(
                f"🔄 Getting missions for hub: {terminal_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(MissionORM)
                .where(MissionORM.terminal_id == terminal_id)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.created_at.desc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions for hub")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(f"❌ Error getting missions by hub: {str(e)}", exc_info=True)
            return []

    async def get_by_shift_id(
        self, shift_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """Get missions by shift ID"""
        try:
            logger.info(
                f"🔄 Getting missions for shift: {shift_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(MissionORM)
                .where(MissionORM.shift_id == shift_id)
                .offset(skip)
                .limit(limit)
                .order_by(MissionORM.created_at.desc())
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions for shift")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(f"❌ Error getting missions by shift: {str(e)}", exc_info=True)
            return []

    async def mark_delivered(
        self,
        mission_id: UUID,
        delivery_time: datetime,
        barcode: Optional[str] = None,
        commit: bool = True,
    ) -> bool:
        """Mark mission as delivered"""
        try:
            logger.info(f"🔄 Marking mission as delivered: {mission_id}")

            mission_orm = await self.session.get(MissionORM, mission_id)
            if not mission_orm:
                logger.warning(f"❌ Mission not found: {mission_id}")
                return False

            mission_orm.status = MissionStatusType.DELIVERED.value
            mission_orm.delivery_scan_parcel_time = delivery_time
            if barcode:
                mission_orm.delivery_scan_parcel_barcode = barcode
            mission_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(
                    f"✅ Mission marked as delivered and committed: {mission_id}"
                )
            else:
                logger.info(
                    f"✅ Mission marked as delivered (pending commit): {mission_id}"
                )

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(
                f"❌ Error marking mission as delivered: {str(e)}", exc_info=True
            )
            raise

    async def mark_failed(
        self, mission_id: UUID, status: MissionStatusType, commit: bool = True
    ) -> bool:
        """Mark mission as failed"""
        try:
            logger.info(
                f"🔄 Marking mission as failed: {mission_id} with status {status.value}"
            )

            mission_orm = await self.session.get(MissionORM, mission_id)
            if not mission_orm:
                logger.warning(f"❌ Mission not found: {mission_id}")
                return False

            mission_orm.status = status.value
            mission_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Mission marked as failed and committed: {mission_id}")
            else:
                logger.info(
                    f"✅ Mission marked as failed (pending commit): {mission_id}"
                )

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error marking mission as failed: {str(e)}", exc_info=True)
            raise

    async def exists(self, mission_id: UUID) -> bool:
        """Check if mission exists"""
        try:
            query = (
                select(func.count())
                .select_from(MissionORM)
                .where(MissionORM.id == mission_id)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            logger.error(
                f"❌ Error checking mission existence: {str(e)}", exc_info=True
            )
            return False

    async def delete_by_route_id(self, route_id: UUID, commit: bool = True) -> int:
        """Delete all missions for a route"""
        try:
            logger.info(f"🔄 Deleting all missions for route: {route_id}")

            query = select(MissionORM).where(MissionORM.route_id == route_id)
            result = await self.session.execute(query)
            missions_orm = result.scalars().all()

            deleted_count = 0
            for mission_orm in missions_orm:
                await self.session.delete(mission_orm)
                deleted_count += 1

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(
                    f"✅ Deleted {deleted_count} missions for route: {route_id}"
                )
            else:
                logger.info(f"✅ Deleted {deleted_count} missions (pending commit)")

            return deleted_count

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(
                f"❌ Error deleting missions by route: {str(e)}", exc_info=True
            )
            raise

    async def get_by_order_list(self, order_ids: List[UUID]) -> List[Mission]:
        """Get missions by list of order IDs"""
        try:
            logger.info(f"🔄 Getting missions by list of order IDs: {order_ids}")

            query = (
                select(MissionORM)
                .where(MissionORM.order_id.in_(order_ids))
                .options(
                    joinedload(MissionORM.route),
                    joinedload(MissionORM.order),
                    joinedload(MissionORM.hub),
                    joinedload(MissionORM.shift),
                    joinedload(MissionORM.courier),
                )
            )
            result = await self.session.execute(query)
            missions_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(missions_orm)} missions")
            return [await self._orm_to_entity(o) for o in missions_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting missions by order list: {str(e)}", exc_info=True
            )
            return []

    async def get_by_order_id_and_route_id(
        self, order_id: UUID, route_id: UUID
    ) -> Optional[MissionORM]:
        """Get mission by order ID and route ID"""
        stmt = select(MissionORM).where(
            (MissionORM.order_id == order_id) & (MissionORM.route_id == route_id)
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        if orm_obj:
            logger.info(f"✅ Mission retrieved: {orm_obj.id}")
        else:
            logger.warning(
                f"⚠️ Mission not found for order {order_id} in route {route_id}"
            )

        return await self._orm_to_entity(orm_obj) if orm_obj else None

    async def get_next_by_position(
        self, route_id: UUID, position: int
    ) -> Optional[Mission]:
        """Get next mission by position in route"""
        stmt = select(MissionORM).where(
            and_(
                MissionORM.route_id == route_id,
                MissionORM.position_in_route == position,
            )
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        return await self._orm_to_entity(orm_obj) if orm_obj else None

    async def get_total_waiting_time(self, route_id: UUID) -> int:
        """Get total waiting time for all missions in route"""
        stmt = select(func.sum(MissionORM.actual_waiting_time)).where(
            MissionORM.route_id == route_id
        )
        result = await self.session.execute(stmt)
        total = result.scalar()
        return int(total) if total else 0

    async def update_missions_status_by_route(self, route_id: UUID, status: str) -> int:
        """Update all missions status in a route"""
        from datetime import datetime

        stmt = (
            update(MissionORM)
            .where(MissionORM.route_id == route_id)
            .values(
                status=status,
                updated_at=datetime.utcnow(),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_missions_by_route_without_loading_time(self, route_id: UUID):
        stmt = select(MissionORM).where(
            and_(
                MissionORM.route_id == route_id,
                MissionORM.loading_scan_parcel_time.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_courier_id(self, courier_id: UUID) -> int:

        stmt = select(MissionORM).where(MissionORM.courier_id == courier_id)
        result = await self.session.execute(stmt)
        return result.rowcount

    # ============ HELPER METHODS ============

    async def _orm_to_entity(self, mission_orm: MissionORM) -> Mission:
        """Convert ORM model to domain entity"""
        try:
            logger.debug(f"🔄 Converting ORM to entity: {mission_orm.id}")

            # Build location if coordinates exist
            location = None
            if mission_orm.latitude is not None and mission_orm.longitude is not None:
                from app.core.entities import Coordinates

                location = Coordinates(
                    lat=mission_orm.latitude, lon=mission_orm.longitude
                )

            # Build address if address fields exist
            address = None
            if mission_orm.street or mission_orm.city:
                from app.core.entities import Address

                address = Address(
                    street=mission_orm.street,
                    city=mission_orm.city,
                    state=mission_orm.state,
                    country=mission_orm.country,
                    postal_code=mission_orm.postal_code,
                )

            # Convert status enum
            status = None
            if mission_orm.status:
                try:
                    status = MissionStatusType(mission_orm.status)
                except ValueError:
                    logger.warning(f"Invalid status value: {mission_orm.status}")
                    status = None

            # Convert postponed enum
            postponed = None
            if mission_orm.postponed:
                try:
                    from app.core.entities import MissionPostponedType

                    postponed = MissionPostponedType(mission_orm.postponed)
                except ValueError:
                    logger.warning(f"Invalid postponed value: {mission_orm.postponed}")
                    postponed = None

            mission = Mission(
                id=mission_orm.id,
                route_id=mission_orm.route_id,
                order_id=mission_orm.order_id,
                terminal_id=mission_orm.terminal_id,
                shift_id=mission_orm.shift_id,
                courier_id=mission_orm.courier_id,
                is_return=mission_orm.is_return,
                location=location,
                address=address,
                arrival_time=mission_orm.arrival_time,
                cumulative_duration=mission_orm.cumulative_duration,
                cumulative_distance=mission_orm.cumulative_distance,
                service_time=mission_orm.service_time,
                actual_arrival_time=mission_orm.actual_arrival_time,
                actual_cumulative_duration=mission_orm.actual_cumulative_duration,
                actual_cumulative_distance=mission_orm.actual_cumulative_distance,
                actual_service_time=mission_orm.actual_service_time,
                actual_mission_start_time=mission_orm.actual_mission_start_time,
                actual_mission_finish_time=mission_orm.actual_mission_finish_time,
                status=status,
                postponed=postponed,
                position_in_route=mission_orm.position_in_route,
                waiting_time=mission_orm.waiting_time,
                actual_waiting_time=mission_orm.actual_waiting_time,
                loading_scan_parcel_time=mission_orm.loading_scan_parcel_time,
                delivery_scan_parcel_time=mission_orm.delivery_scan_parcel_time,
                delivery_scan_parcel_barcode=mission_orm.delivery_scan_parcel_barcode,
                courier_comment=mission_orm.courier_comment,
                created_at=mission_orm.created_at,
                updated_at=mission_orm.updated_at,
            )

            logger.debug(f"✅ ORM converted to entity: {mission.id}")
            return mission

        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise
