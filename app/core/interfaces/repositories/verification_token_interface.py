from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from app.core.entities import UserVerificationToken
from app.core.interfaces.repositories._base import IRepository


class IVerificationTokenRepository(IRepository[UserVerificationToken]):
    """Interface for verification token repository"""

    @abstractmethod
    async def get_by_token(self, token: str) -> UserVerificationToken | None:
        """Get verification token by token string"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> list[UserVerificationToken] | None:
        """Get verification token by user ID"""
        pass
