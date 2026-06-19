from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, selectinload

from app.core.entities import Role, Permission, PermissionAction, RoleType
from app.core.interfaces import IRoleRepository
from app.adapters.database.models import RoleORM, PermissionRoleORM, PermissionORM

logger = logging.getLogger(__name__)


class RoleRepositoryImp(IRoleRepository):
    """Role repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: Role) -> Role:
        """Create a new role"""
        try:
            role_orm = RoleORM(
                id=entity.id,
                name=(
                    entity.name.value
                    if isinstance(entity.name, RoleType)
                    else entity.name
                ),
            )
            self.session.add(role_orm)
            await self.session.flush()
            logger.info(f"Role created: {entity.name}")
            return await self._orm_to_entity(role_orm)
        except Exception as e:
            logger.error(f"Error creating role: {str(e)}")
            raise

    async def get_by_id(self, entity_id) -> Optional[Role]:
        """Get role by ID with permissions"""
        try:
            query = (
                select(RoleORM)
                .where(RoleORM.id == entity_id)
                .options(joinedload(RoleORM.permissions))
            )
            result = await self.session.execute(query)
            role_orm = result.unique().scalar_one_or_none()
            if not role_orm:
                return None
            return await self._orm_to_entity(role_orm)
        except Exception as e:
            logger.error(f"Error getting role by id: {str(e)}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles with pagination"""
        try:
            query = (
                select(RoleORM)
                .offset(skip)
                .limit(limit)
                .options(joinedload(RoleORM.permissions))
            )
            result = await self.session.execute(query)
            roles_orm = result.unique().scalars().all()
            return [await self._orm_to_entity(r) for r in roles_orm]
        except Exception as e:
            logger.error(f"Error getting all roles: {str(e)}")
            return []

    async def update(self, entity_id, entity: Role) -> Optional[Role]:
        """Update an existing role"""
        try:
            role_orm = await self.session.get(RoleORM, entity_id)
            if not role_orm:
                return None

            role_orm.name = (
                entity.name.value if isinstance(entity.name, RoleType) else entity.name
            )
            await self.session.flush()
            logger.info(f"Role updated: {entity_id}")
            return await self._orm_to_entity(role_orm)
        except Exception as e:
            logger.error(f"Error updating role: {str(e)}")
            raise

    async def delete(self, entity_id) -> bool:
        """Delete a role"""
        try:
            role_orm = await self.session.get(RoleORM, entity_id)
            if not role_orm:
                return False
            await self.session.delete(role_orm)
            await self.session.flush()
            logger.info(f"Role deleted: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting role: {str(e)}")
            return False

    async def get_by_name(self, name: str | RoleType) -> Optional[Role]:
        """Get role by name"""
        try:
            # Ensure we have the enum value as a string
            if isinstance(name, RoleType):
                role_name_value = name.value
            else:
                role_name_value = RoleType(name).value  # Validate and get value

            query = (
                select(RoleORM)
                .where(RoleORM.name == role_name_value)  # Compare strings
                .options(joinedload(RoleORM.permissions))
            )
            result = await self.session.execute(query)
            role_orm = result.unique().scalar_one_or_none()
            if not role_orm:
                return None
            return await self._orm_to_entity(role_orm)
        except ValueError as e:
            logger.error(f"Invalid role name: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting role by name: {str(e)}")
            return None

    async def get_with_permissions(self, role_id) -> Optional[Role]:
        """Get role with all permissions loaded"""
        try:
            query = (
                select(RoleORM)
                .where(RoleORM.id == role_id)
                .options(
                    selectinload(RoleORM.role_permissions).joinedload(
                        PermissionRoleORM.permission
                    )
                )
            )
            result = await self.session.execute(query)
            role_orm = result.unique().scalar_one_or_none()
            if not role_orm:
                return None
            return await self._orm_to_entity(role_orm)
        except Exception as e:
            logger.error(f"Error getting role with permissions: {str(e)}")
            return None

    async def add_permission_to_role(self, role_id, permission_id) -> bool:
        """Add permission to role"""
        try:
            # Check if already exists
            query = select(PermissionRoleORM).where(
                and_(
                    PermissionRoleORM.role_id == role_id,
                    PermissionRoleORM.permission_id == permission_id,
                )
            )
            result = await self.session.execute(query)
            if result.scalar_one_or_none():
                logger.debug(
                    f"Permission {permission_id} already assigned to role {role_id}"
                )
                return True

            permission_role = PermissionRoleORM(
                role_id=role_id, permission_id=permission_id
            )
            self.session.add(permission_role)
            await self.session.flush()
            logger.info(f"Permission {permission_id} added to role {role_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding permission to role: {str(e)}")
            return False

    async def remove_permission_from_role(self, role_id, permission_id) -> bool:
        """Remove permission from role"""
        try:
            query = select(PermissionRoleORM).where(
                and_(
                    PermissionRoleORM.role_id == role_id,
                    PermissionRoleORM.permission_id == permission_id,
                )
            )
            result = await self.session.execute(query)
            permission_role = result.scalar_one_or_none()
            if not permission_role:
                logger.warning(
                    f"Permission {permission_id} not found for role {role_id}"
                )
                return False
            await self.session.delete(permission_role)
            await self.session.flush()
            logger.info(f"Permission {permission_id} removed from role {role_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing permission from role: {str(e)}")
            return False

    async def get_role_permissions(self, role_id) -> List[Permission]:
        """Get all permissions for a role"""
        try:
            query = (
                select(PermissionORM)
                .join(PermissionRoleORM)
                .where(PermissionRoleORM.role_id == role_id)
            )
            result = await self.session.execute(query)
            permissions_orm = result.scalars().all()
            from app.adapters.repositories.permission_repository import (
                PermissionRepositoryImp,
            )

            perm_repo = PermissionRepositoryImp(self.session)
            return [await perm_repo._orm_to_entity(p) for p in permissions_orm]
        except Exception as e:
            logger.error(f"Error getting role permissions: {str(e)}")
            return []

    async def _orm_to_entity(self, role_orm: RoleORM) -> Role:
        """Convert ORM model to domain entity"""
        try:
            permissions = []
            if role_orm.permissions:
                from app.adapters.repositories.permission_repository import (
                    PermissionRepositoryImp,
                )

                perm_repo = PermissionRepositoryImp(self.session)
                for perm_orm in role_orm.permissions:
                    perm = await perm_repo._orm_to_entity(perm_orm)
                    permissions.append(perm)

            return Role(
                id=role_orm.id,
                name=RoleType(role_orm.name),
                permissions=permissions,
                created_at=role_orm.created_at,
                updated_at=role_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"Error converting ORM to entity: {str(e)}")
            raise
