# app/core/interfaces/repositories/recipient_repository.py
"""
Recipient repository interface
"""
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import Recipient
from app.core.interfaces.repositories._base import IRepository


class IRecipientRepository(IRepository[Recipient]):
    """Recipient repository interface"""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[Recipient]:
        """Get recipient by ID"""
        pass

    @abstractmethod
    async def get_by_list_of_user_ids(self, user_ids: List[UUID]) -> List[Recipient]:
        """Get recipients by list of user IDs"""
        pass

    @abstractmethod
    async def get_by_ids(self, recipient_ids: List[UUID]) -> List[Recipient]:
        """Get recipients by list of recipient IDs"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Recipient]:
        """Get recipient by email"""
        pass

    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> Optional[Recipient]:
        """Get recipient by phone number"""
        pass

    @abstractmethod
    async def get_by_name(
        self, name: str, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Get recipients by name"""
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        pass

    @abstractmethod
    async def phone_exists(self, phone_number: str) -> bool:
        """Check if phone number exists"""
        pass

    @abstractmethod
    async def get_all_recipients(
        self, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Get all recipients with pagination"""
        pass

    @abstractmethod
    async def search_recipients(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> List[Recipient]:
        """Search recipients by name or email"""
        pass
