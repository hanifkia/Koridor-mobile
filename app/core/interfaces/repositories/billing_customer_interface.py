from abc import abstractmethod
from typing import Optional
from uuid import UUID

from app.core.entities import BillingCustomer
from app.core.interfaces.repositories._base import IRepository


class IBillingCustomerRepository(IRepository[BillingCustomer]):
    """Billing customer repository interface"""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[BillingCustomer]:
        pass

    @abstractmethod
    async def get_by_stripe_customer_id(
        self, stripe_customer_id: str
    ) -> Optional[BillingCustomer]:
        pass
