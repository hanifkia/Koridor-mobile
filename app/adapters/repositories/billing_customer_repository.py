from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.entities import BillingCustomer
from app.core.interfaces.repositories.billing_customer_interface import (
    IBillingCustomerRepository,
)
from app.adapters.database.models import BillingCustomerORM

logger = logging.getLogger(__name__)


class BillingCustomerRepositoryImp(IBillingCustomerRepository):
    """Billing customer repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: BillingCustomer) -> BillingCustomer:
        try:
            orm = BillingCustomerORM(
                id=entity.id,
                user_id=entity.user_id,
                stripe_customer_id=entity.stripe_customer_id,
                currency=entity.currency,
                billing_email=entity.billing_email,
                billing_name=entity.billing_name,
                tax_id=entity.tax_id,
                country_code=entity.country_code,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()

            logger.info(f"Billing customer created for user: {entity.user_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating billing customer: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[BillingCustomer]:
        try:
            query = select(BillingCustomerORM).where(BillingCustomerORM.id == entity_id)
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting billing customer: {str(e)}", exc_info=True)
            return None

    async def get_by_user_id(self, user_id: UUID) -> Optional[BillingCustomer]:
        try:
            query = select(BillingCustomerORM).where(
                BillingCustomerORM.user_id == user_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(
                f"Error getting billing customer by user: {str(e)}", exc_info=True
            )
            return None

    async def get_by_stripe_customer_id(
        self, stripe_customer_id: str
    ) -> Optional[BillingCustomer]:
        try:
            query = select(BillingCustomerORM).where(
                BillingCustomerORM.stripe_customer_id == stripe_customer_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(
                f"Error getting billing customer by stripe id: {str(e)}",
                exc_info=True,
            )
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[BillingCustomer]:
        try:
            query = select(BillingCustomerORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            orms = result.scalars().all()
            return [self._orm_to_entity(o) for o in orms]
        except Exception as e:
            logger.error(f"Error getting all billing customers: {str(e)}")
            return []

    async def update(
        self, entity_id: UUID, entity: BillingCustomer
    ) -> Optional[BillingCustomer]:
        try:
            orm = await self.session.get(BillingCustomerORM, entity_id)
            if not orm:
                return None

            orm.billing_email = entity.billing_email
            orm.billing_name = entity.billing_name
            orm.tax_id = entity.tax_id
            orm.country_code = entity.country_code
            orm.currency = entity.currency

            await self.session.flush()
            await self.session.commit()

            logger.info(f"Billing customer updated: {entity_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating billing customer: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(BillingCustomerORM, entity_id)
            if not orm:
                return False
            await self.session.delete(orm)
            await self.session.flush()
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting billing customer: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _orm_to_entity(orm: BillingCustomerORM) -> BillingCustomer:
        return BillingCustomer(
            id=orm.id,
            user_id=orm.user_id,
            stripe_customer_id=orm.stripe_customer_id,
            currency=orm.currency,
            billing_email=orm.billing_email,
            billing_name=orm.billing_name,
            tax_id=orm.tax_id,
            country_code=orm.country_code,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
