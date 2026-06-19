"""
Mission repository interface definition
"""

from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional

from app.core.entities import Mission, MissionStatusType
from app.core.interfaces.repositories._base import IRepository


class IMissionRepository(IRepository[Mission]):
    """
    Mission repository interface

    Defines contract for mission data access operations.
    Handles CRUD operations and mission-specific queries.
    """

    @abstractmethod
    async def get_by_route_id(
        self, route_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all missions for a specific route

        Args:
            route_id: Route UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of missions in route
        """
        pass

    @abstractmethod
    async def get_by_courier_id(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all missions for a specific courier

        Args:
            courier_id: Courier UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of missions for courier
        """
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> Optional[Mission]:
        """
        Get mission by order ID (one-to-one relationship)

        Args:
            order_id: Order UUID

        Returns:
            Mission entity or None if not found
        """
        pass

    @abstractmethod
    async def get_by_status(
        self, status: MissionStatusType, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get missions by status

        Args:
            status: MissionStatus enum value
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of missions with matching status
        """
        pass

    @abstractmethod
    async def get_next_mission_in_route(
        self, route_id: UUID, current_sequence: int
    ) -> Optional[Mission]:
        """
        Get next mission in route by sequence number

        Args:
            route_id: Route UUID
            current_sequence: Current mission sequence number

        Returns:
            Next mission in sequence or None
        """
        pass

    @abstractmethod
    async def get_mission_by_sequence(
        self, route_id: UUID, sequence_number: int
    ) -> Optional[Mission]:
        """
        Get mission by sequence number within route

        Args:
            route_id: Route UUID
            sequence_number: Sequence number (1-indexed)

        Returns:
            Mission with matching sequence or None
        """
        pass

    @abstractmethod
    async def count_by_route_id(self, route_id: UUID) -> int:
        """
        Count missions in a route

        Args:
            route_id: Route UUID

        Returns:
            Number of missions in route
        """
        pass

    @abstractmethod
    async def count_by_status(self, status: MissionStatusType) -> int:
        """
        Count missions by status

        Args:
            status: MissionStatus enum value

        Returns:
            Number of missions with that status
        """
        pass

    @abstractmethod
    async def filter_missions(self, filter_params) -> List[Mission]:
        """Filter missions"""
        pass

    @abstractmethod
    async def get_by_order_id_and_route_id(
        self, order_id: UUID, route_id: UUID
    ) -> Optional[Mission]:
        """Get order by ID and route ID"""
        pass

    @abstractmethod
    async def get_next_by_position(
        self, route_id: UUID, position: int
    ) -> Optional[Mission]:
        """Get next mission by position in route"""
        pass

    @abstractmethod
    async def get_total_waiting_time(self, route_id: UUID) -> int:
        """Get total waiting time for all missions in route"""
        pass

    @abstractmethod
    async def update_missions_status_by_route(self, route_id: UUID, status: str) -> int:
        """Update all missions status in a route"""
        pass

    @abstractmethod
    async def count_by_courier_id(self, courier_id: UUID) -> int:
        """Count missions for a specific courier"""
        pass
