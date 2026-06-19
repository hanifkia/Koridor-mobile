from typing import Optional, List
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.entities import UsageRecord
from app.core.interfaces.repositories.usage_record_interface import (
    IUsageRecordRepository,
)
from app.adapters.database.models import UsageRecordORM

logger = logging.getLogger(__name__)


class UsageRecordRepositoryImp(IUsageRecordRepository):
    """Usage record repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: UsageRecord) -> UsageRecord:
        try:
            orm = UsageRecordORM(
                id=entity.id,
                billing_customer_id=entity.billing_customer_id,
                subscription_id=entity.subscription_id,
                period_start=entity.period_start,
                period_end=entity.period_end,
                delivery_count=entity.delivery_count,
                delivery_limit=entity.limit,
                overage_count=entity.overage_count,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(
                f"Usage record created for customer: {entity.billing_customer_id}"
            )
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating usage record: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[UsageRecord]:
        try:
            orm = await self.session.get(UsageRecordORM, entity_id)
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting usage record: {str(e)}", exc_info=True)
            return None

    async def get_current_period(
        self, billing_customer_id: UUID
    ) -> Optional[UsageRecord]:
        """Get usage record where now() is between period_start and period_end"""
        try:
            now = datetime.now(timezone.utc)
            query = select(UsageRecordORM).where(
                and_(
                    UsageRecordORM.billing_customer_id == billing_customer_id,
                    # UsageRecordORM.period_start <= now,
                    # UsageRecordORM.period_end >= now,
                )
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting current period usage: {str(e)}", exc_info=True)
            return None

    async def increment_delivery_count(
        self, billing_customer_id: UUID
    ) -> Optional[UsageRecord]:
        """Increment delivery count atomically for current period"""
        try:
            usage = await self.get_current_period(billing_customer_id)
            if not usage:
                logger.warning(
                    f"No active usage record for customer: {billing_customer_id}"
                )
                return None

            orm = await self.session.get(UsageRecordORM, usage.id)
            orm.delivery_count += 1

            if orm.delivery_count > orm.delivery_limit:
                orm.overage_count = orm.delivery_count - orm.delivery_limit

            await self.session.flush()
            await self.session.commit()

            logger.info(
                f"Delivery count incremented: {orm.delivery_count}/{orm.delivery_limit} "
                f"for customer {billing_customer_id}"
            )
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error incrementing delivery count: {str(e)}", exc_info=True)
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UsageRecord]:
        try:
            query = select(UsageRecordORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting all usage records: {str(e)}")
            return []

    async def update(
        self, entity_id: UUID, entity: UsageRecord
    ) -> Optional[UsageRecord]:
        try:
            orm = await self.session.get(UsageRecordORM, entity_id)
            if not orm:
                return None
            orm.delivery_count = entity.delivery_count
            orm.overage_count = entity.overage_count
            await self.session.flush()
            await self.session.commit()
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating usage record: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(UsageRecordORM, entity_id)
            if not orm:
                return False
            await self.session.delete(orm)
            await self.session.flush()
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            return False

    @staticmethod
    def _orm_to_entity(orm: UsageRecordORM) -> UsageRecord:
        return UsageRecord(
            id=orm.id,
            billing_customer_id=orm.billing_customer_id,
            subscription_id=orm.subscription_id,
            period_start=orm.period_start,
            period_end=orm.period_end,
            delivery_count=orm.delivery_count,
            limit=orm.delivery_limit,
            overage_count=orm.overage_count,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
