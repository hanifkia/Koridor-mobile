import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID

from app.core.interfaces import IPasswordResetRepository
from app.adapters.database.models import PasswordResetCodeORM

logger = logging.getLogger(__name__)


class PasswordResetRepositoryImp(IPasswordResetRepository):
    """Password reset repository SQLAlchemy implementation"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_reset_code(
        self, user_id: UUID, code: str, expires_at: datetime
    ) -> str:
        """Create password reset code"""
        try:
            logger.info(f"🔄 Creating reset code for user: {user_id}")

            reset_code_orm = PasswordResetCodeORM(
                user_id=user_id,
                code=code,
                expires_at=expires_at,
            )
            self.session.add(reset_code_orm)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Reset code created and committed: {code[:30]}...")
            logger.debug(f"   User ID: {user_id}")
            logger.debug(f"   Expires at: {expires_at}")

            return code
        except Exception as e:
            await self.session.rollback()  # ✅ Rollback on error
            logger.error(f"❌ Error creating reset code: {str(e)}", exc_info=True)
            raise

    async def get_by_code(self, code: str) -> Optional[dict]:
        """Get reset code info by code - ✅ CRITICAL METHOD"""
        try:
            logger.debug(f"🔍 Looking for reset code: {code[:30]}...")

            # Query the database
            query = select(PasswordResetCodeORM).where(
                PasswordResetCodeORM.code == code
            )
            result = await self.session.execute(query)
            reset_orm = result.scalar_one_or_none()

            if not reset_orm:
                logger.warning(f"❌ Reset code NOT found in database: {code[:30]}...")

                # DEBUG: Check all codes in DB
                all_codes = await self.session.execute(
                    select(PasswordResetCodeORM).limit(5)
                )
                all_codes_list = all_codes.scalars().all()
                if all_codes_list:
                    logger.debug(f"📊 Sample codes in DB:")
                    for c in all_codes_list:
                        logger.debug(
                            f"   - {c.code[:30]}... (user: {c.user_id}, used: {c.is_used})"
                        )
                else:
                    logger.debug(f"📊 No codes in database at all")

                return None

            logger.info(f"✅ Reset code found: {code[:30]}...")
            logger.debug(f"   User ID: {reset_orm.user_id}")
            logger.debug(f"   Is Used: {reset_orm.is_used}")
            logger.debug(f"   Expires At: {reset_orm.expires_at}")
            logger.debug(f"   Created At: {reset_orm.created_at}")

            return {
                "id": reset_orm.id,
                "user_id": reset_orm.user_id,
                "code": reset_orm.code,
                "is_used": reset_orm.is_used,
                "expires_at": reset_orm.expires_at,
                "created_at": reset_orm.created_at,
            }
        except Exception as e:
            logger.error(f"❌ Error getting reset code: {str(e)}", exc_info=True)
            return None

    async def mark_as_used(self, code: str) -> bool:
        """Mark reset code as used"""
        try:
            logger.info(f"🔄 Marking reset code as used: {code[:30]}...")

            query = select(PasswordResetCodeORM).where(
                PasswordResetCodeORM.code == code
            )
            result = await self.session.execute(query)
            reset_orm = result.scalar_one_or_none()

            if not reset_orm:
                logger.warning(f"❌ Reset code not found for marking: {code[:30]}...")
                return False

            reset_orm.is_used = True
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            logger.info(f"✅ Reset code marked as used: {code[:30]}...")
            return True
        except Exception as e:
            await self.session.rollback()  # ✅ Rollback on error
            logger.error(f"❌ Error marking code as used: {str(e)}", exc_info=True)
            return False

    async def delete_expired_codes(self, user_id: UUID) -> bool:
        """Delete expired reset codes for user"""
        try:
            logger.info(f"🔄 Deleting expired codes for user: {user_id}")

            query = delete(PasswordResetCodeORM).where(
                (PasswordResetCodeORM.user_id == user_id)
                & (PasswordResetCodeORM.expires_at < datetime.now(timezone.utc))
            )
            result = await self.session.execute(query)
            await self.session.flush()

            # ✅ CRITICAL: COMMIT IMMEDIATELY
            await self.session.commit()

            deleted_count = result.rowcount
            logger.info(f"✅ Deleted {deleted_count} expired codes for user {user_id}")
            return deleted_count > 0
        except Exception as e:
            await self.session.rollback()  # ✅ Rollback on error
            logger.error(f"❌ Error deleting expired codes: {str(e)}", exc_info=True)
            return False
