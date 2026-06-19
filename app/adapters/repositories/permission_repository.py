from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.core.entities import Permission, PermissionAction
from app.core.interfaces import IPermissionRepository
from app.adapters.database.models import (
    PermissionORM,
    PermissionRoleORM,
    UserORM,
    RoleORM,
)

logger = logging.getLogger(__name__)


class PermissionRepositoryImp(IPermissionRepository):
    """Permission repository SQLAlchemy implementation - Fixed for ARRAY actions"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Permission) -> Permission:
        """Create a new permission"""
        try:
            # Convert PermissionAction list to string values
            action_values = [action.value for action in entity.actions]

            permission_orm = PermissionORM(
                id=entity.id,
                table_name=entity.table_name,
                actions=action_values,
            )
            self.session.add(permission_orm)
            await self.session.flush()
            logger.info(f"Permission created: {entity.table_name}")
            return await self._orm_to_entity(permission_orm)
        except Exception as e:
            logger.error(f"Error creating permission: {str(e)}")
            raise

    async def get_by_id(self, entity_id) -> Optional[Permission]:
        """Get permission by ID"""
        try:
            query = select(PermissionORM).where(PermissionORM.id == entity_id)
            result = await self.session.execute(query)
            permission_orm = result.scalar_one_or_none()
            if not permission_orm:
                return None
            return await self._orm_to_entity(permission_orm)
        except Exception as e:
            logger.error(f"Error getting permission by id: {str(e)}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Get all permissions with pagination"""
        try:
            query = select(PermissionORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            permissions_orm = result.scalars().all()
            return [await self._orm_to_entity(p) for p in permissions_orm]
        except Exception as e:
            logger.error(f"Error getting all permissions: {str(e)}")
            return []

    async def update(self, entity_id, entity: Permission) -> Optional[Permission]:
        """Update an existing permission"""
        try:
            permission_orm = await self.session.get(PermissionORM, entity_id)
            if not permission_orm:
                return None

            permission_orm.table_name = entity.table_name
            permission_orm.actions = [action.value for action in entity.actions]

            await self.session.flush()
            logger.info(f"Permission updated: {entity_id}")
            return await self._orm_to_entity(permission_orm)
        except Exception as e:
            logger.error(f"Error updating permission: {str(e)}")
            raise

    async def delete(self, entity_id) -> bool:
        """Delete a permission"""
        try:
            permission_orm = await self.session.get(PermissionORM, entity_id)
            if not permission_orm:
                return False
            await self.session.delete(permission_orm)
            await self.session.flush()
            logger.info(f"Permission deleted: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting permission: {str(e)}")
            return False

    async def get_by_table_name(self, table_name: str) -> Optional[Permission]:
        """Get permission by table name"""
        try:
            query = select(PermissionORM).where(PermissionORM.table_name == table_name)
            result = await self.session.execute(query)
            permission_orm = result.scalar_one_or_none()
            if not permission_orm:
                return None
            return await self._orm_to_entity(permission_orm)
        except Exception as e:
            logger.error(f"Error getting permission by table name: {str(e)}")
            return None

    async def get_by_action(
        self, table_name: str, action: PermissionAction
    ) -> Optional[Permission]:
        """Get permission by table and action"""
        try:
            query = select(PermissionORM).where(
                and_(
                    PermissionORM.table_name == table_name,
                    PermissionORM.actions.contains(
                        [action.value]
                    ),  # PostgreSQL array contains
                )
            )
            result = await self.session.execute(query)
            permission_orm = result.scalar_one_or_none()
            if not permission_orm:
                return None
            return await self._orm_to_entity(permission_orm)
        except Exception as e:
            logger.error(f"Error getting permission by action: {str(e)}")
            return None

    async def get_user_permissions(self, user_id) -> List[Permission]:
        """Get all permissions for a user through their role"""
        try:
            query = (
                select(PermissionORM)
                .distinct()
                .join(
                    PermissionRoleORM,
                    PermissionRoleORM.permission_id == PermissionORM.id,
                )
                .join(RoleORM, RoleORM.id == PermissionRoleORM.role_id)
                .join(UserORM, UserORM.role_id == RoleORM.id)
                .where(UserORM.id == user_id)
            )
            result = await self.session.execute(query)
            permissions_orm = result.scalars().all()
            return [await self._orm_to_entity(p) for p in permissions_orm]
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return []

    async def check_user_permission(
        self, user_id, table_name: str, action: PermissionAction
    ) -> bool:
        """Check if user has specific permission"""
        try:
            query = (
                select(PermissionORM)
                .distinct()
                .join(
                    PermissionRoleORM,
                    PermissionRoleORM.permission_id == PermissionORM.id,
                )
                .join(RoleORM, RoleORM.id == PermissionRoleORM.role_id)
                .join(UserORM, UserORM.role_id == RoleORM.id)
                .where(
                    and_(
                        UserORM.id == user_id,
                        PermissionORM.table_name == table_name,
                        PermissionORM.actions.contains([action.value]),
                    )
                )
            )
            result = await self.session.execute(query)
            permission = result.scalar_one_or_none()
            has_access = permission is not None

            if not has_access:
                logger.debug(
                    f"Permission denied: user={user_id}, table={table_name}, action={action.value}"
                )

            return has_access
        except Exception as e:
            logger.error(f"Error checking user permission: {str(e)}")
            return False

    async def _orm_to_entity(self, permission_orm: PermissionORM) -> Permission:
        """Convert ORM model to domain entity"""
        try:
            actions = [
                PermissionAction(action) for action in (permission_orm.actions or [])
            ]
            return Permission(
                id=permission_orm.id,
                table_name=permission_orm.table_name,
                actions=actions,
                created_at=permission_orm.created_at,
                updated_at=permission_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"Error converting ORM to entity: {str(e)}")
            raise
