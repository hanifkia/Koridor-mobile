from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.core.entities import User, UserAvatar, UserStatus, Role, Permission
from app.core.interfaces import IUserRepository

from app.core.entities import PermissionAction
from app.adapters.database.models import (
    UserORM,
    UserAvatarORM,
    RoleORM,
    PermissionRoleORM,
)

logger = logging.getLogger(__name__)


class UserRepositoryImp(IUserRepository):
    """User repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _get_user_eager_load_options(self):
        """Get standard eager load options for user queries"""
        return (
            selectinload(UserORM.role)
            .selectinload(RoleORM.role_permissions)
            .selectinload(PermissionRoleORM.permission),
            selectinload(UserORM.avatar),
        )

    async def create(self, entity: User) -> User:
        """Create a new user"""
        try:
            user_orm = UserORM(
                id=entity.id,
                first_name=entity.first_name,
                middle_name=entity.middle_name,
                last_name=entity.last_name,
                phone_number=entity.phone_number,
                email=entity.email,
                username=entity.username,
                password_hash=entity.password_hash,
                status=entity.status,
                role_id=entity.role.id if entity.role else None,
                timezone=entity.timezone,
                currency=entity.currency,
            )
            self.session.add(user_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()
            logger.info(f"User created and committed: {entity.email}")

            # Re-fetch with eager loading
            query = (
                select(UserORM)
                .where(UserORM.id == user_orm.id)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()

            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()  # ✅ Rollback on error
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise

    async def get_by_id(self, entity_id) -> Optional[User]:
        """Get user by ID with role and permissions loaded"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.id == entity_id)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()
            if not user_orm:
                return None
            return self._orm_to_entity(user_orm)
        except Exception as e:
            logger.error(f"Error getting user by id: {str(e)}")
            return None

    async def get_by_list_of_user_ids(self, user_ids: List[int]) -> List[User]:
        """Get users by list of IDs with role and permissions loaded"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.id.in_(user_ids))
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            users_orm = result.unique().scalars().all()
            return [self._orm_to_entity(u) for u in users_orm]
        except Exception as e:
            logger.error(f"Error getting users by list of ids: {str(e)}")
            return []

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        try:
            query = (
                select(UserORM)
                .offset(skip)
                .limit(limit)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            users_orm = result.unique().scalars().all()
            return [self._orm_to_entity(u) for u in users_orm]
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []

    async def update(self, entity_id, entity: User) -> Optional[User]:
        """Update an existing user with EXPLICIT DATABASE COMMIT"""
        try:
            logger.info(f"🔄 Starting update for user: {entity_id}")

            # Step 1: Get the existing user from database
            user_orm = await self.session.get(UserORM, entity_id)
            if not user_orm:
                logger.warning(f"❌ User not found for update: {entity_id}")
                return None

            logger.debug(f"📝 Current password hash: {user_orm.password_hash[:30]}...")

            # Step 2: Update ALL fields
            user_orm.first_name = entity.first_name
            user_orm.middle_name = entity.middle_name
            user_orm.last_name = entity.last_name
            user_orm.phone_number = entity.phone_number
            user_orm.email = entity.email
            user_orm.password_hash = entity.password_hash  # ✅ CRITICAL
            user_orm.status = entity.status
            user_orm.timezone = entity.timezone
            user_orm.currency = entity.currency
            user_orm.is_courier_profile_completed = entity.is_courier_profile_completed
            user_orm.is_terminal_setup_completed = entity.is_terminal_setup_completed
            if entity.role:
                user_orm.role_id = entity.role.id

            logger.debug(f"📝 New password hash: {user_orm.password_hash[:30]}...")

            # Step 3: Flush changes to prepare for commit
            await self.session.flush()
            logger.debug(f"✅ Session flushed - changes prepared")

            # ✅ CRITICAL: COMMIT IMMEDIATELY (don't wait for endpoint to finish)
            await self.session.commit()
            logger.info(f"💾 ✅ COMMITTED to database immediately")

            # Step 4: Refresh from database to confirm update
            await self.session.refresh(user_orm)
            logger.debug(f"✅ User object refreshed from database")

            # Step 5: Re-fetch with relationships
            query = (
                select(UserORM)
                .where(UserORM.id == entity_id)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            updated_user_orm = result.unique().scalar_one_or_none()

            if not updated_user_orm:
                logger.error(f"❌ Could not re-fetch updated user")
                return None

            logger.info(f"✅ User updated successfully: {entity_id}")
            logger.debug(
                f"✅ Final password hash: {updated_user_orm.password_hash[:30]}..."
            )

            return self._orm_to_entity(updated_user_orm)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error updating user: {str(e)}", exc_info=True)
            raise

    async def delete(self, entity_id) -> bool:
        """Delete a user"""
        try:
            user_orm = await self.session.get(UserORM, entity_id)
            if not user_orm:
                return False
            await self.session.delete(user_orm)
            await self.session.flush()
            await self.session.commit()  # ✅ ADD THIS
            logger.info(f"User deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()  # ✅ ADD THIS
            logger.error(f"Error deleting user: {str(e)}")
            return False

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            if email is not None:
                query = (
                    select(UserORM)
                    .where(UserORM.email == email)
                    .options(*self._get_user_eager_load_options())
                )
                result = await self.session.execute(query)
                user_orm = result.unique().scalar_one_or_none()

                if not user_orm:
                    return None

                return self._orm_to_entity(user_orm)
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.username == username)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()

            if not user_orm:
                return None

            return self._orm_to_entity(user_orm)

        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.phone_number == phone)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()
            if not user_orm:
                return None
            return self._orm_to_entity(user_orm)
        except Exception as e:
            logger.error(f"Error getting user by phone: {str(e)}")
            return None

    async def get_by_role(self, role_id, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.role_id == role_id)
                .offset(skip)
                .limit(limit)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            users_orm = result.unique().scalars().all()
            return [self._orm_to_entity(u) for u in users_orm]
        except Exception as e:
            logger.error(f"Error getting users by role: {str(e)}")
            return []

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        try:
            query = (
                select(UserORM)
                .where(UserORM.status == UserStatus.ACTIVE)
                .offset(skip)
                .limit(limit)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            users_orm = result.unique().scalars().all()
            return [self._orm_to_entity(u) for u in users_orm]
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []

    async def update_status(self, user_id, status: UserStatus) -> Optional[User]:
        """Update user status"""
        try:
            user_orm = await self.session.get(UserORM, user_id)
            if not user_orm:
                return None
            user_orm.status = status
            await self.session.flush()
            await self.session.commit()  # ✅ ADD THIS

            # Re-fetch with eager loading
            query = (
                select(UserORM)
                .where(UserORM.id == user_id)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()

            logger.info(f"User {user_id} status updated to {status.value}")
            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()  # ✅ ADD THIS
            logger.error(f"Error updating user status: {str(e)}")
            raise

    async def update_last_login(self, user_id) -> Optional[User]:
        """Update last login timestamp"""
        try:
            user_orm = await self.session.get(UserORM, user_id)
            if not user_orm:
                return None
            user_orm.last_login_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()  # ✅ ADD THIS

            # Re-fetch with eager loading
            query = (
                select(UserORM)
                .where(UserORM.id == user_id)
                .options(*self._get_user_eager_load_options())
            )
            result = await self.session.execute(query)
            user_orm = result.unique().scalar_one_or_none()

            logger.debug(f"User {user_id} last login updated")
            return self._orm_to_entity(user_orm)
        except Exception as e:
            await self.session.rollback()  # ✅ ADD THIS
            logger.error(f"Error updating last login: {str(e)}", exc_info=True)
            raise

    async def verify_email(self, user_id) -> bool:
        """Mark user email as verified"""
        try:
            user_orm = await self.session.get(UserORM, user_id)
            if not user_orm:
                return False
            user_orm.is_email_verified = True
            user_orm.email_verified_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()  # ✅ ADD THIS
            logger.info(f"User {user_id} email verified")
            return True
        except Exception as e:
            await self.session.rollback()  # ✅ ADD THIS
            logger.error(f"Error verifying email: {str(e)}")
            return False

    def _orm_to_entity(self, user_orm: UserORM) -> User:
        """Convert ORM model to domain entity"""
        try:
            # Convert avatar
            avatar = None
            if user_orm.avatar:
                avatar = UserAvatar(
                    id=user_orm.avatar.id,
                    file_name=user_orm.avatar.file_name,
                    file_path=user_orm.avatar.file_path,
                    file_type=user_orm.avatar.file_type,
                    file_size=user_orm.avatar.file_size,
                    user_id=user_orm.avatar.user_id,
                )

            # Convert role with permissions
            role = None
            if user_orm.role:
                permissions = []

                # Access role_permissions instead of the viewonly permissions
                if (
                    hasattr(user_orm.role, "role_permissions")
                    and user_orm.role.role_permissions
                ):
                    for rp in user_orm.role.role_permissions:
                        if rp.permission:
                            # ✅ FIXED: Use correct Permission fields
                            actions = [
                                PermissionAction(action)
                                for action in (rp.permission.actions or [])
                            ]
                            permissions.append(
                                Permission(
                                    id=rp.permission.id,
                                    table_name=rp.permission.table_name,
                                    actions=actions,
                                    created_at=rp.permission.created_at,
                                    updated_at=rp.permission.updated_at,
                                )
                            )

                role = Role(
                    id=user_orm.role.id,
                    name=user_orm.role.name,
                    permissions=permissions,
                    created_at=user_orm.role.created_at,
                    updated_at=user_orm.role.updated_at,
                )

            return User(
                id=user_orm.id,
                first_name=user_orm.first_name,
                middle_name=user_orm.middle_name,
                last_name=user_orm.last_name,
                phone_number=user_orm.phone_number,
                email=user_orm.email,
                is_email_verified=user_orm.is_email_verified,
                email_verified_at=user_orm.email_verified_at,
                is_courier_profile_completed=user_orm.is_courier_profile_completed,
                is_terminal_setup_completed=user_orm.is_terminal_setup_completed,
                username=user_orm.username,
                password_hash=user_orm.password_hash,
                status=user_orm.status,
                avatar=avatar,
                role=role,
                timezone=user_orm.timezone,
                currency=user_orm.currency,
                created_at=user_orm.created_at,
                updated_at=user_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise
