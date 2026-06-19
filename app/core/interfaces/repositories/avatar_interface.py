from abc import abstractmethod
from typing import Optional
from uuid import UUID

from app.core.entities import UserAvatar
from app.core.interfaces.repositories._base import IRepository


class IAvatarRepository(IRepository[UserAvatar]):
    """Avatar repository interface"""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[UserAvatar]:
        """Get avatar by user ID"""
        pass

    @abstractmethod
    async def delete_by_user_id(self, user_id: UUID) -> bool:
        """Delete avatar by user ID"""
        pass
