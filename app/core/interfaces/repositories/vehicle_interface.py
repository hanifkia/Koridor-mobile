from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Vehicle, VehicleType
from app.core.interfaces.repositories._base import IRepository


class IVehicleRepository(IRepository[Vehicle]):
    """Vehicle repository interface"""

    @abstractmethod
    async def get_by_courier_id(self, courier_id: UUID) -> List[Vehicle]:
        """Get all vehicles by courier ID"""
        pass

    @abstractmethod
    async def get_by_vehicle_type(
        self, courier_id: UUID, vehicle_type: VehicleType
    ) -> Optional[Vehicle]:
        """Get vehicle by courier ID and vehicle type"""
        pass

    @abstractmethod
    async def get_vehicles_with_capacity(
        self, courier_id: UUID, weight: float, volume: float
    ) -> List[Vehicle]:
        """Get vehicles that can handle the specified capacity"""
        pass

    @abstractmethod
    async def get_available_vehicles(
        self, courier_id: UUID, vehicle_type: VehicleType
    ) -> List[Vehicle]:
        """Get available vehicles for a courier by type"""
        pass
