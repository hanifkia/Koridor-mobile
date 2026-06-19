from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.entities import PlanPrice, Currency
from app.core.interfaces.repositories.plan_price_interface import (
    IPlanPriceRepository,
)
from app.adapters.database.models import PlanPriceORM

logger = logging.getLogger(__name__)


class PlanPriceRepositoryImp(IPlanPriceRepository):
    """Plan price repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: PlanPrice) -> PlanPrice:
        try:
            orm = PlanPriceORM(
                id=entity.id,
                plan_id=entity.plan_id,
                currency=entity.currency,
                amount=entity.amount,
                stripe_price_id=entity.stripe_price_id,
                billing_interval=entity.billing_interval,
                is_active=entity.is_active,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Plan price created: {entity.stripe_price_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating plan price: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[PlanPrice]:
        try:
            orm = await self.session.get(PlanPriceORM, entity_id)
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting plan price: {str(e)}", exc_info=True)
            return None

    async def get_by_plan_and_currency(
        self, plan_id: UUID, currency: Currency
    ) -> Optional[PlanPrice]:
        try:
            query = select(PlanPriceORM).where(
                PlanPriceORM.plan_id == plan_id,
                PlanPriceORM.currency == currency,
                PlanPriceORM.is_active == True,
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(
                f"Error getting price by plan+currency: {str(e)}", exc_info=True
            )
            return None

    async def get_by_plan_id(self, plan_id: UUID) -> Optional[List[PlanPrice]]:
        try:
            query = select(PlanPriceORM).where(
                PlanPriceORM.plan_id == plan_id,
                PlanPriceORM.is_active == True,
            )
            result = await self.session.execute(query)
            orm = result.scalars().all()
            return [self._orm_to_entity(o) for o in orm] if orm else []
        except Exception as e:
            logger.error(f"Error getting price by plan id: {str(e)}", exc_info=True)
            return []

    async def get_by_stripe_price_id(self, stripe_price_id: str) -> Optional[PlanPrice]:
        try:
            query = select(PlanPriceORM).where(
                PlanPriceORM.stripe_price_id == stripe_price_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting price by stripe id: {str(e)}", exc_info=True)
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[PlanPrice]:
        try:
            query = select(PlanPriceORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting all plan prices: {str(e)}")
            return []

    async def update(self, entity_id: UUID, entity: PlanPrice) -> Optional[PlanPrice]:
        try:
            orm = await self.session.get(PlanPriceORM, entity_id)
            if not orm:
                return None
            orm.amount = entity.amount
            orm.is_active = entity.is_active
            await self.session.flush()
            await self.session.commit()
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating plan price: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(PlanPriceORM, entity_id)
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
    def _orm_to_entity(orm: PlanPriceORM) -> PlanPrice:
        return PlanPrice(
            id=orm.id,
            plan_id=orm.plan_id,
            currency=orm.currency,
            amount=orm.amount,
            stripe_price_id=orm.stripe_price_id,
            billing_interval=orm.billing_interval,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
