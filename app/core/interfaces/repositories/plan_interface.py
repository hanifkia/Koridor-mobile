# core/interfaces/repositories/plan_interface.py

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Plan, PlanTier
from app.core.interfaces.repositories._base import IRepository


class IPlanRepository(IRepository[Plan]):
    """Plan repository interface"""

    @abstractmethod
    async def get_by_tier(self, tier: PlanTier) -> Optional[Plan]:
        pass

    @abstractmethod
    async def get_active_plans(self) -> List[Plan]:
        pass
