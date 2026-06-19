from abc import abstractmethod
from typing import Optional
from uuid import UUID

from app.core.entities import UsageRecord
from app.core.interfaces.repositories._base import IRepository


class IUsageRecordRepository(IRepository[UsageRecord]):
    """Usage record repository interface"""

    @abstractmethod
    async def get_current_period(
        self, billing_customer_id: UUID
    ) -> Optional[UsageRecord]:
        """Get usage record for current billing period"""
        pass

    @abstractmethod
    async def increment_delivery_count(
        self, billing_customer_id: UUID
    ) -> Optional[UsageRecord]:
        """Increment delivery count atomically"""
        pass
