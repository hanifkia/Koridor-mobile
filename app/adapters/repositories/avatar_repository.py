from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.entities import UserAvatar
from app.adapters.database.models import UserAvatarORM
from app.core.interfaces import IAvatarRepository

logger = logging.getLogger(__name__)


class AvatarRepositoryImp(IAvatarRepository):
    """Avatar repository implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._logger = logging.getLogger(__name__)

    def _orm_to_entity(self, orm_obj: Optional[UserAvatarORM]) -> Optional[UserAvatar]:
        """Convert ORM object to entity"""
        if not orm_obj:
            return None

        return UserAvatar(
            id=orm_obj.id,
            user_id=orm_obj.user_id,
            file_name=orm_obj.file_name,
            file_path=orm_obj.file_path,
            file_type=orm_obj.file_type,
            file_size=orm_obj.file_size,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )

    async def create(self, entity: UserAvatar) -> UserAvatar:
        """Create a new avatar"""
        self._logger.info(f"📝 Creating avatar for user: {entity.user_id}")

        orm_obj = UserAvatarORM(
            id=entity.id,
            user_id=entity.user_id,
            file_name=entity.file_name,
            file_path=entity.file_path,
            file_type=entity.file_type,
            file_size=entity.file_size,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(orm_obj)
        await self.session.flush()
        await self.session.commit()

        self._logger.info(f"✅ Avatar created: {orm_obj.id}")
        return self._orm_to_entity(orm_obj)

    async def get_by_id(self, entity_id: UUID) -> Optional[UserAvatar]:
        """Get avatar by ID"""
        self._logger.debug(f"🔍 Getting avatar by ID: {entity_id}")

        stmt = select(UserAvatarORM).where(UserAvatarORM.id == entity_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        if orm_obj:
            self._logger.info(f"✅ Avatar retrieved: {orm_obj.id}")
        else:
            self._logger.warning(f"⚠️ Avatar not found: {entity_id}")

        return self._orm_to_entity(orm_obj)

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserAvatar]:
        """Get avatar by user ID"""
        self._logger.debug(f"🔍 Getting avatar for user: {user_id}")

        stmt = select(UserAvatarORM).where(UserAvatarORM.user_id == user_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        if orm_obj:
            self._logger.info(f"✅ Avatar retrieved for user {user_id}: {orm_obj.id}")
        else:
            self._logger.debug(f"ℹ️ No avatar found for user: {user_id}")

        return self._orm_to_entity(orm_obj)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[UserAvatar]:
        """Get all avatars with pagination"""
        self._logger.debug(f"🔍 Getting all avatars (skip={skip}, limit={limit})")

        stmt = select(UserAvatarORM).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        orm_objs = result.scalars().all()

        self._logger.info(f"✅ Retrieved {len(orm_objs)} avatars")
        return [self._orm_to_entity(obj) for obj in orm_objs]

    async def update(self, entity_id: UUID, entity: UserAvatar) -> Optional[UserAvatar]:
        """Update an existing avatar"""
        self._logger.info(f"🔄 Updating avatar: {entity_id}")

        orm_obj = await self.session.get(UserAvatarORM, entity_id)
        if not orm_obj:
            self._logger.warning(f"❌ Avatar not found: {entity_id}")
            return None

        # Update fields
        if entity.file_name:
            orm_obj.file_name = entity.file_name
        if entity.file_path:
            orm_obj.file_path = entity.file_path
        if entity.file_type:
            orm_obj.file_type = entity.file_type
        if entity.file_size is not None:
            orm_obj.file_size = entity.file_size

        orm_obj.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.commit()

        self._logger.info(f"✅ Avatar updated: {entity_id}")
        return self._orm_to_entity(orm_obj)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete an avatar"""
        self._logger.info(f"🗑️ Deleting avatar: {entity_id}")

        orm_obj = await self.session.get(UserAvatarORM, entity_id)
        if not orm_obj:
            self._logger.warning(f"❌ Avatar not found: {entity_id}")
            return False

        await self.session.delete(orm_obj)
        await self.session.flush()
        await self.session.commit()

        self._logger.info(f"✅ Avatar deleted: {entity_id}")
        return True

    async def delete_by_user_id(self, user_id: UUID) -> bool:
        """Delete avatar by user ID"""
        self._logger.info(f"🗑️ Deleting avatar for user: {user_id}")

        stmt = select(UserAvatarORM).where(UserAvatarORM.user_id == user_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()

        if not orm_obj:
            self._logger.warning(f"⚠️ No avatar found for user: {user_id}")
            return False

        await self.session.delete(orm_obj)
        await self.session.flush()
        await self.session.commit()

        self._logger.info(f"✅ Avatar deleted for user: {user_id}")
        return True
