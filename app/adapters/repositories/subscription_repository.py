from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.entities import Subscription, SubscriptionStatus
from app.core.interfaces.repositories.subscription_interface import (
    ISubscriptionRepository,
)
from app.adapters.database.models import SubscriptionORM

logger = logging.getLogger(__name__)


class SubscriptionRepositoryImp(ISubscriptionRepository):
    """Subscription repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Subscription) -> Subscription:
        try:
            orm = SubscriptionORM(
                id=entity.id,
                billing_customer_id=entity.billing_customer_id,
                user_id=entity.user_id,
                plan_id=entity.plan_id,
                plan_price_id=entity.plan_price_id,
                stripe_subscription_id=entity.stripe_subscription_id,
                status=entity.status,
                current_period_start=entity.current_period_start,
                current_period_end=entity.current_period_end,
                cancel_at_period_end=entity.cancel_at_period_end,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Subscription created: {entity.stripe_subscription_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating subscription: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Subscription]:
        try:
            query = select(SubscriptionORM).where(SubscriptionORM.id == entity_id)
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}", exc_info=True)
            return None

    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID
    ) -> Optional[Subscription]:
        """Get active subscription for a customer"""
        try:
            query = select(SubscriptionORM).where(
                SubscriptionORM.billing_customer_id == billing_customer_id,
                SubscriptionORM.status.in_(
                    [
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING,
                        SubscriptionStatus.PAST_DUE,
                    ]
                ),
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(
                f"Error getting subscription by customer: {str(e)}", exc_info=True
            )
            return None

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        try:
            query = select(SubscriptionORM).where(
                SubscriptionORM.stripe_subscription_id == stripe_subscription_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(
                f"Error getting subscription by stripe id: {str(e)}", exc_info=True
            )
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Subscription]:
        try:
            query = select(SubscriptionORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting all subscriptions: {str(e)}")
            return []

    async def update(
        self, entity_id: UUID, entity: Subscription
    ) -> Optional[Subscription]:
        try:
            orm = await self.session.get(SubscriptionORM, entity_id)
            if not orm:
                return None

            orm.status = entity.status
            orm.current_period_start = entity.current_period_start
            orm.current_period_end = entity.current_period_end
            orm.cancel_at_period_end = entity.cancel_at_period_end
            orm.canceled_at = entity.canceled_at

            await self.session.flush()
            await self.session.commit()
            logger.info(f"Subscription updated: {entity_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(SubscriptionORM, entity_id)
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
    def _orm_to_entity(orm: SubscriptionORM) -> Subscription:
        return Subscription(
            id=orm.id,
            billing_customer_id=orm.billing_customer_id,
            plan_id=orm.plan_id,
            plan_price_id=orm.plan_price_id,
            stripe_subscription_id=orm.stripe_subscription_id,
            status=orm.status,
            current_period_start=orm.current_period_start,
            current_period_end=orm.current_period_end,
            cancel_at_period_end=orm.cancel_at_period_end,
            canceled_at=orm.canceled_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
