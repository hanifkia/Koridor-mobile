from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Generic repository interface"""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass

    @abstractmethod
    async def update(self, entity_id: int, entity: T) -> Optional[T]:
        """Update an existing entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """Delete an entity"""
        pass
