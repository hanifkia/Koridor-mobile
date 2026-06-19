"""
Role service implementation
"""

from typing import Optional, List
import logging
from uuid import UUID

from app.core.entities import Role, RoleType
from app.core.interfaces import (
    IRoleRepository,
    IPermissionRepository,
)

logger = logging.getLogger(__name__)


class RoleService:
    """Service for role operations"""

    def __init__(
        self,
        role_repo: IRoleRepository,
        permission_repo: IPermissionRepository,
    ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo

    async def create_role(self, name: str) -> Role:
        """
        Create a new role

        **Validation:**
        1. Check role name does not already exist
        2. Verify role name is valid RoleType (if applicable)

        **Returns:**
        - Created role entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If creation fails
        """
        logger.info(f"🔄 Creating role: {name}")

        # Check if role name exists
        existing_role = await self.role_repo.get_by_name(name)
        if existing_role:
            logger.error(f"❌ Role already exists: {name}")
            raise ValueError("Role already exists")

        logger.info(f"✅ Role name available: {name}")

        # Try to convert to RoleType enum if possible
        try:
            role_name = (
                RoleType[name.upper()] if hasattr(RoleType, name.upper()) else name
            )
            logger.info(f"✅ Role name validated: {role_name}")
        except Exception as e:
            logger.warning(f"⚠️  Could not validate role type: {str(e)}")
            role_name = name

        # Create role entity
        try:
            role = Role(name=role_name)
            created_role = await self.role_repo.create(role)
            logger.info(f"✅ Role created: {created_role.id}")

            return created_role

        except Exception as e:
            logger.error(f"❌ Error creating role: {str(e)}", exc_info=True)
            raise

    async def get_role_by_id(self, role_id: UUID) -> Role:
        """
        Get role by ID with all permissions

        **Returns:**
        - Role entity with permissions

        **Raises:**
        - ValueError: If role not found
        """
        logger.info(f"🔄 Getting role: {role_id}")

        role = await self.role_repo.get_with_permissions(role_id)
        if not role:
            logger.error(f"❌ Role not found: {role_id}")
            raise ValueError(f"Role not found: {role_id}")

        logger.info(
            f"✅ Role found: {role.name} with {len(role.permissions)} permissions"
        )
        return role

    async def get_all_roles(self, skip: int = 0, limit: int = 10) -> List[Role]:
        """
        Get all roles with pagination

        **Returns:**
        - List of role entities

        **Raises:**
        - Exception: If query fails
        """
        logger.info(f"🔄 Getting all roles (skip={skip}, limit={limit})")

        try:
            roles = await self.role_repo.get_all(skip=skip, limit=limit)
            logger.info(f"✅ Retrieved {len(roles)} roles")
            return roles

        except Exception as e:
            logger.error(f"❌ Error getting all roles: {str(e)}", exc_info=True)
            raise

    async def update_role(self, role_id: UUID, name: Optional[str] = None) -> Role:
        """
        Update role

        **Validation:**
        1. Verify role exists
        2. Check new name is not already in use (if provided)

        **Returns:**
        - Updated role entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating role: {role_id}")

        # Verify role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            logger.error(f"❌ Role not found: {role_id}")
            raise ValueError(f"Role not found: {role_id}")

        logger.info(f"✅ Role found: {role.name}")

        # Check if new name exists
        if name:
            existing = await self.role_repo.get_by_name(name)
            if existing and existing.id != role_id:
                logger.error(f"❌ Role name already exists: {name}")
                raise ValueError("Role name already exists")

            logger.info(f"✅ Role name available: {name}")
            role.name = name

        # Update role
        try:
            updated_role = await self.role_repo.update(role_id, role)
            logger.info(f"✅ Role updated: {role_id}")

            return updated_role

        except Exception as e:
            logger.error(f"❌ Error updating role: {str(e)}", exc_info=True)
            raise

    async def delete_role(self, role_id: UUID) -> bool:
        """
        Delete role

        **Validation:**
        1. Verify role exists

        **Returns:**
        - True if deleted

        **Raises:**
        - ValueError: If role not found
        - Exception: If deletion fails
        """
        logger.info(f"🔄 Deleting role: {role_id}")

        # Verify role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            logger.error(f"❌ Role not found: {role_id}")
            raise ValueError(f"Role not found: {role_id}")

        logger.info(f"✅ Role found: {role.name}")

        try:
            success = await self.role_repo.delete(role_id)
            if not success:
                logger.error(f"❌ Failed to delete role: {role_id}")
                raise ValueError(f"Failed to delete role: {role_id}")

            logger.info(f"✅ Role deleted: {role_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting role: {str(e)}", exc_info=True)
            raise

    async def add_permission_to_role(self, role_id: UUID, permission_id: UUID) -> bool:
        """
        Add permission to role

        **Validation:**
        1. Verify role exists
        2. Verify permission exists
        3. Verify permission is not already assigned to role

        **Returns:**
        - True if permission added

        **Raises:**
        - ValueError: If validation fails
        - Exception: If operation fails
        """
        logger.info(f"🔄 Adding permission {permission_id} to role {role_id}")

        # Verify role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            logger.error(f"❌ Role not found: {role_id}")
            raise ValueError(f"Role not found: {role_id}")

        logger.info(f"✅ Role found: {role.name}")

        # Verify permission exists
        permission = await self.permission_repo.get_by_id(permission_id)
        if not permission:
            logger.error(f"❌ Permission not found: {permission_id}")
            raise ValueError(f"Permission not found: {permission_id}")

        logger.info(f"✅ Permission found: {permission.name}")

        # Check if permission already assigned to role
        try:
            role_with_perms = await self.role_repo.get_with_permissions(role_id)
            if any(p.id == permission_id for p in role_with_perms.permissions):
                logger.warning(
                    f"⚠️  Permission {permission_id} already assigned to role {role_id}"
                )
                raise ValueError("Permission already assigned to this role")

            logger.info(f"✅ Permission not yet assigned to role")

        except Exception as e:
            if "already assigned" in str(e):
                raise
            logger.error(f"❌ Error checking permissions: {str(e)}", exc_info=True)
            raise

        # Add permission to role
        try:
            success = await self.role_repo.add_permission_to_role(
                role_id, permission_id
            )
            if not success:
                logger.error(f"❌ Failed to add permission to role")
                raise ValueError("Failed to add permission to role")

            logger.info(f"✅ Permission {permission_id} added to role {role_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding permission: {str(e)}", exc_info=True)
            raise

    async def remove_permission_from_role(
        self, role_id: UUID, permission_id: UUID
    ) -> bool:
        """
        Remove permission from role

        **Validation:**
        1. Verify role exists
        2. Verify permission is assigned to role

        **Returns:**
        - True if permission removed

        **Raises:**
        - ValueError: If validation fails
        - Exception: If operation fails
        """
        logger.info(f"🔄 Removing permission {permission_id} from role {role_id}")

        # Verify role exists
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            logger.error(f"❌ Role not found: {role_id}")
            raise ValueError(f"Role not found: {role_id}")

        logger.info(f"✅ Role found: {role.name}")

        # Verify permission is assigned to role
        try:
            role_with_perms = await self.role_repo.get_with_permissions(role_id)
            if not any(p.id == permission_id for p in role_with_perms.permissions):
                logger.error(
                    f"❌ Permission {permission_id} not found for role {role_id}"
                )
                raise ValueError("Permission not found for this role")

            logger.info(f"✅ Permission found in role")

        except Exception as e:
            if "not found for this role" in str(e):
                raise
            logger.error(f"❌ Error checking permissions: {str(e)}", exc_info=True)
            raise

        # Remove permission from role
        try:
            success = await self.role_repo.remove_permission_from_role(
                role_id, permission_id
            )
            if not success:
                logger.error(f"❌ Failed to remove permission from role")
                raise ValueError("Failed to remove permission from role")

            logger.info(f"✅ Permission {permission_id} removed from role {role_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error removing permission: {str(e)}", exc_info=True)
            raise
