from typing import List, Dict, Optional
import logging
from uuid import UUID

from app.core.entities import PermissionAction, RoleType
from app.core.interfaces import (
    IPermissionRepository,
    IRoleRepository,
    IUserRepository,
)

logger = logging.getLogger(__name__)


class AuthorizationServiceImp:
    """Authorization/RBAC service implementation with improved error handling"""

    def __init__(
        self,
        permission_repo: IPermissionRepository,
        role_repo: IRoleRepository,
        user_repo: IUserRepository,
    ):
        self.permission_repo = permission_repo
        self.role_repo = role_repo
        self.user_repo = user_repo

    async def check_permission(
        self, user_id: UUID, table_name: str, action: PermissionAction
    ) -> bool:
        """Check if user has permission on a resource"""
        try:
            result = await self.permission_repo.check_user_permission(
                user_id, table_name, action
            )
            if not result:
                logger.debug(
                    f"Permission denied for user {user_id} on {table_name}:{action.value}"
                )
            return result
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}", exc_info=True)
            return False

    async def check_role(self, user_id: UUID, required_roles: List[str]) -> bool:
        """Check if user has one of required roles"""
        try:
            if not required_roles:
                return True

            # Fetch user with their role
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.role:
                logger.warning(f"User {user_id} not found or has no role assigned")
                return False

            user_role = (
                user.role.name.value
                if hasattr(user.role.name, "value")
                else str(user.role.name)
            )
            has_role = user_role in required_roles

            if not has_role:
                logger.warning(
                    f"User {user_id} denied - required roles: {required_roles}, has: {user_role}"
                )
            return has_role

        except Exception as e:
            logger.error(f"Error checking role: {str(e)}", exc_info=True)
            return False

    async def get_user_permissions(self, user_id: UUID) -> Dict[str, Dict[str, bool]]:
        """Get all permissions for user organized by table name"""
        try:
            permissions = await self.permission_repo.get_user_permissions(user_id)

            organized_perms = {}
            for perm in permissions:
                organized_perms[perm.table_name] = {
                    "read": PermissionAction.READ in perm.actions,
                    "create": PermissionAction.CREATE in perm.actions,
                    "update": PermissionAction.UPDATE in perm.actions,
                    "delete": PermissionAction.DELETE in perm.actions,
                }

            logger.debug(
                f"Retrieved permissions for user {user_id}: {len(organized_perms)} resources"
            )
            return organized_perms
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}", exc_info=True)
            return {}

    async def add_permission_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """Add permission to role with validation"""
        try:
            result = await self.role_repo.add_permission_to_role(role_id, permission_id)
            if result:
                logger.info(f"Permission {permission_id} added to role {role_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding permission to role: {str(e)}", exc_info=True)
            return False

    async def remove_permission_from_role(
        self, role_id: UUID, permission_id: UUID
    ) -> bool:
        """Remove permission from role with validation"""
        try:
            result = await self.role_repo.remove_permission_from_role(
                role_id, permission_id
            )
            if result:
                logger.info(f"Permission {permission_id} removed from role {role_id}")
            return result
        except Exception as e:
            logger.error(
                f"Error removing permission from role: {str(e)}", exc_info=True
            )
            return False

    async def bulk_assign_permissions_to_role(
        self, role_id: UUID, permission_ids: List[UUID]
    ) -> Dict[UUID, bool]:
        """Bulk assign permissions to role"""
        results = {}
        for perm_id in permission_ids:
            results[perm_id] = await self.add_permission_to_role(role_id, perm_id)

        successful = sum(1 for v in results.values() if v)
        logger.info(
            f"Bulk assigned {successful}/{len(permission_ids)} permissions to role {role_id}"
        )
        return results
