from abc import ABC, abstractmethod
from typing import List, Optional


class IAuditLogRepository(ABC):
    """Audit log repository interface"""

    @abstractmethod
    async def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: int,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Log an action for audit trail"""
        pass

    @abstractmethod
    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Get audit logs for specific user"""
        pass

    @abstractmethod
    async def get_by_resource(
        self, resource_type: str, resource_id: int, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Get audit logs for specific resource"""
        pass

    @abstractmethod
    async def get_by_action(
        self, action: str, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Get audit logs by action type"""
        pass
