# repositories/courier_current_state_repository.py

from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from app.core.entities import CourierCurrentState, CourierStatesType
from app.core.interfaces.repositories._base import IRepository


class ICourierCurrentStateRepository(IRepository[CourierCurrentState]):
    """Repository interface for CourierCurrentState entity"""

    @abstractmethod
    async def get_by_courier_id(
        self, courier_id: UUID
    ) -> Optional[CourierCurrentState]:
        """Get current state by courier ID"""
        pass

    @abstractmethod
    async def update_state(
        self, courier_id: UUID, state: CourierStatesType
    ) -> Optional[CourierCurrentState]:
        """Update courier's current state"""
        pass

    @abstractmethod
    async def add_delivered_order(
        self, courier_id: UUID, order_id: UUID
    ) -> Optional[CourierCurrentState]:
        """Add a delivered order to the courier's delivered list"""
        pass

    @abstractmethod
    async def remove_delivered_order(
        self, courier_id: UUID, order_id: UUID
    ) -> Optional[CourierCurrentState]:
        """Remove an order from the courier's delivered list"""
        pass

    @abstractmethod
    async def clear_delivered_orders(
        self, courier_id: UUID
    ) -> Optional[CourierCurrentState]:
        """Clear all delivered orders for a courier"""
        pass

    @abstractmethod
    async def get_delivered_orders(self, courier_id: UUID) -> List[UUID]:
        """Get all delivered order IDs for a courier"""
        pass
