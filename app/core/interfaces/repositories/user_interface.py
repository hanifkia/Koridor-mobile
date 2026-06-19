from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.core.entities import User, UserStatus


from app.core.interfaces.repositories._base import IRepository


class IUserRepository(IRepository[User]):
    """User repository interface"""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    async def get_by_list_of_user_ids(self, user_ids: List[int]) -> List[User]:
        """Get users by list of user IDs"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        pass

    @abstractmethod
    async def get_by_role(
        self, role_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get users by role"""
        pass

    @abstractmethod
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        pass

    @abstractmethod
    async def update_status(self, user_id: int, status: UserStatus) -> Optional[User]:
        """Update user status"""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: int) -> Optional[User]:
        """Update last login timestamp"""
        pass

    @abstractmethod
    async def verify_email(self, user_id: int) -> bool:
        """Mark user email as verified"""
        pass
