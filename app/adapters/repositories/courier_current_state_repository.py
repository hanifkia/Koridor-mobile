# repositories/courier_current_state_repository.py

from typing import Optional, List
from uuid import UUID
import logging
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces import ICourierCurrentStateRepository
from app.core.entities import CourierCurrentState, CourierStatesType
from app.adapters.database.models import CourierCurrentStateORM

logger = logging.getLogger(__name__)


class CourierCurrentStateRepositoryImp(ICourierCurrentStateRepository):
    """Implementation of CourierCurrentStateRepository"""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ============ CRUD OPERATIONS ============

    async def create(self, entity: CourierCurrentState) -> CourierCurrentState:
        """
        Create a new courier current state record

        Args:
            entity: CourierCurrentState entity to create

        Returns:
            Created CourierCurrentState entity

        Raises:
            Exception: If creation fails
        """
        try:
            orm_obj = CourierCurrentStateORM(
                id=entity.id,
                courier_id=entity.courier_id,
                delivered_order_ids=entity.delivered_order_ids or [],
                state=(
                    entity.state.value
                    if isinstance(entity.state, CourierStatesType)
                    else entity.state
                ),
                created_at=entity.created_at or datetime.utcnow(),
                updated_at=entity.updated_at or datetime.utcnow(),
            )

            self.session.add(orm_obj)
            await self.session.flush()

            # Commit transaction
            await self.session.commit()

            return self._orm_to_entity(orm_obj)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Error creating courier current state: {str(e)}", exc_info=True
            )
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[CourierCurrentState]:
        """
        Get courier current state by ID

        Args:
            entity_id: The state ID

        Returns:
            CourierCurrentState entity or None
        """
        stmt = select(CourierCurrentStateORM).where(
            CourierCurrentStateORM.id == entity_id
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[CourierCurrentState]:
        """
        Get all courier current states with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of CourierCurrentState entities
        """
        stmt = (
            select(CourierCurrentStateORM)
            .order_by(CourierCurrentStateORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        orm_objs = result.scalars().all()

        return [self._orm_to_entity(obj) for obj in orm_objs]

    async def update(
        self, entity_id: UUID, entity: CourierCurrentState
    ) -> Optional[CourierCurrentState]:
        """
        Update an existing courier current state

        Args:
            entity_id: The state ID to update
            entity: Updated CourierCurrentState entity

        Returns:
            Updated CourierCurrentState entity or None
        """
        stmt = (
            update(CourierCurrentStateORM)
            .where(CourierCurrentStateORM.id == entity_id)
            .values(
                state=(
                    entity.state.value
                    if isinstance(entity.state, CourierStatesType)
                    else entity.state
                ),
                delivered_order_ids=entity.delivered_order_ids or [],
                updated_at=entity.updated_at,
            )
            .returning(CourierCurrentStateORM)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        await self.session.commit()
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete a courier current state record

        Args:
            entity_id: The state ID to delete

        Returns:
            True if deleted, False otherwise
        """
        stmt = delete(CourierCurrentStateORM).where(
            CourierCurrentStateORM.id == entity_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    # ============ CUSTOM OPERATIONS ============

    async def get_by_courier_id(
        self, courier_id: UUID
    ) -> Optional[CourierCurrentState]:
        """
        Get current state by courier ID

        Args:
            courier_id: The courier ID

        Returns:
            CourierCurrentState entity or None
        """
        stmt = select(CourierCurrentStateORM).where(
            CourierCurrentStateORM.courier_id == courier_id
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def update_state(
        self, courier_id: UUID, state: CourierStatesType
    ) -> Optional[CourierCurrentState]:
        """
        Update courier's current state

        Args:
            courier_id: The courier ID
            state: New CourierStatesType state

        Returns:
            Updated CourierCurrentState entity or None
        """
        from datetime import datetime

        stmt = (
            update(CourierCurrentStateORM)
            .where(CourierCurrentStateORM.courier_id == courier_id)
            .values(
                state=state.value,
                updated_at=datetime.utcnow(),
            )
            .returning(CourierCurrentStateORM)
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        await self.session.flush()
        await self.session.commit()
        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def add_delivered_order(
        self, courier_id: UUID, order_id: UUID
    ) -> Optional[CourierCurrentState]:
        """
        Add a delivered order to the courier's delivered list

        Args:
            courier_id: The courier ID
            order_id: The order ID to add

        Returns:
            Updated CourierCurrentState entity or None
        """
        from datetime import datetime

        # Get current state
        current_state = await self.get_by_courier_id(courier_id)
        if not current_state:
            return None

        # Add order if not already in list
        if order_id not in current_state.delivered_order_ids:
            current_state.delivered_order_ids.append(order_id)

        # Update in database
        stmt = (
            update(CourierCurrentStateORM)
            .where(CourierCurrentStateORM.courier_id == courier_id)
            .values(
                delivered_order_ids=current_state.delivered_order_ids,
                updated_at=datetime.utcnow(),
            )
            .returning(CourierCurrentStateORM)
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def remove_delivered_order(
        self, courier_id: UUID, order_id: UUID
    ) -> Optional[CourierCurrentState]:
        """
        Remove an order from the courier's delivered list

        Args:
            courier_id: The courier ID
            order_id: The order ID to remove

        Returns:
            Updated CourierCurrentState entity or None
        """
        from datetime import datetime

        # Get current state
        current_state = await self.get_by_courier_id(courier_id)
        if not current_state:
            return None

        # Remove order if in list
        if order_id in current_state.delivered_order_ids:
            current_state.delivered_order_ids.remove(order_id)

        # Update in database
        stmt = (
            update(CourierCurrentStateORM)
            .where(CourierCurrentStateORM.courier_id == courier_id)
            .values(
                delivered_order_ids=current_state.delivered_order_ids,
                updated_at=datetime.utcnow(),
            )
            .returning(CourierCurrentStateORM)
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def clear_delivered_orders(
        self, courier_id: UUID
    ) -> Optional[CourierCurrentState]:
        """
        Clear all delivered orders for a courier

        Args:
            courier_id: The courier ID

        Returns:
            Updated CourierCurrentState entity or None
        """
        from datetime import datetime

        stmt = (
            update(CourierCurrentStateORM)
            .where(CourierCurrentStateORM.courier_id == courier_id)
            .values(
                delivered_order_ids=[],
                updated_at=datetime.utcnow(),
            )
            .returning(CourierCurrentStateORM)
        )
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        return self._orm_to_entity(orm_obj) if orm_obj else None

    async def get_delivered_orders(self, courier_id: UUID) -> List[UUID]:
        """
        Get all delivered order IDs for a courier

        Args:
            courier_id: The courier ID

        Returns:
            List of delivered order UUIDs
        """
        current_state = await self.get_by_courier_id(courier_id)

        if not current_state:
            return []

        return current_state.delivered_order_ids

    # ============ HELPER METHODS ============

    @staticmethod
    def _orm_to_entity(orm_obj: CourierCurrentStateORM) -> CourierCurrentState:
        """
        Convert ORM object to domain entity

        Args:
            orm_obj: CourierCurrentStateORM object

        Returns:
            CourierCurrentState entity
        """
        return CourierCurrentState(
            id=orm_obj.id,
            courier_id=orm_obj.courier_id,
            delivered_order_ids=orm_obj.delivered_order_ids or [],
            state=CourierStatesType(orm_obj.state),
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )
