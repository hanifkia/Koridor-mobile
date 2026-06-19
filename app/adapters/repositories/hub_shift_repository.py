"""
Hub shift repository implementation
"""

from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.core.entities import HubShifts
from app.core.interfaces import IHubShiftRepository
from app.adapters.database.models import HubShiftORM, HubORM

logger = logging.getLogger(__name__)


class HubShiftRepositoryImp(IHubShiftRepository):
    """Hub shift repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: HubShifts) -> HubShifts:
        """Create a new hub shift"""
        try:
            logger.info(
                f"🔄 Creating hub shift for hub: {entity.terminal_id} "
                f"({entity.start_time} - {entity.finish_time})"
            )

            hub_shift_orm = HubShiftORM(
                id=entity.id,
                terminal_id=entity.terminal_id,
                start_time=entity.start_time,
                finish_time=entity.finish_time,
            )
            self.session.add(hub_shift_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Hub shift created: {entity.id}")
            return await self._orm_to_entity(hub_shift_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error creating hub shift: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[HubShifts]:
        """Get hub shift by ID"""
        try:
            query = (
                select(HubShiftORM)
                .where(HubShiftORM.id == entity_id)
                .options(joinedload(HubShiftORM.hub))
            )
            result = await self.session.execute(query)
            hub_shift_orm = result.unique().scalar_one_or_none()
            if not hub_shift_orm:
                logger.debug(f"Hub shift not found: {entity_id}")
                return None
            return await self._orm_to_entity(hub_shift_orm)
        except Exception as e:
            logger.error(f"❌ Error getting hub shift by id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[HubShifts]:
        """Get all hub shifts with pagination"""
        try:
            query = (
                select(HubShiftORM)
                .offset(skip)
                .limit(limit)
                .options(joinedload(HubShiftORM.hub))
            )
            result = await self.session.execute(query)
            hub_shifts_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(hs) for hs in hub_shifts_orm]
        except Exception as e:
            logger.error(f"❌ Error getting all hub shifts: {str(e)}", exc_info=True)
            return []

    async def update(self, entity_id: UUID, entity: HubShifts) -> Optional[HubShifts]:
        """Update an existing hub shift"""
        try:
            logger.info(f"🔄 Updating hub shift: {entity_id}")

            hub_shift_orm = await self.session.get(HubShiftORM, entity_id)
            if not hub_shift_orm:
                logger.warning(f"❌ Hub shift not found: {entity_id}")
                return None

            hub_shift_orm.start_time = entity.start_time
            hub_shift_orm.finish_time = entity.finish_time

            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Hub shift updated: {entity_id}")
            return await self._orm_to_entity(hub_shift_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error updating hub shift: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a hub shift"""
        try:
            logger.info(f"🔄 Deleting hub shift: {entity_id}")

            hub_shift_orm = await self.session.get(HubShiftORM, entity_id)
            if not hub_shift_orm:
                logger.warning(f"❌ Hub shift not found: {entity_id}")
                return False

            await self.session.delete(hub_shift_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Hub shift deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error deleting hub shift: {str(e)}", exc_info=True)
            return False

    async def get_by_terminal_id(self, terminal_id: UUID) -> List[HubShifts]:
        """Get all shifts for a specific hub"""
        try:
            logger.info(f"🔄 Getting shifts for hub: {terminal_id}")

            query = (
                select(HubShiftORM)
                .where(HubShiftORM.terminal_id == terminal_id)
                .options(joinedload(HubShiftORM.hub))
                .order_by(HubShiftORM.start_time)  # Order by start time
            )
            result = await self.session.execute(query)
            hub_shifts_orm = result.unique().scalars().all()

            if not hub_shifts_orm:
                logger.debug(f"No shifts found for hub: {terminal_id}")
                return []

            logger.info(f"✅ Found {len(hub_shifts_orm)} shifts for hub: {terminal_id}")
            return [await self._orm_to_entity(hs) for hs in hub_shifts_orm]

        except Exception as e:
            logger.error(f"❌ Error getting shifts by hub id: {str(e)}", exc_info=True)
            return []

    async def _orm_to_entity(self, hub_shift_orm: HubShiftORM) -> HubShifts:
        """Convert ORM model to domain entity"""
        try:
            return HubShifts(
                id=hub_shift_orm.id,
                terminal_id=hub_shift_orm.terminal_id,
                start_time=hub_shift_orm.start_time,
                finish_time=hub_shift_orm.finish_time,
                created_at=hub_shift_orm.created_at,
                updated_at=hub_shift_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise

    async def check_shift_overlap(
        self, terminal_id: UUID, start_time, finish_time, exclude_shift_id: UUID = None
    ) -> Optional[HubShifts]:
        """
        Check if a shift overlaps with existing shifts for the same hub
        Returns the conflicting shift if overlap exists, None otherwise
        """
        try:
            logger.info(
                f"🔍 Checking for overlaps: hub={terminal_id}, "
                f"time={start_time}-{finish_time}"
            )

            query = select(HubShiftORM).where(HubShiftORM.terminal_id == terminal_id)

            # Exclude the shift being updated (if any)
            if exclude_shift_id:
                query = query.where(HubShiftORM.id != exclude_shift_id)

            result = await self.session.execute(query)
            existing_shifts_orm = result.scalars().all()

            for shift_orm in existing_shifts_orm:
                if self._shifts_overlap(
                    start_time, finish_time, shift_orm.start_time, shift_orm.finish_time
                ):
                    logger.warning(
                        f"⚠️  Overlap detected with shift {shift_orm.id}: "
                        f"{shift_orm.start_time}-{shift_orm.finish_time}"
                    )
                    return await self._orm_to_entity(shift_orm)

            logger.info(f"✅ No overlaps detected")
            return None

        except Exception as e:
            logger.error(f"❌ Error checking shift overlap: {str(e)}", exc_info=True)
            raise

    async def get_conflicting_shifts(
        self, terminal_id: UUID, start_time, finish_time, exclude_shift_id: UUID = None
    ) -> List[HubShifts]:
        """
        Get all shifts that overlap with the given time range
        """
        try:
            logger.info(
                f"🔍 Getting conflicting shifts: hub={terminal_id}, "
                f"time={start_time}-{finish_time}"
            )

            query = select(HubShiftORM).where(HubShiftORM.terminal_id == terminal_id)

            if exclude_shift_id:
                query = query.where(HubShiftORM.id != exclude_shift_id)

            result = await self.session.execute(query)
            existing_shifts_orm = result.scalars().all()

            conflicting = []
            for shift_orm in existing_shifts_orm:
                if self._shifts_overlap(
                    start_time, finish_time, shift_orm.start_time, shift_orm.finish_time
                ):
                    conflicting.append(await self._orm_to_entity(shift_orm))

            logger.info(f"✅ Found {len(conflicting)} conflicting shifts")
            return conflicting

        except Exception as e:
            logger.error(
                f"❌ Error getting conflicting shifts: {str(e)}", exc_info=True
            )
            return []

    async def get_hub_shifts_by_date_range(
        self, terminal_id: UUID, start_time, finish_time
    ) -> List[HubShifts]:
        """
        Get all shifts within a time range for a hub
        """
        try:
            logger.info(
                f"🔍 Getting shifts in range: hub={terminal_id}, "
                f"time={start_time}-{finish_time}"
            )

            query = (
                select(HubShiftORM)
                .where(HubShiftORM.terminal_id == terminal_id)
                .order_by(HubShiftORM.start_time)
            )

            result = await self.session.execute(query)
            shifts_orm = result.scalars().all()

            # Filter shifts that overlap with the range
            in_range = [
                await self._orm_to_entity(s)
                for s in shifts_orm
                if self._shifts_overlap(
                    start_time, finish_time, s.start_time, s.finish_time
                )
            ]

            logger.info(f"✅ Found {len(in_range)} shifts in range")
            return in_range

        except Exception as e:
            logger.error(
                f"❌ Error getting shifts by date range: {str(e)}", exc_info=True
            )
            return []

    @staticmethod
    def _shifts_overlap(start1, finish1, start2, finish2) -> bool:
        """
        Check if two time ranges overlap

        Overlap occurs when:
        - start1 < finish2 AND finish1 > start2
        """
        return start1 < finish2 and finish1 > start2

    @staticmethod
    def _get_overlap_type(start1, finish1, start2, finish2) -> str:
        """
        Determine the type of overlap between two time ranges

        - "full": new shift completely overlaps existing
        - "partial_start": new shift overlaps at the start
        - "partial_end": new shift overlaps at the end
        - "contains": new shift is contained within existing
        - "contained_in": existing shift is contained within new
        """
        if start1 <= start2 and finish1 >= finish2:
            return "full"
        elif start1 > start2 and finish1 > finish2:
            return "partial_start"
        elif start1 < start2 and finish1 < finish2:
            return "partial_end"
        elif start1 > start2 and finish1 < finish2:
            return "contained_in"
        else:
            return "contains"
