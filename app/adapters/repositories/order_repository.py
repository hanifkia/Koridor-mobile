"""
Order repository implementation
"""

from typing import List, Optional
import logging
from uuid import UUID
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.core.entities import Order, TimeWindow, OrderStatusTypes
from app.core.interfaces import IOrderRepository
from app.adapters.database.models import OrderORM
from app.adapters.filters.order_filter import OrderFilter

logger = logging.getLogger(__name__)


class OrderRepositoryImp(IOrderRepository):
    """Order repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Order, commit: bool = True) -> Order:
        """Create a new order"""
        try:
            logger.info(f"🔄 Creating order: {entity.barcode}")

            order_orm = OrderORM(
                id=entity.id,
                terminal_id=entity.terminal_id,
                shift_id=entity.shift_id,
                courier_id=entity.courier_id,
                recipient_id=entity.recipient_id,
                name=entity.name,
                barcode=entity.barcode,
                status=entity.status,
                time_window_earliest=(
                    entity.time_window.earliest if entity.time_window else None
                ),
                time_window_latest=(
                    entity.time_window.latest if entity.time_window else None
                ),
                weight_occupation=entity.weight_occupation,
                volume_occupation=entity.volume_occupation,
                is_return=entity.is_return,
                original_delivery_date=entity.original_delivery_date,
                expected_delivery_date=entity.expected_delivery_date,
                actual_delivery_date=entity.actual_delivery_date,
            )

            self.session.add(order_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order created and committed: {entity.id}")
            else:
                logger.info(f"✅ Order created (pending commit): {entity.id}")

            return await self._orm_to_entity(order_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error creating order: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        try:
            logger.info(f"🔄 Getting order by ID: {entity_id}")

            query = (
                select(OrderORM)
                .where(OrderORM.id == entity_id)
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            order_orm = result.unique().scalar_one_or_none()

            if not order_orm:
                logger.debug(f"Order not found: {entity_id}")
                return None

            logger.info(f"✅ Order retrieved: {entity_id}")
            return await self._orm_to_entity(order_orm)

        except Exception as e:
            logger.error(f"❌ Error getting order by id: {str(e)}", exc_info=True)
            return None

    async def get_by_list_of_order_ids(self, order_ids: List[UUID]) -> List[Order]:
        logger.info(f"🔄 Getting orders by list of IDs: {order_ids}")

        query = (
            select(OrderORM)
            .where(OrderORM.id.in_(order_ids))
            .options(
                joinedload(OrderORM.hub),
                joinedload(OrderORM.shift),
                joinedload(OrderORM.courier),
                joinedload(OrderORM.recipient),
            )
        )
        result = await self.session.execute(query)
        orders_orm = result.unique().scalars().all()

        logger.info(f"✅ Retrieved {len(orders_orm)} orders")
        return [await self._orm_to_entity(o) for o in orders_orm]
        # Remove the try-except or re-raise the exception

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all orders with pagination"""
        try:
            logger.info(f"🔄 Getting all orders (skip={skip}, limit={limit})")

            query = (
                select(OrderORM)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting all orders: {str(e)}", exc_info=True)
            return []

    async def get_by_barcode(self, barcode: str) -> Optional[Order]:
        """Get order by barcode"""
        try:
            logger.info(f"🔄 Getting order by barcode: {barcode}")

            query = (
                select(OrderORM)
                .where(OrderORM.barcode == barcode)
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            order_orm = result.unique().scalar_one_or_none()

            if not order_orm:
                logger.debug(f"Order not found by barcode: {barcode}")
                return None

            logger.info(f"✅ Order found by barcode: {barcode}")
            return await self._orm_to_entity(order_orm)

        except Exception as e:
            logger.error(f"❌ Error getting order by barcode: {str(e)}", exc_info=True)
            return None

    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by courier ID"""
        try:
            logger.info(
                f"🔄 Getting orders for courier: {courier_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(OrderORM)
                .where(OrderORM.courier_id == courier_id)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for courier")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting orders by courier: {str(e)}", exc_info=True)
            return []

    async def get_by_recipient_id(
        self, recipient_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by recipient ID"""
        try:
            logger.info(
                f"🔄 Getting orders for recipient: {recipient_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(OrderORM)
                .where(OrderORM.recipient_id == recipient_id)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for recipient")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by recipient: {str(e)}", exc_info=True
            )
            return []

    async def get_by_terminal_id(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by hub ID"""
        try:
            logger.info(
                f"🔄 Getting orders for hub: {terminal_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(OrderORM)
                .where(OrderORM.terminal_id == terminal_id)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for hub")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting orders by hub: {str(e)}", exc_info=True)
            return []

    async def get_by_shift_id(
        self, shift_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by shift ID"""
        try:
            logger.info(
                f"🔄 Getting orders for shift: {shift_id} (skip={skip}, limit={limit})"
            )

            query = (
                select(OrderORM)
                .where(OrderORM.shift_id == shift_id)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for shift")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting orders by shift: {str(e)}", exc_info=True)
            return []

    async def get_by_status(
        self, status: OrderStatusTypes, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by status"""
        try:
            logger.info(f"🔄 Getting orders with status: {status.value}")

            query = (
                select(OrderORM)
                .where(OrderORM.status == status)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(
                f"✅ Retrieved {len(orders_orm)} orders with status {status.value}"
            )
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting orders by status: {str(e)}", exc_info=True)
            return []

    async def get_by_courier_and_status(
        self,
        courier_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get courier orders with specific status"""
        try:
            logger.info(
                f"🔄 Getting orders for courier {courier_id} with status {status.value}"
            )

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.courier_id == courier_id,
                        OrderORM.status == status,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by courier and status: {str(e)}",
                exc_info=True,
            )
            return []

    async def get_by_recipient_and_status(
        self,
        recipient_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get recipient orders with specific status"""
        try:
            logger.info(
                f"🔄 Getting orders for recipient {recipient_id} with status {status.value}"
            )

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.recipient_id == recipient_id,
                        OrderORM.status == status,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for recipient")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by recipient and status: {str(e)}",
                exc_info=True,
            )
            return []

    async def get_by_hub_and_status(
        self,
        terminal_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get hub orders with specific status"""
        try:
            logger.info(
                f"🔄 Getting orders for hub {terminal_id} with status {status.value}"
            )

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.terminal_id == terminal_id,
                        OrderORM.status == status,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for hub")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by hub and status: {str(e)}", exc_info=True
            )
            return []

    async def get_by_shift_and_status(
        self,
        shift_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get shift orders with specific status"""
        try:
            logger.info(
                f"🔄 Getting orders for shift {shift_id} with status {status.value}"
            )

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.shift_id == shift_id,
                        OrderORM.status == status,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders for shift")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by shift and status: {str(e)}", exc_info=True
            )
            return []

    async def update_status(
        self, order_id: UUID, status: OrderStatusTypes, commit: bool = True
    ) -> bool:
        """Update order status"""
        try:
            logger.info(f"🔄 Updating order status: {order_id} -> {status.value}")

            order_orm = await self.session.get(OrderORM, order_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {order_id}")
                return False

            order_orm.status = status
            order_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order status updated and committed: {order_id}")
            else:
                logger.info(f"✅ Order status updated (pending commit): {order_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error updating order status: {str(e)}", exc_info=True)
            raise

    async def mark_delivered(
        self, order_id: UUID, actual_delivery_date: datetime, commit: bool = True
    ) -> bool:
        """Mark order as delivered"""
        try:
            logger.info(f"🔄 Marking order as delivered: {order_id}")

            order_orm = await self.session.get(OrderORM, order_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {order_id}")
                return False

            order_orm.status = OrderStatusTypes.DELIVERED
            order_orm.actual_delivery_date = actual_delivery_date
            order_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order marked as delivered and committed: {order_id}")
            else:
                logger.info(
                    f"✅ Order marked as delivered (pending commit): {order_id}"
                )

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(
                f"❌ Error marking order as delivered: {str(e)}", exc_info=True
            )
            raise

    async def mark_returned(self, order_id: UUID, commit: bool = True) -> bool:
        """Mark order as returned"""
        try:
            logger.info(f"🔄 Marking order as returned: {order_id}")

            order_orm = await self.session.get(OrderORM, order_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {order_id}")
                return False

            order_orm.is_return = True
            order_orm.status = OrderStatusTypes.RETURNED
            order_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order marked as returned and committed: {order_id}")
            else:
                logger.info(f"✅ Order marked as returned (pending commit): {order_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error marking order as returned: {str(e)}", exc_info=True)
            raise

    async def barcode_exists(self, barcode: str) -> bool:
        """Check if barcode exists"""
        try:
            query = (
                select(func.count())
                .select_from(OrderORM)
                .where(OrderORM.barcode == barcode)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count > 0

        except Exception as e:
            logger.error(
                f"❌ Error checking barcode existence: {str(e)}", exc_info=True
            )
            return False

    async def get_pending_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all pending orders"""
        try:
            logger.info(f"🔄 Getting pending orders (skip={skip}, limit={limit})")

            query = (
                select(OrderORM)
                .where(OrderORM.status == OrderStatusTypes.PENDING)
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} pending orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting pending orders: {str(e)}", exc_info=True)
            return []

    async def get_undelivered_orders(
        self, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all undelivered orders"""
        try:
            logger.info(f"🔄 Getting undelivered orders (skip={skip}, limit={limit})")

            undelivered_statuses = [
                OrderStatusTypes.REGISTERED,
                OrderStatusTypes.PENDING,
                OrderStatusTypes.ASSIGNED,
                OrderStatusTypes.IN_TRANSIT,
            ]

            query = (
                select(OrderORM)
                .where(OrderORM.status.in_(undelivered_statuses))
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} undelivered orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting undelivered orders: {str(e)}", exc_info=True
            )
            return []

    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get orders within date range"""
        try:
            logger.info(f"🔄 Getting orders between {start_date} and {end_date}")

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.created_at >= start_date,
                        OrderORM.created_at <= end_date,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting orders by date range: {str(e)}", exc_info=True
            )
            return []

    async def get_returned_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all returned orders"""
        try:
            logger.info(f"🔄 Getting returned orders (skip={skip}, limit={limit})")

            query = (
                select(OrderORM)
                .where(
                    and_(
                        OrderORM.is_return == True,
                        OrderORM.status == OrderStatusTypes.RETURNED,
                    )
                )
                .offset(skip)
                .limit(limit)
                .order_by(OrderORM.created_at.desc())
                .options(
                    joinedload(OrderORM.hub),
                    joinedload(OrderORM.shift),
                    joinedload(OrderORM.courier),
                    joinedload(OrderORM.recipient),
                )
            )
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} returned orders")
            return [await self._orm_to_entity(o) for o in orders_orm]

        except Exception as e:
            logger.error(f"❌ Error getting returned orders: {str(e)}", exc_info=True)
            return []

    async def assign_to_courier(
        self, order_id: UUID, courier_id: UUID, shift_id: UUID, commit: bool = True
    ) -> bool:
        """Assign order to courier and shift"""
        try:
            logger.info(
                f"🔄 Assigning order {order_id} to courier {courier_id} in shift {shift_id}"
            )

            order_orm = await self.session.get(OrderORM, order_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {order_id}")
                return False

            order_orm.courier_id = courier_id
            order_orm.shift_id = shift_id
            order_orm.status = OrderStatusTypes.ASSIGNED
            order_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order assigned and committed: {order_id}")
            else:
                logger.info(f"✅ Order assigned (pending commit): {order_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error assigning order: {str(e)}", exc_info=True)
            raise

    async def bulk_update_status(
        self, order_ids: List[UUID], status: OrderStatusTypes, commit: bool = True
    ) -> int:
        """Update status for multiple orders"""
        try:
            logger.info(
                f"🔄 Bulk updating {len(order_ids)} orders to status {status.value}"
            )

            query = select(OrderORM).where(OrderORM.id.in_(order_ids))
            result = await self.session.execute(query)
            orders_orm = result.scalars().all()

            updated_count = 0
            for order_orm in orders_orm:
                order_orm.status = status
                order_orm.updated_at = datetime.utcnow()
                updated_count += 1

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Bulk updated {updated_count} orders and committed")
            else:
                logger.info(f"✅ Bulk updated {updated_count} orders (pending commit)")

            return updated_count

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error bulk updating orders: {str(e)}", exc_info=True)
            raise

    async def count_by_courier_id(self, courier_id: UUID) -> int:
        """Count orders by courier"""
        try:
            query = (
                select(func.count())
                .select_from(OrderORM)
                .where(OrderORM.courier_id == courier_id)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(
                f"❌ Error counting orders by courier: {str(e)}", exc_info=True
            )
            return 0

    async def count_by_recipient_id(self, recipient_id: UUID) -> int:
        """Count orders by recipient"""
        try:
            query = (
                select(func.count())
                .select_from(OrderORM)
                .where(OrderORM.recipient_id == recipient_id)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(
                f"❌ Error counting orders by recipient: {str(e)}", exc_info=True
            )
            return 0

    async def count_by_status(self, status: OrderStatusTypes) -> int:
        """Count orders by status"""
        try:
            query = (
                select(func.count())
                .select_from(OrderORM)
                .where(OrderORM.status == status)
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(f"❌ Error counting orders by status: {str(e)}", exc_info=True)
            return 0

    async def count_by_courier_id_and_status(
        self, courier_id: UUID, status: OrderStatusTypes
    ) -> int:
        """Count orders by courier and status"""
        try:
            query = (
                select(func.count())
                .select_from(OrderORM)
                .where(
                    and_(
                        OrderORM.courier_id == courier_id,
                        OrderORM.status == status,
                    )
                )
            )
            result = await self.session.execute(query)
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(
                f"❌ Error counting orders by courier and status: {str(e)}",
                exc_info=True,
            )
            return 0

    async def update(
        self, entity_id: UUID, entity: Order, commit: bool = True
    ) -> Optional[Order]:
        """Update an existing order"""
        try:
            logger.info(f"🔄 Updating order: {entity_id}")

            order_orm = await self.session.get(OrderORM, entity_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {entity_id}")
                return None

            # Update fields
            order_orm.name = entity.name
            order_orm.barcode = entity.barcode
            order_orm.status = entity.status
            order_orm.time_window_earliest = (
                entity.time_window.earliest if entity.time_window else None
            )
            order_orm.time_window_latest = (
                entity.time_window.latest if entity.time_window else None
            )
            order_orm.weight_occupation = entity.weight_occupation
            order_orm.volume_occupation = entity.volume_occupation
            order_orm.is_return = entity.is_return
            order_orm.original_delivery_date = entity.original_delivery_date
            order_orm.expected_delivery_date = entity.expected_delivery_date
            order_orm.actual_delivery_date = entity.actual_delivery_date
            order_orm.updated_at = datetime.utcnow()

            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order updated and committed: {entity_id}")
            else:
                logger.info(f"✅ Order updated (pending commit): {entity_id}")

            return await self._orm_to_entity(order_orm)

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error updating order: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID, commit: bool = True) -> bool:
        """Delete an order"""
        try:
            logger.info(f"🔄 Deleting order: {entity_id}")

            order_orm = await self.session.get(OrderORM, entity_id)
            if not order_orm:
                logger.warning(f"❌ Order not found: {entity_id}")
                return False

            await self.session.delete(order_orm)
            await self.session.flush()

            if commit:
                await self.session.commit()
                logger.info(f"✅ Order deleted and committed: {entity_id}")
            else:
                logger.info(f"✅ Order deleted (pending commit): {entity_id}")

            return True

        except Exception as e:
            if commit:
                await self.session.rollback()
            logger.error(f"❌ Error deleting order: {str(e)}", exc_info=True)
            raise

    # ============ HELPER METHODS ============

    async def _orm_to_entity(self, order_orm: OrderORM) -> Order:
        """Convert ORM model to domain entity"""
        try:
            logger.debug(f"🔄 Converting ORM to entity: {order_orm.id}")

            # Build time window if available
            time_window = None
            if order_orm.time_window_earliest and order_orm.time_window_latest:
                try:
                    time_window = TimeWindow(
                        earliest=order_orm.time_window_earliest,
                        latest=order_orm.time_window_latest,
                    )
                except ValueError as e:
                    logger.warning(f"⚠️  Invalid time window: {str(e)}")
                    time_window = None

            order = Order(
                id=order_orm.id,
                terminal_id=order_orm.terminal_id,
                shift_id=order_orm.shift_id,
                courier_id=order_orm.courier_id,
                recipient_id=order_orm.recipient_id,
                name=order_orm.name,
                barcode=order_orm.barcode,
                status=order_orm.status,
                time_window=time_window,
                weight_occupation=order_orm.weight_occupation,
                volume_occupation=order_orm.volume_occupation,
                is_return=order_orm.is_return,
                original_delivery_date=order_orm.original_delivery_date,
                expected_delivery_date=order_orm.expected_delivery_date,
                actual_delivery_date=order_orm.actual_delivery_date,
                created_at=order_orm.created_at,
                updated_at=order_orm.updated_at,
            )

            logger.debug(f"✅ ORM converted to entity: {order.id}")
            return order

        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise

    async def filter_orders(
        self,
        filter_params: OrderFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Order], int]:
        """
        Filter orders using advanced filter

        Args:
            filter_params: OrderFilter instance
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Tuple of (orders, total_count)
        """
        try:
            logger.info(f"🔄 Filtering orders with params: {filter_params}")

            # Build base query
            query = select(OrderORM).options(
                joinedload(OrderORM.hub),
                joinedload(OrderORM.shift),
                joinedload(OrderORM.courier),
                joinedload(OrderORM.recipient),
            )

            # Apply filter
            query = filter_params.filter(query)

            # Get total count before pagination
            count_query = select(func.count()).select_from(OrderORM)
            count_query = filter_params.filter(count_query)
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply pagination
            query = query.offset(skip).limit(limit).order_by(OrderORM.created_at.desc())

            # Execute query
            result = await self.session.execute(query)
            orders_orm = result.unique().scalars().all()

            logger.info(f"✅ Retrieved {len(orders_orm)} orders (total: {total_count})")
            orders = [await self._orm_to_entity(o) for o in orders_orm]

            return orders, total_count

        except Exception as e:
            logger.error(f"❌ Error filtering orders: {str(e)}", exc_info=True)
            return [], 0

    async def postpone_orders(
        self,
        order_ids: list[UUID],
        terminal_id: UUID,
        shift_id: UUID,
        delivery_date: date,
        commit: bool = True,
    ) -> list[Order]:
        try:
            logger.info(f"🔄 Postponing orders: {order_ids}")
            new_orders = []

            # Update orders
            for order_id in order_ids:
                order_orm = await self.session.get(OrderORM, order_id)
                if not order_orm:
                    logger.warning(f"❌ Order not found: {order_id}")
                    continue

                order_orm.status = OrderStatusTypes.POSTPONED

                new_order = OrderORM(
                    terminal_id=terminal_id,
                    shift_id=shift_id,
                    courier_id=order_orm.courier_id,
                    recipient_id=order_orm.recipient_id,
                    name=order_orm.name,
                    barcode=order_orm.barcode + str(delivery_date),
                    status=OrderStatusTypes.REGISTERED,
                    time_window_earliest=order_orm.time_window_earliest,
                    time_window_latest=order_orm.time_window_latest,
                    weight_occupation=order_orm.weight_occupation,
                    volume_occupation=order_orm.volume_occupation,
                    is_return=order_orm.is_return,
                    original_delivery_date=order_orm.original_delivery_date,
                    expected_delivery_date=delivery_date,
                    actual_delivery_date=order_orm.actual_delivery_date,
                    moved_as=order_orm.id,
                    created_at=order_orm.created_at,
                    updated_at=datetime.utcnow(),
                )
                self.session.add(new_order)
                await self.session.flush()
                new_orders.append(new_order)

            # Commit
            if commit:
                await self.session.commit()
                logger.info(f"✅ Orders postponed and committed: {order_ids}")

            # Return orders
            orders = [await self._orm_to_entity(o) for o in new_orders]
            return orders

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error postponing orders: {str(e)}", exc_info=True)
            return []
