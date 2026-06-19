from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Subscription
from app.core.interfaces.repositories._base import IRepository


class ISubscriptionRepository(IRepository[Subscription]):
    """Subscription repository interface"""

    @abstractmethod
    async def get_by_billing_customer_id(
        self, billing_customer_id: UUID
    ) -> Optional[Subscription]:
        """Get active subscription for customer"""
        pass

    @abstractmethod
    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        pass
