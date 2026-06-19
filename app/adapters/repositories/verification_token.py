"""
User verification token repository implementation
"""

from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.entities import UserVerificationToken
from app.core.interfaces import IVerificationTokenRepository
from app.adapters.database.models import UserVerificationTokenORM

logger = logging.getLogger(__name__)


class VerificationTokenRepositoryImp(IVerificationTokenRepository):
    """User verification token repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entity: UserVerificationToken) -> UserVerificationToken:
        """Create a new verification token"""
        try:
            logger.info(f"🔄 Creating verification token for user: {entity.user_id}")

            token_orm = UserVerificationTokenORM(
                id=entity.id,
                user_id=entity.user_id,
                token=entity.token,
                expires_at=entity.expires_at,
            )
            self.session.add(token_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Verification token created: {entity.id}")
            return await self._orm_to_entity(token_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error creating verification token: {str(e)}", exc_info=True
            )
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[UserVerificationToken]:
        """Get verification token by ID"""
        try:
            query = select(UserVerificationTokenORM).where(
                UserVerificationTokenORM.id == entity_id
            )
            result = await self.session.execute(query)
            token_orm = result.scalar_one_or_none()
            if not token_orm:
                logger.debug(f"Verification token not found: {entity_id}")
                return None
            return await self._orm_to_entity(token_orm)
        except Exception as e:
            logger.error(
                f"❌ Error getting verification token by id: {str(e)}", exc_info=True
            )
            return None

    async def get_by_token(self, token: str) -> Optional[UserVerificationToken]:
        """Get verification token by token string"""
        try:
            logger.info(f"🔄 Getting verification token by string: {token}")

            query = select(UserVerificationTokenORM).where(
                UserVerificationTokenORM.token == token
            )
            result = await self.session.execute(query)
            token_orm = result.scalar_one_or_none()

            if not token_orm:
                logger.debug(f"Verification token not found: {token}")
                return None

            logger.info(f"✅ Verification token found for user: {token_orm.user_id}")
            return await self._orm_to_entity(token_orm)

        except Exception as e:
            logger.error(
                f"❌ Error getting verification token by string: {str(e)}",
                exc_info=True,
            )
            return None

    async def get_by_user_id(
        self, user_id: UUID
    ) -> Optional[list[UserVerificationToken]]:
        """Get verification token by user ID"""
        try:
            logger.info(f"🔄 Getting verification token for user: {user_id}")

            query = select(UserVerificationTokenORM).where(
                UserVerificationTokenORM.user_id == user_id
            )
            result = await self.session.execute(query)
            token_orm = result.scalars().all()

            if not token_orm:
                logger.debug(f"Verification token not found for user: {user_id}")
                return None

            logger.info(f"✅ Verification token found for user: {user_id}")
            return [await self._orm_to_entity(o) for o in token_orm]

        except Exception as e:
            logger.error(
                f"❌ Error getting verification token by user id: {str(e)}",
                exc_info=True,
            )
            return None

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> list[UserVerificationToken]:
        """Get all verification tokens with pagination"""
        try:
            query = select(UserVerificationTokenORM).offset(skip).limit(limit)
            result = await self.session.execute(query)
            tokens_orm = result.scalars().all()
            return [await self._orm_to_entity(t) for t in tokens_orm]
        except Exception as e:
            logger.error(
                f"❌ Error getting all verification tokens: {str(e)}", exc_info=True
            )
            return []

    async def update(
        self, entity_id: UUID, entity: UserVerificationToken
    ) -> Optional[UserVerificationToken]:
        """Update an existing verification token"""
        try:
            logger.info(f"🔄 Updating verification token: {entity_id}")

            token_orm = await self.session.get(UserVerificationTokenORM, entity_id)
            if not token_orm:
                logger.warning(f"❌ Verification token not found: {entity_id}")
                return None

            # Update fields
            token_orm.token = entity.token or token_orm.token
            token_orm.expires_at = entity.expires_at or token_orm.expires_at

            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Verification token updated: {entity_id}")
            return await self._orm_to_entity(token_orm)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error updating verification token: {str(e)}", exc_info=True
            )
            raise

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a verification token"""
        try:
            logger.info(f"🔄 Deleting verification token: {entity_id}")

            token_orm = await self.session.get(UserVerificationTokenORM, entity_id)
            if not token_orm:
                logger.warning(f"❌ Verification token not found: {entity_id}")
                return False

            await self.session.delete(token_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Verification token deleted: {entity_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error deleting verification token: {str(e)}", exc_info=True
            )
            return False

    async def _orm_to_entity(
        self, token_orm: UserVerificationTokenORM
    ) -> UserVerificationToken:
        """Convert ORM model to domain entity"""
        try:
            return UserVerificationToken(
                id=token_orm.id,
                user_id=token_orm.user_id,
                token=token_orm.token,
                expires_at=token_orm.expires_at,
                created_at=token_orm.created_at,
                updated_at=token_orm.updated_at,
            )
        except Exception as e:
            logger.error(f"❌ Error converting ORM to entity: {str(e)}", exc_info=True)
            raise
