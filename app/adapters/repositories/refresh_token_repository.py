import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID

from app.core.interfaces import IRefreshTokenRepository
from app.adapters.database.models import RefreshTokenORM

logger = logging.getLogger(__name__)


class RefreshTokenRepositoryImp(IRefreshTokenRepository):
    """Refresh token repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> str:
        """Create refresh token"""
        try:
            refresh_token = RefreshTokenORM(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
            )
            self.session.add(refresh_token)
            await self.session.flush()
            logger.debug(f"✅ Refresh token created for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"❌ Error creating refresh token: {str(e)}", exc_info=True)
            raise

    async def get_by_token(self, token: str) -> Optional[dict]:
        """Get token info by token string"""
        try:
            query = select(RefreshTokenORM).where(RefreshTokenORM.token == token)
            result = await self.session.execute(query)
            token_orm = result.scalar_one_or_none()

            if not token_orm:
                logger.debug(f"Refresh token not found: {token[:20]}...")
                return None

            return {
                "id": token_orm.id,
                "user_id": token_orm.user_id,
                "token": token_orm.token,
                "is_revoked": token_orm.is_revoked,
                "expires_at": token_orm.expires_at,
                "created_at": token_orm.created_at,
            }
        except Exception as e:
            logger.error(f"❌ Error getting refresh token: {str(e)}", exc_info=True)
            return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a single refresh token"""
        try:
            query = select(RefreshTokenORM).where(RefreshTokenORM.token == token)
            result = await self.session.execute(query)
            token_orm = result.scalar_one_or_none()

            if not token_orm:
                logger.warning(f"Refresh token not found for revoke: {token[:20]}...")
                return False

            token_orm.is_revoked = True
            token_orm.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            logger.info(f"✅ Refresh token revoked: {token[:20]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Error revoking token: {str(e)}", exc_info=True)
            return False

    async def revoke_user_tokens(self, user_id: UUID) -> bool:
        """Revoke all tokens for a user with EXPLICIT COMMIT"""
        try:
            query = select(RefreshTokenORM).where(RefreshTokenORM.user_id == user_id)
            result = await self.session.execute(query)
            tokens = result.scalars().all()

            for token_orm in tokens:
                token_orm.is_revoked = True
                token_orm.revoked_at = datetime.now(timezone.utc)

            await self.session.flush()

            # ✅ EXPLICIT COMMIT
            await self.session.commit()
            logger.info(f"✅ All tokens revoked and COMMITTED for user {user_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error revoking user tokens: {str(e)}", exc_info=True)
            return False

    async def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens from database"""
        try:
            query = delete(RefreshTokenORM).where(
                RefreshTokenORM.expires_at
                < datetime.now(timezone.utc)  # ✅ USE timezone.utc
            )
            result = await self.session.execute(query)
            await self.session.flush()

            deleted_count = result.rowcount
            logger.info(f"✅ Cleaned up {deleted_count} expired refresh tokens")
            return deleted_count
        except Exception as e:
            logger.error(
                f"❌ Error cleaning up expired tokens: {str(e)}", exc_info=True
            )
            return 0
