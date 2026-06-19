from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import PlanPrice, Currency
from app.core.interfaces.repositories._base import IRepository


class IPlanPriceRepository(IRepository[PlanPrice]):
    """Plan price repository interface"""

    @abstractmethod
    async def get_by_plan_and_currency(
        self, plan_id: UUID, currency: Currency
    ) -> Optional[PlanPrice]:
        pass

    @abstractmethod
    async def get_by_plan_id(self, plan_id: UUID) -> Optional[List[PlanPrice]]:
        pass

    @abstractmethod
    async def get_by_stripe_price_id(self, stripe_price_id: str) -> Optional[PlanPrice]:
        pass
