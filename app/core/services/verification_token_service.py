from typing import Optional, List
import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from app.core.entities import UserVerificationToken, User
from app.core.interfaces import IVerificationTokenRepository, IUserRepository
from app.adapters.services.email.messages import WelcomeEmail

logger = logging.getLogger(__name__)


class VerificationTokenService:
    def __init__(
        self,
        verification_token_repository: IVerificationTokenRepository,
        user_repository: IUserRepository,
    ):
        self.verification_token_repository = verification_token_repository
        self.user_repository = user_repository

    async def create_token(
        self, user_id: int, token: str, expires_at: datetime
    ) -> UserVerificationToken:
        """Create a new verification token for a user"""
        try:
            verification_token = UserVerificationToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                id=uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            logger.info(
                f"Creating verification token for user_id={user_id} with token={token}"
            )
            created_token = await self.verification_token_repository.create(
                verification_token
            )
            logger.info(f"✅ Created verification token for user_id={user_id}")
            return created_token
        except Exception as e:
            logger.error(
                f"❌ Error creating verification token: {str(e)}", exc_info=True
            )
            raise

    async def get_token(self, token: str) -> Optional[UserVerificationToken]:
        """Get a verification token by its value"""
        try:
            verification_token = await self.verification_token_repository.get_by_token(
                token
            )
            if verification_token:
                logger.info(f"✅ Retrieved verification token for token={token}")
            else:
                logger.warning(f"⚠️ Verification token not found for token={token}")
            return verification_token
        except Exception as e:
            logger.error(
                f"❌ Error retrieving verification token: {str(e)}", exc_info=True
            )
            raise

    async def delete_token(self, token_id: int) -> bool:
        """Delete a verification token by its ID"""
        try:
            result = await self.verification_token_repository.delete(token_id)
            if result:
                logger.info(f"✅ Deleted verification token with id={token_id}")
            else:
                logger.warning(
                    f"⚠️ Failed to delete verification token with id={token_id}"
                )
            return result
        except Exception as e:
            logger.error(
                f"❌ Error deleting verification token: {str(e)}", exc_info=True
            )
            raise

    async def generate_and_store_token(self, user_id: int) -> UserVerificationToken:
        """Generate a new token and store it in the database"""
        try:
            # For development, we can use a simple token generation (e.g., UUID)
            import secrets
            import string

            chars = string.ascii_uppercase + string.digits
            token_value = "".join(secrets.choice(chars) for _ in range(8))
            expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
            return await self.create_token(
                user_id=user_id, token=token_value, expires_at=expires_at
            )
        except Exception as e:
            logger.error(
                f"❌ Error generating and storing verification token: {str(e)}",
                exc_info=True,
            )
            raise

    async def verify_token(self, token: str) -> Optional[UUID]:
        """Verify a token and return the associated user ID if valid"""
        try:
            verification_token: UserVerificationToken = await self.get_token(token)
            if verification_token and not verification_token.is_expired():
                logger.info(f"✅ Token verified successfully for token={token}")
                await self.verify_user_email(verification_token.user_id)
                return verification_token.user_id
            else:
                logger.warning(f"⚠️ Invalid or expired token: {token}")
                return None
        except Exception as e:
            logger.error(f"❌ Error verifying token: {str(e)}", exc_info=True)
            raise

    async def verify_user_email(self, user_id: int) -> None:
        """Mark user's email as verified and delete associated token"""
        try:
            # In a real implementation, you would also update the user's record to mark email as verified
            # For this example, we just delete the token
            tokens = await self.verification_token_repository.get_by_user_id(user_id)
            for token in tokens:
                await self.delete_token(token.id)
            logger.info(
                f"✅ User email verified and tokens deleted for user_id={user_id}"
            )
            user = await self.user_repository.get_by_id(user_id)
            if user:
                logger.info(f"🔄 Marking user {user_id} email as verified")
                await self.user_repository.verify_email(user_id)

                # Send welcome email
                logger.info(f"🔄 Sending welcome email to user {user_id}")
                await WelcomeEmail(
                    to=user.email, name=f"{user.first_name} {user.last_name}"
                ).send()
            else:
                logger.warning(
                    f"⚠️ User not found for user_id={user_id} during email verification"
                )

        except Exception as e:
            logger.error(f"❌ Error verifying user email: {str(e)}", exc_info=True)
            raise
