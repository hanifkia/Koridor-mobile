from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Invoice
from app.core.interfaces.repositories._base import IRepository


class IInvoiceRepository(IRepository[Invoice]):
    """Invoice repository interface"""

    @abstractmethod
    async def get_by_stripe_invoice_id(
        self, stripe_invoice_id: str
    ) -> Optional[Invoice]:
        pass

    @abstractmethod
    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Invoice]:
        pass
