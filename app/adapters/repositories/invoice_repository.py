from typing import Optional, List
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.entities import Invoice
from app.core.interfaces.repositories.invoice_interface import IInvoiceRepository
from app.adapters.database.models import InvoiceORM

logger = logging.getLogger(__name__)


class InvoiceRepositoryImp(IInvoiceRepository):
    """Invoice repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Invoice) -> Invoice:
        try:
            orm = InvoiceORM(
                id=entity.id,
                billing_customer_id=entity.billing_customer_id,
                subscription_id=entity.subscription_id,
                stripe_invoice_id=entity.stripe_invoice_id,
                amount_due=entity.amount_due,
                amount_paid=entity.amount_paid,
                currency=entity.currency,
                status=entity.status,
                invoice_pdf_url=entity.invoice_pdf_url,
                due_date=entity.due_date,
                paid_at=entity.paid_at,
            )
            self.session.add(orm)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Invoice created: {entity.stripe_invoice_id}")
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating invoice: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Invoice]:
        try:
            orm = await self.session.get(InvoiceORM, entity_id)
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting invoice: {str(e)}", exc_info=True)
            return None

    async def get_by_stripe_invoice_id(
        self, stripe_invoice_id: str
    ) -> Optional[Invoice]:
        try:
            query = select(InvoiceORM).where(
                InvoiceORM.stripe_invoice_id == stripe_invoice_id
            )
            result = await self.session.execute(query)
            orm = result.scalar_one_or_none()
            return self._orm_to_entity(orm) if orm else None
        except Exception as e:
            logger.error(f"Error getting invoice by stripe id: {str(e)}", exc_info=True)
            return None

    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Invoice]:
        try:
            query = (
                select(InvoiceORM)
                .where(InvoiceORM.billing_customer_id == billing_customer_id)
                .order_by(InvoiceORM.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting invoices by customer: {str(e)}", exc_info=True)
            return []

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        try:
            query = select(InvoiceORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            return [self._orm_to_entity(o) for o in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error getting all invoices: {str(e)}")
            return []

    async def update(self, entity_id: UUID, entity: Invoice) -> Optional[Invoice]:
        try:
            orm = await self.session.get(InvoiceORM, entity_id)
            if not orm:
                return None
            orm.amount_due = entity.amount_due
            orm.amount_paid = entity.amount_paid
            orm.status = entity.status
            orm.invoice_pdf_url = entity.invoice_pdf_url
            orm.paid_at = entity.paid_at
            await self.session.flush()
            await self.session.commit()
            return self._orm_to_entity(orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating invoice: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id: UUID) -> bool:
        try:
            orm = await self.session.get(InvoiceORM, entity_id)
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
    def _orm_to_entity(orm: InvoiceORM) -> Invoice:
        return Invoice(
            id=orm.id,
            billing_customer_id=orm.billing_customer_id,
            subscription_id=orm.subscription_id,
            stripe_invoice_id=orm.stripe_invoice_id,
            amount_due=orm.amount_due,
            amount_paid=orm.amount_paid,
            currency=orm.currency,
            status=orm.status,
            invoice_pdf_url=orm.invoice_pdf_url,
            due_date=orm.due_date,
            paid_at=orm.paid_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
