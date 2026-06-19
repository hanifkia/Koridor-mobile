"""
Route repository implementation
"""

from typing import List, Optional
import logging
from uuid import UUID
from datetime import datetime, date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, text
from sqlalchemy.orm import joinedload

from app.core.entities import Route, RouteStatesType, RouteCreatedType
from app.core.interfaces import IRouteRepository
from app.adapters.database.models import RouteORM
from app.adapters.filters.route_filter import RouteFilter

logger = logging.getLogger(__name__)


class RouteRepositoryImp(IRouteRepository):
    """Route repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Route, commit: bool = True) -> Route:
        """Create a new route"""
        try:
            logger.info(f"🔄 Creating route: {entity.route_name}")

            route_orm = RouteORM(
                id=entity.id,
                terminal_id=entity.terminal_id,
                shift_id=entity.shift_id,
                courier_id=entity.courier_id,
                vehicle_id=entity.vehicle_id,
                route_name=entity.route_name,
                start_time=entity.start_time,
                finish_time=entity.finish_time,
                actual_start_time=entity.actual_start_time,
                actual_finish_time=entity.actual_finish_time,
                cost=entity.cost,
                duration=entity.duration,
                distance=entity.distance,
                status=entity.status.value,
                color=entity.color,
                current_mission_id=entity.current_mission_id,
                must_return=entity.must_return,
                number_of_missions=entity.number_of_missions,
                total_waiting_time=entity.total_waiting_time,
                total_actual_waiting_time=entity.total_actual_waiting_time,
                total_number_of_orders=entity.total_number_of_orders,
                total_number_of_stops=entity.total_number_of_stops,
                loading_time_start=entity.loading_time_start,
                arrived_at_hub_time=entity.arrived_at_hub_time,
                lock=entity.lock,
                created_type=entity.created_type.value if entity.created_type else None,
                modification_time=entity.modification_time,
                courier_score=entity.courier_score,
            )

            self.session.add(route_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Route created and committed: {entity.id}")
            else:
                logger.info(f"✅ Route created (pending commit): {entity.id}")

            return await self._orm_to_entity(route_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error creating route: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Route]:
        """Get route by ID"""
        try:
            logger.info(f"🔄 Getting route by ID: {entity_id}")

            query = (
                select(RouteORM)
                .where(RouteORM.id == entity_id)
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            route_orm = result.unique().scalar_one_or_none()

            if not route_orm:
                logger.debug(f"Route not found: {entity_id}")
                return None

            logger.info(f"✅ Route retrieved: {entity_id}")
            return await self._orm_to_entity(route_orm)

        except Exception as e:
            logger.error(f"❌ Error getting route by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Route]:
        """Get all routes with pagination"""
        try:
            logger.info(f"🔄 Getting all routes (skip={skip}, limit={limit})")

            query = (
                select(RouteORM)
                .offset(skip)
                .limit(limit)
                .order_by(RouteORM.created_at.desc())
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(routes_orm)} routes")
            return [await self._orm_to_entity(o) for o in routes_orm]

        except Exception as e:
            logger.error(f"❌ Error getting all routes: {str(e)}", exc_info=True)
            return []

    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """Get all routes for a specific courier"""
        try:
            logger.info(
                f"🔄 Getting routes for courier: {courier_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(RouteORM)
                .where(RouteORM.courier_id == courier_id)
                .offset(skip)
                .limit(limit)
                .order_by(RouteORM.created_at.desc())
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(routes_orm)} routes for courier")
            return [await self._orm_to_entity(o) for o in routes_orm]

        except Exception as e:
            logger.error(f"❌ Error getting routes by courier: {str(e)}", exc_info=True)
            return []

    async def get_by_terminal_id(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """Get all routes for a specific hub"""
        try:
            logger.info(
                f"🔄 Getting routes for hub: {terminal_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(RouteORM)
                .where(RouteORM.terminal_id == terminal_id)
                .offset(skip)
                .limit(limit)
                .order_by(RouteORM.created_at.desc())
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(routes_orm)} routes for hub")
            return [await self._orm_to_entity(o) for o in routes_orm]

        except Exception as e:
            logger.error(f"❌ Error getting routes by hub: {str(e)}", exc_info=True)
            return []

    async def get_by_status(
        self, status: RouteStatesType, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """Get routes by status"""
        try:
            logger.info(f"🔄 Getting routes with status: {status.value}")

            query = (
                select(RouteORM)
                .where(RouteORM.status == status.value)
                .offset(skip)
                .limit(limit)
                .order_by(RouteORM.created_at.desc())
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(
                f"✅ Retrieved {len(routes_orm)} routes with status {status.value}"
            )
            return [await self._orm_to_entity(o) for o in routes_orm]

        except Exception as e:
            logger.error(f"❌ Error getting routes by status: {str(e)}", exc_info=True)
            return []

    async def get_active_route(self, courier_id: UUID) -> Optional[Route]:
        """Get active route for a courier"""
        try:
            logger.info(f"🔄 Getting active route for courier: {courier_id}")

            active_statuses = [
                RouteStatesType.LOADING.value,
                RouteStatesType.ONGOING.value,
            ]

            query = (
                select(RouteORM)
                .where(
                    and_(
                        RouteORM.courier_id == courier_id,
                        RouteORM.status.in_(active_statuses),
                    )
                )
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            route_orm = result.unique().scalar_one_or_none()

            if not route_orm:
                logger.debug(f"No active route found for courier: {courier_id}")
                return None

            logger.info(f"✅ Active route found for courier: {courier_id}")
            return await self._orm_to_entity(route_orm)

        except Exception as e:
            logger.error(f"❌ Error getting active route: {str(e)}", exc_info=True)
            return None

    async def get_planned_routes_by_date(
        self, courier_id: UUID, target_date: date
    ) -> List[Route]:
        """Get planned routes for a specific date and courier"""
        try:
            logger.info(
                f"🔄 Getting planned routes for courier {courier_id} on {target_date}"
            )

            # Get routes with SCHEDULED status for the given date
            query = (
                select(RouteORM)
                .where(
                    and_(
                        RouteORM.courier_id == courier_id,
                        RouteORM.status == RouteStatesType.SCHEDULED.value,
                        func.date(RouteORM.created_at) == target_date,
                    )
                )
                .order_by(RouteORM.start_time.asc())
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(
                f"✅ Retrieved {len(routes_orm)} planned routes for courier on {target_date}"
            )
            return [await self._orm_to_entity(o) for o in routes_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting planned routes by date: {str(e)}", exc_info=True
            )
            return []

    async def get_by_vehicle_id(self, vehicle_id: UUID) -> Optional[Route]:
        """Get route assigned to a specific vehicle"""
        try:
            logger.info(f"🔄 Getting route for vehicle: {vehicle_id}")

            query = (
                select(RouteORM)
                .where(RouteORM.vehicle_id == vehicle_id)
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.shift),
                    joinedload(RouteORM.courier),
                    joinedload(RouteORM.vehicle),
                    joinedload(RouteORM.missions),
                )
            )
            result = await self.session.execute(query)
            route_orm = result.unique().scalar_one_or_none()

            if not route_orm:
                logger.debug(f"Route not found for vehicle: {vehicle_id}")
                return None

            logger.info(f"✅ Route found for vehicle: {vehicle_id}")
            return await self._orm_to_entity(route_orm)

        except Exception as e:
            logger.error(f"❌ Error getting route by vehicle: {str(e)}", exc_info=True)
            return None

    async def delete_by_courier_id(self, courier_id: UUID) -> int:
        """Delete all routes for a courier"""
        try:
            logger.info(f"🔄 Deleting all routes for courier: {courier_id}")

            query = select(RouteORM).where(RouteORM.courier_id == courier_id)
            result = await self.session.execute(query)
            routes_orm = result.scalars().all()

            deleted_count = 0
            for route_orm in routes_orm:
                await self.session.delete(route_orm)
                deleted_count += 1

            await self.session.flush()
            await self.session.commit()

            logger.info(f"✅ Deleted {deleted_count} routes for courier: {courier_id}")
            return deleted_count

        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error deleting routes by courier: {str(e)}", exc_info=True
            )
            raise

    async def exists(self, route_id: UUID) -> bool:
        """Check if route exists"""
        try:
            query = (
                select(func.count())
                .select_from(RouteORM)
                .where(RouteORM.id == route_id)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            logger.error(f"❌ Error checking route existence: {str(e)}", exc_info=True)
            return False

    async def filter_routes(
        self,
        filter_params: RouteFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Route], int]:
        """Filter routes using advanced filter"""
        try:
            logger.info(f"🔄 Filtering routes with params: {filter_params}")

            # Build base query
            query = select(RouteORM).options(
                joinedload(RouteORM.hub),
                joinedload(RouteORM.shift),
                joinedload(RouteORM.courier),
                joinedload(RouteORM.vehicle),
                joinedload(RouteORM.missions),
            )

            # Apply filter
            query = filter_params.filter(query)

            # Get total count before pagination
            count_query = select(func.count()).select_from(RouteORM)
            count_query = filter_params.filter(count_query)
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(RouteORM.created_at.desc())

            # Execute query
            result = await self.session.execute(query)
            routes_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(routes_orm)} routes (total: {total_count})")
            routes = [await self._orm_to_entity(o) for o in routes_orm]

            return routes, total_count

        except Exception as e:
            logger.error(f"❌ Error filtering routes: {str(e)}", exc_info=True)
            return [], 0

    async def update(
        self, entity_id: UUID, entity: Route, commit: bool = True
    ) -> Optional[Route]:
        """Update an existing route"""
        try:
            logger.info(f"🔄 Updating route: {entity_id}")

            route_orm = await self.session.get(RouteORM, entity_id)
            if not route_orm:
                logger.warning(f"❌ Route not found: {entity_id}")
                return None

            # Update fields
            route_orm.route_name = entity.route_name
            route_orm.start_time = entity.start_time
            route_orm.finish_time = entity.finish_time
            route_orm.actual_start_time = entity.actual_start_time
            route_orm.actual_finish_time = entity.actual_finish_time
            route_orm.cost = entity.cost
            route_orm.duration = entity.duration
            route_orm.distance = entity.distance
            route_orm.status = (
                entity.status if type(entity.status) is str else entity.status.value
            )
            route_orm.color = entity.color
            route_orm.current_mission_id = entity.current_mission_id
            route_orm.must_return = entity.must_return
            route_orm.number_of_missions = entity.number_of_missions
            route_orm.total_waiting_time = entity.total_waiting_time
            route_orm.total_actual_waiting_time = entity.total_actual_waiting_time
            route_orm.total_number_of_orders = entity.total_number_of_orders
            route_orm.total_number_of_stops = entity.total_number_of_stops
            route_orm.loading_time_start = entity.loading_time_start
            route_orm.arrived_at_hub_time = entity.arrived_at_hub_time
            route_orm.lock = entity.lock
            route_orm.created_type = (
                entity.created_type.value if entity.created_type else None
            )
            route_orm.modification_time = entity.modification_time
            route_orm.courier_score = entity.courier_score
            route_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Route updated and committed: {entity_id}")
            else:
                logger.info(f"✅ Route updated (pending commit): {entity_id}")

            return await self._orm_to_entity(route_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error updating route: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID, commit: bool = True) -> bool:
        """Delete a route"""
        try:
            logger.info(f"🔄 Deleting route: {entity_id}")

            route_orm = await self.session.get(RouteORM, entity_id)
            if not route_orm:
                logger.warning(f"❌ Route not found: {entity_id}")
                return False

            await self.session.delete(route_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Route deleted and committed: {entity_id}")
            else:
                logger.info(f"✅ Route deleted (pending commit): {entity_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error deleting route: {str(e)}", exc_info=True)
            raise

    # ============ HELPER METHODS ============

    async def _orm_to_entity(self, route_orm: RouteORM) -> Route:
        """Convert ORM model to domain entity"""
        try:
            logger.debug(f"🔄 Converting ORM to entity: {route_orm.id}")

            route = Route(
                id=route_orm.id,
                terminal_id=route_orm.terminal_id,
                shift_id=route_orm.shift_id,
                courier_id=route_orm.courier_id,
                vehicle_id=route_orm.vehicle_id,
                route_name=route_orm.route_name,
                start_time=route_orm.start_time,
                finish_time=route_orm.finish_time,
                actual_start_time=route_orm.actual_start_time,
                actual_finish_time=route_orm.actual_finish_time,
                cost=route_orm.cost,
                duration=route_orm.duration,
                distance=route_orm.distance,
                status=RouteStatesType(route_orm.status),
                color=route_orm.color,
                current_mission_id=route_orm.current_mission_id,
                must_return=route_orm.must_return,
                number_of_missions=route_orm.number_of_missions,
                total_waiting_time=route_orm.total_waiting_time,
                total_actual_waiting_time=route_orm.total_actual_waiting_time,
                total_number_of_orders=route_orm.total_number_of_orders,
                total_number_of_stops=route_orm.total_number_of_stops,
                loading_time_start=route_orm.loading_time_start,
                arrived_at_hub_time=route_orm.arrived_at_hub_time,
                lock=route_orm.lock,
                created_type=(
                    RouteCreatedType(route_orm.created_type)
                    if route_orm.created_type
                    else None
                ),
                modification_time=route_orm.modification_time,
                courier_score=route_orm.courier_score,
                created_at=route_orm.created_at,
                updated_at=route_orm.updated_at,
            )

            logger.debug(f"✅ ORM converted to entity: {route.id}")
            return route

        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise

    async def get_assigned_route(
        self,
        courier_id: UUID,
        shift_id: UUID,
    ) -> Optional[Route]:
        """Get assigned route for courier with complex conditions"""
        try:
            logger.info(
                f"🔄 Getting assigned route for courier: {courier_id}, shift: {shift_id}"
            )

            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)

            # Build query WITHOUT using RouteFilter
            query = (
                select(RouteORM)
                .where(
                    and_(
                        RouteORM.courier_id == courier_id,
                        RouteORM.shift_id == shift_id,
                        RouteORM.created_at >= today,
                        RouteORM.created_at < tomorrow,
                        or_(
                            RouteORM.status == RouteStatesType.ONGOING.value,
                            RouteORM.status.not_in(
                                [
                                    RouteStatesType.FINISHED.value,
                                    RouteStatesType.CANCELLED.value,
                                ]
                            ),
                        ),
                    )
                )
                .options(
                    joinedload(RouteORM.hub),
                    joinedload(RouteORM.missions),
                    joinedload(RouteORM.shift),
                )
                .order_by(
                    RouteORM.shift_id,  # ← Use ORM attribute instead of text()
                )
            )

            result = await self.session.execute(query)
            route_orm = result.unique().scalars().first()

            if route_orm:
                logger.info(f"✅ Assigned route found: {route_orm.id}")
                return await self._orm_to_entity(route_orm)

            logger.debug(
                f"No assigned route found for courier: {courier_id}, shift: {shift_id}"
            )
            return None

        except Exception as e:
            logger.error(f"❌ Error getting assigned route: {str(e)}", exc_info=True)
            return None

    async def count_routes_by_courier_id(self, courier_id: UUID) -> int:
        """Count total routes for a specific courier"""
        try:
            logger.info(f"🔄 Counting routes for courier: {courier_id}")

            query = select(func.count()).where(RouteORM.courier_id == courier_id)
            result = await self.session.execute(query)
            count = result.scalar() or 0

            logger.info(f"✅ Total routes for courier {courier_id}: {count}")
            return count

        except Exception as e:
            logger.error(
                f"❌ Error counting routes by courier: {str(e)}", exc_info=True
            )
            return 0

    async def get_not_finished_routes_with_passed_shift_time(
        self, current_time: time
    ) -> List[Route]:
        try:
            logger.info(f"🔄 Getting routes with passed shift time: {current_time}")

            query = select(RouteORM).where(
                and_(
                    RouteORM.finish_time < current_time,
                    RouteORM.status.not_in(
                        [
                            RouteStatesType.FINISHED.value,
                            RouteStatesType.CANCELLED.value,
                        ]
                    ),
                )
            )
            result = await self.session.execute(query)
            routes_orm = result.scalars().all()

            logger.info(f"✅ Routes with passed shift time: {len(routes_orm)}")
            return [await self._orm_to_entity(route_orm) for route_orm in routes_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting routes with passed shift time: {str(e)}",
                exc_info=True,
            )
            return []
