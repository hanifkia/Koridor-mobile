from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Payment
from app.core.interfaces.repositories._base import IRepository


class IPaymentRepository(IRepository[Payment]):
    """Payment repository interface"""

    @abstractmethod
    async def get_by_stripe_payment_intent_id(
        self, stripe_payment_intent_id: str
    ) -> Optional[Payment]:
        pass

    @abstractmethod
    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Payment]:
        pass
