# app/core/interfaces/repositories/route_repository_interface.py
"""
Route repository interface definition
"""

from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.core.entities import Route, RouteStatesType
from app.core.interfaces.repositories._base import IRepository


class IRouteRepository(IRepository[Route]):
    """
    Route repository interface

    Defines contract for route data access operations.
    Handles CRUD operations and route-specific queries.
    """

    @abstractmethod
    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """
        Get all routes for a specific courier

        Args:
            courier_id: Courier UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of routes assigned to courier
        """
        pass

    @abstractmethod
    async def get_by_terminal_id(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """
        Get all routes for a specific hub

        Args:
            terminal_id: Hub UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of routes associated with hub
        """
        pass

    @abstractmethod
    async def get_by_status(
        self, status: RouteStatesType, skip: int = 0, limit: int = 100
    ) -> List[Route]:
        """
        Get routes by status

        Args:
            status: RouteStatus enum value
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of routes with matching status
        """
        pass

    @abstractmethod
    async def get_active_route(self, courier_id: UUID) -> Route:
        """
        Get active route for a courier

        Args:
            courier_id: Courier UUID

        Returns:
            Single active routes
        """
        pass

    @abstractmethod
    async def get_planned_routes_by_date(
        self, courier_id: UUID, date: datetime
    ) -> List[Route]:
        """
        Get planned routes for a specific date and courier

        Args:
            courier_id: Courier UUID
            date: Date to filter by

        Returns:
            List of routes planned for that date
        """
        pass

    @abstractmethod
    async def get_by_vehicle_id(self, vehicle_id: UUID) -> List[Route]:
        """
        Get routes assigned to a specific vehicle

        Args:
            vehicle_id: Vehicle UUID

        Returns:
            List of routes assigned to vehicle
        """
        pass

    @abstractmethod
    async def delete_by_courier_id(self, courier_id: UUID) -> int:
        """
        Delete all routes for a courier

        Args:
            courier_id: Courier UUID

        Returns:
            Number of routes deleted
        """
        pass

    @abstractmethod
    async def exists(self, route_id: UUID) -> bool:
        """
        Check if route exists

        Args:
            route_id: Route UUID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def filter_routes(self, filter_params) -> List[Route]:
        """Filter routes"""
        pass

    @abstractmethod
    async def count_routes_by_courier_id(self, courier_id: UUID) -> int:
        """
        Count routes for a specific courier

        Args:
            courier_id: Courier UUID

        Returns:
            Number of routes for courier
        """
        pass

    @abstractmethod
    async def get_not_finished_routes_with_passed_shift_time(
        self, current_time: datetime.time
    ) -> List[Route]:
        """
        Get routes that are not finished but their shift time has passed

        Args:
            current_time: Current time to compare against route shift times

        Returns:
            List of routes that are still ongoing but their shift time has passed
        """
        pass
