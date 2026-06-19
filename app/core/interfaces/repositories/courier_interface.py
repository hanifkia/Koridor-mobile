from abc import ABC, abstractmethod
from typing import List

from app.core.entities import Courier
from app.core.interfaces.repositories._base import IRepository


class ICourierRepository(IRepository[Courier]):
    """Courier repository interface"""

    @abstractmethod
    async def get_by_vehicle_type(
        self, vehicle_type_id: int, skip: int = 0, limit: int = 100
    ) -> List[Courier]:
        """Get couriers by vehicle type"""
        pass

    @abstractmethod
    async def get_available_couriers(
        self, terminal_id: int, vehicle_type_id: int
    ) -> List[Courier]:
        """Get available couriers for hub and vehicle type"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Courier:
        """Get courier by user ID"""
        pass
