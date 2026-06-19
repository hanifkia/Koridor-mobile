from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities import Hub
from app.core.interfaces.repositories._base import IRepository


class IHubRepository(IRepository[Hub]):
    """Hub repository interface"""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Hub]:
        """Get hub by name"""
        pass

    @abstractmethod
    async def get_nearby_hubs(
        self, lat: float, lon: float, radius_km: float
    ) -> List[Hub]:
        """Get hubs within radius of coordinates"""
        pass

    @abstractmethod
    async def get_by_courier_id(self, courier_id: int) -> List[Hub]:
        """Get hubs by courier ID"""
        pass
