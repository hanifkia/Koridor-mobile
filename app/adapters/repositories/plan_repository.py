from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.entities import Plan, PlanTier
from app.core.interfaces.repositories.plan_interface import IPlanRepository
from app.adapters.database.models import PlanORM

logger = logging.getLogger(__name__)


class PlanRepositoryImp(IPlanRepository):
    """Plan repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Plan) -> Plan:
        try:
            orm = PlanORM(
                id=entity.id,
                name=entity.name,
                tier=entity.tier,
                stripe_product_id=entity.stripe_product_id,
                monthly_delivery_limit=entity.monthly_delivery_limit,
                is_active=entity.is_active,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Plan created: {entity.name}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating plan: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Plan]:
        try:
            query = (
                select(PlanORM)
                .where(PlanORM.id == entity_id)
                .options(selectinload(PlanORM.prices))
            )
            result = await self.session.execute(query)
            orm = result.unique().scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting plan: {str(e)}", exc_info=True)
            return None

    async def get_by_tier(self, tier: PlanTier) -> Optional[Plan]:
        try:
            query = (
                select(PlanORM)
                .where(PlanORM.tier == tier, PlanORM.is_active == True)
                .options(selectinload(PlanORM.prices))
            )
            result = await self.session.execute(query)
            orm = result.unique().scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting plan by tier: {str(e)}", exc_info=True)
            return None

    async def get_active_plans(self) -> List[Plan]:
        try:
            query = (
                select(PlanORM)
                .where(PlanORM.is_active == True)
                .options(selectinload(PlanORM.prices))
            )
            result = await self.session.execute(query)
            orms = result.unique().scalars().all()
            return [self._orm_to_entity(o) for o in orms]
        except Exception as e:
            logger.error(f"Error getting active plans: {str(e)}", exc_info=True)
            return []

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Plan]:
        try:
            query = select(PlanORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            orms = result.scalars().all()
            return [self._orm_to_entity(o) for o in orms]
        except Exception as e:
            logger.error(f"Error getting all plans: {str(e)}")
            return []

    async def update(self, entity_id: UUID, entity: Plan) -> Optional[Plan]:
        try:
            orm = await self.session.get(PlanORM, entity_id)
            if not orm:
                return None
            orm.name = entity.name
            orm.monthly_delivery_limit = entity.monthly_delivery_limit
            orm.is_active = entity.is_active
            await self.session.flush()
            await self.session.commit()
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating plan: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(PlanORM, entity_id)
            if not orm:
                return False
            await self.session.delete(orm)
            await self.session.flush()
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting plan: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _orm_to_entity(orm: PlanORM) -> Plan:
        return Plan(
            id=orm.id,
            name=orm.name,
            tier=orm.tier,
            stripe_product_id=orm.stripe_product_id,
            monthly_delivery_limit=orm.monthly_delivery_limit,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
