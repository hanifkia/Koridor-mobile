from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.core.entities import Role, Permission, PermissionAction
from app.core.interfaces.repositories._base import IRepository


class IRoleRepository(IRepository[Role]):
    """Role repository interface"""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        pass

    @abstractmethod
    async def get_with_permissions(self, role_id: int) -> Optional[Role]:
        """Get role with all permissions"""
        pass

    @abstractmethod
    async def add_permission_to_role(self, role_id: int, permission_id: int) -> bool:
        """Add permission to role"""
        pass

    @abstractmethod
    async def remove_permission_from_role(
        self, role_id: int, permission_id: int
    ) -> bool:
        """Remove permission from role"""
        pass

    @abstractmethod
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Get all permissions for a role"""
        pass


class IPermissionRepository(IRepository[Permission]):
    """Permission repository interface"""

    @abstractmethod
    async def get_by_table_name(self, table_name: str) -> Optional[Permission]:
        """Get permission by table name"""
        pass

    @abstractmethod
    async def get_by_action(
        self, table_name: str, action: PermissionAction
    ) -> Optional[Permission]:
        """Get permission by table and action"""
        pass

    @abstractmethod
    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user through their role"""
        pass

    @abstractmethod
    async def check_user_permission(
        self, user_id: int, table_name: str, action: PermissionAction
    ) -> bool:
        """Check if user has specific permission"""
        pass
