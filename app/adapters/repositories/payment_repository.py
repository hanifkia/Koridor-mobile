from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.entities import Payment
from app.core.interfaces import IPaymentRepository
from app.adapters.database.models import PaymentORM

logger = logging.getLogger(__name__)


class PaymentRepositoryImp(IPaymentRepository):
    """Payment repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Payment) -> Payment:
        try:
            orm = PaymentORM(
                id=entity.id,
                billing_customer_id=entity.billing_customer_id,
                subscription_id=entity.subscription_id,
                stripe_payment_intent_id=entity.stripe_payment_intent_id,
                amount=entity.amount,
                currency=entity.currency,
                status=entity.status,
                paid_at=entity.paid_at,
                failure_reason=entity.failure_reason,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Payment created: {entity.stripe_payment_intent_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Payment]:
        try:
            orm = await self.session.get(PaymentORM, entity_id)
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}", exc_info=True)
            return None

    async def get_by_stripe_payment_intent_id(
        self, stripe_payment_intent_id: str
    ) -> Optional[Payment]:
        try:
            query = select(PaymentORM).where(
                PaymentORM.stripe_payment_intent_id == stripe_payment_intent_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting payment by stripe id: {str(e)}", exc_info=True)
            return None

    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Payment]:
        try:
            query = (
                select(PaymentORM)
                .where(PaymentORM.billing_customer_id == billing_customer_id)
                .order_by(PaymentORM.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting payments by customer: {str(e)}", exc_info=True)
            return []

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        try:
            query = select(PaymentORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting all payments: {str(e)}")
            return []

    async def update(self, entity_id: UUID, entity: Payment) -> Optional[Payment]:
        try:
            orm = await self.session.get(PaymentORM, entity_id)
            if not orm:
                return None
            orm.status = entity.status
            orm.paid_at = entity.paid_at
            orm.failure_reason = entity.failure_reason
            await self.session.flush()
            await self.session.commit()
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating payment: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(PaymentORM, entity_id)
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
    def _orm_to_entity(orm: PaymentORM) -> Payment:
        return Payment(
            id=orm.id,
            billing_customer_id=orm.billing_customer_id,
            subscription_id=orm.subscription_id,
            stripe_payment_intent_id=orm.stripe_payment_intent_id,
            amount=orm.amount,
            currency=orm.currency,
            status=orm.status,
            paid_at=orm.paid_at,
            failure_reason=orm.failure_reason,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
