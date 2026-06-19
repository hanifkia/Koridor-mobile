# app/core/interfaces/services/order_service.py
"""
Order service interface
"""
from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional, Tuple

from app.core.entities import Order, OrderStatusTypes
from app.api.v1.schemas.order_schemas import (
    CreateOrderRequest,
    UpdateOrderRequest,
    PostponeOrdersRequest,
)
from app.adapters.filters.order_filter import OrderFilter


class IOrderService(ABC):
    """Order service interface"""

    @abstractmethod
    async def create_order(
        self,
        user_id: UUID,
        terminal_id: UUID,
        shift_id: UUID,
        order_request: CreateOrderRequest,
    ) -> Order:
        """Create a new order"""
        pass

    @abstractmethod
    async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    async def get_courier_orders(
        self, courier_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Order]:
        """Get all orders for a courier"""
        pass

    @abstractmethod
    async def get_unassigned_orders(self, courier_id: UUID) -> List[Order]:
        """Get unassigned orders for a courier"""
        pass

    @abstractmethod
    async def filter_orders(
        self,
        filter_params: OrderFilter,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Order], int]:
        """Filter orders with params"""
        pass

    @abstractmethod
    async def update_order(
        self,
        order_id: UUID,
        order_request: UpdateOrderRequest,
        user_id: UUID,
    ) -> Order:
        """Update an order"""
        pass

    @abstractmethod
    async def delete_order(self, order_id: UUID, user_id: UUID) -> bool:
        """Delete an order"""
        pass

    @abstractmethod
    async def postpone_orders(
        self,
        request: PostponeOrdersRequest,
        user_id: UUID,
    ) -> List[Order]:
        """Postpone multiple orders"""
        pass

    @abstractmethod
    async def mark_delivered(self, order_id: UUID) -> Order:
        """Mark order as delivered"""
        pass

    @abstractmethod
    async def mark_returned(self, order_id: UUID) -> Order:
        """Mark order as returned"""
        pass

    @abstractmethod
    async def mark_cancelled(self, order_id: UUID) -> Order:
        """Mark order as cancelled"""
        pass
