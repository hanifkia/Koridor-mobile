"""
Order repository interface
"""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.entities import Order, OrderStatusTypes
from app.core.interfaces.repositories._base import IRepository


class IOrderRepository(IRepository[Order]):
    """Order repository interface"""

    @abstractmethod
    async def get_by_barcode(self, barcode: str) -> Optional[Order]:
        """Get order by barcode"""
        pass

    @abstractmethod
    async def get_by_list_of_order_ids(self, order_ids: List[UUID]) -> List[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by courier ID with pagination"""
        pass

    @abstractmethod
    async def get_by_recipient_id(
        self, recipient_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by recipient ID with pagination"""
        pass

    @abstractmethod
    async def get_by_terminal_id(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by hub ID with pagination"""
        pass

    @abstractmethod
    async def get_by_shift_id(
        self, shift_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by shift ID with pagination"""
        pass

    @abstractmethod
    async def get_by_status(
        self, status: OrderStatusTypes, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get orders by status with pagination"""
        pass

    @abstractmethod
    async def get_by_courier_and_status(
        self,
        courier_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get courier orders with specific status"""
        pass

    @abstractmethod
    async def get_by_recipient_and_status(
        self,
        recipient_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get recipient orders with specific status"""
        pass

    @abstractmethod
    async def get_by_hub_and_status(
        self,
        terminal_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get hub orders with specific status"""
        pass

    @abstractmethod
    async def get_by_shift_and_status(
        self,
        shift_id: UUID,
        status: OrderStatusTypes,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get shift orders with specific status"""
        pass

    @abstractmethod
    async def update_status(self, order_id: UUID, status: OrderStatusTypes) -> bool:
        """Update order status"""
        pass

    @abstractmethod
    async def mark_delivered(
        self, order_id: UUID, actual_delivery_date: datetime
    ) -> bool:
        """Mark order as delivered"""
        pass

    @abstractmethod
    async def mark_returned(self, order_id: UUID) -> bool:
        """Mark order as returned"""
        pass

    @abstractmethod
    async def barcode_exists(self, barcode: str) -> bool:
        """Check if barcode exists"""
        pass

    @abstractmethod
    async def get_pending_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all pending orders"""
        pass

    @abstractmethod
    async def get_undelivered_orders(
        self, skip: int = 0, limit: int = 100
    ) -> List[Order]:
        """Get all undelivered orders"""
        pass

    @abstractmethod
    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Order]:
        """Get orders within date range"""
        pass

    @abstractmethod
    async def get_returned_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all returned orders"""
        pass

    @abstractmethod
    async def assign_to_courier(
        self, order_id: UUID, courier_id: UUID, shift_id: UUID
    ) -> bool:
        """Assign order to courier and shift"""
        pass

    @abstractmethod
    async def bulk_update_status(
        self, order_ids: List[UUID], status: OrderStatusTypes
    ) -> int:
        """Update status for multiple orders"""
        pass

    @abstractmethod
    async def count_by_courier_id(self, courier_id: UUID) -> int:
        """Count orders by courier"""
        pass

    @abstractmethod
    async def count_by_recipient_id(self, recipient_id: UUID) -> int:
        """Count orders by recipient"""
        pass

    @abstractmethod
    async def count_by_status(self, status: OrderStatusTypes) -> int:
        """Count orders by status"""
        pass

    @abstractmethod
    async def count_by_courier_id_and_status(
        self, courier_id: UUID, status: OrderStatusTypes
    ) -> int:
        """Count orders by courier and status"""
        pass

    @abstractmethod
    async def postpone_orders(self, order_ids: List[UUID]) -> List[Order]:
        """Postpone orders"""
        pass

    @abstractmethod
    async def filter_orders(self, filter_params) -> List[Order]:
        """Filter orders"""
        pass
