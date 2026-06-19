"""
Authentication service implementation with enhanced security
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import secrets
import string
import jwt
import logging
from passlib.context import CryptContext
from uuid import UUID

from app.core.entities import User, Role, PermissionAction
from app.core.interfaces import (
    IUserRepository,
    IRefreshTokenRepository,
    IPasswordResetRepository,
    IAuthService,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthServiceImp(IAuthService):
    """
    Authentication service implementation with enhanced security

    Features:
    - Password hashing with bcrypt
    - JWT token generation and verification
    - Refresh token management with revocation
    - Password reset with secure codes
    - Token invalidation on logout
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_reset_repo: IPasswordResetRepository,
    ):
        """
        Initialize auth service

        Args:
            user_repo: User repository instance
            refresh_token_repo: Refresh token repository instance
            password_reset_repo: Password reset repository instance
        """
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.password_reset_repo = password_reset_repo
        logger.info("🔄 AuthServiceImp initialized")

    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            logger.debug(f"🔄 Hashing password")
            hashed = pwd_context.hash(password)
            logger.debug(f"✅ Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"❌ Error hashing password: {str(e)}", exc_info=True)
            raise

    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            logger.debug(f"🔄 Verifying password")
            is_valid = pwd_context.verify(plain_password, password_hash)
            logger.debug(f"✅ Password verification result: {is_valid}")
            return is_valid
        except Exception as e:
            logger.warning(f"⚠️ Password verification error: {str(e)}")
            return False

    async def generate_access_token(
        self, user_id: UUID, role: Role, expires_in: int = 3600
    ) -> str:
        """Generate JWT access token with proper expiration"""
        try:
            logger.debug(f"🔄 Generating access token for user {user_id}")

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=expires_in)

            # Format role name safely
            role_name = (
                role.name.value if hasattr(role.name, "value") else str(role.name)
            )

            payload = {
                "sub": str(user_id),
                "role": role_name,
                "permissions": (
                    [p.name for p in role.permissions] if role.permissions else []
                ),
                "exp": expires_at,
                "iat": now,
                "type": "access",
            }

            token = jwt.encode(
                payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
            )
            logger.debug(f"✅ Access token generated for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"❌ Error generating access token: {str(e)}", exc_info=True)
            raise

    async def generate_refresh_token(self, user_id: UUID) -> str:
        """Generate secure refresh token"""
        try:
            logger.debug(f"🔄 Generating refresh token for user {user_id}")

            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )

            await self.refresh_token_repo.create_token(user_id, token, expires_at)
            logger.debug(f"✅ Refresh token generated for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"❌ Error generating refresh token: {str(e)}", exc_info=True)
            raise

    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token with detailed error handling"""
        try:
            logger.debug(f"🔄 Verifying token")
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            logger.debug(f"✅ Token verified successfully")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(
                f"❌ Unexpected error verifying token: {str(e)}", exc_info=True
            )
            return None

    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """Generate new access and refresh tokens"""
        try:
            logger.info(f"🔄 Refreshing access token")

            token_info = await self.refresh_token_repo.get_by_token(refresh_token)

            if not token_info:
                logger.warning("⚠️ Refresh token not found")
                return None

            if token_info.get("is_revoked"):
                logger.warning(
                    f"⚠️ Attempt to use revoked token for user {token_info['user_id']}"
                )
                return None

            # Check expiration
            expires_at = token_info.get("expires_at")
            if isinstance(expires_at, datetime):
                is_expired = datetime.now(timezone.utc) > expires_at
            else:
                is_expired = True

            if is_expired:
                logger.warning(
                    f"⚠️ Refresh token expired for user {token_info['user_id']}"
                )
                await self.refresh_token_repo.revoke_token(refresh_token)
                return None

            user = await self.user_repo.get_by_id(token_info["user_id"])
            if not user or not user.role:
                logger.error(
                    f"❌ User {token_info['user_id']} not found or has no role"
                )
                return None

            # Revoke old token
            await self.refresh_token_repo.revoke_token(refresh_token)

            # Generate new tokens
            access_token = await self.generate_access_token(user.id, user.role)
            new_refresh_token = await self.generate_refresh_token(user.id)

            logger.info(f"✅ Tokens refreshed for user {user.id}")
            return access_token, new_refresh_token
        except Exception as e:
            logger.error(f"❌ Error refreshing token: {str(e)}", exc_info=True)
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a single refresh token"""
        try:
            logger.info(f"🔄 Revoking refresh token")
            result = await self.refresh_token_repo.revoke_token(token)
            if result:
                logger.info("✅ Refresh token revoked")
            else:
                logger.warning("⚠️ Token not found or already revoked")
            return result
        except Exception as e:
            logger.error(f"❌ Error revoking token: {str(e)}", exc_info=True)
            return False

    async def revoke_user_tokens(self, user_id: UUID) -> bool:
        """Revoke all tokens for a user (logout)"""
        try:
            logger.info(f"🔄 Revoking all tokens for user {user_id}")
            result = await self.refresh_token_repo.revoke_user_tokens(user_id)
            if result:
                logger.info(f"✅ All tokens revoked for user {user_id}")
            else:
                logger.warning(f"⚠️ No tokens found for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Error revoking user tokens: {str(e)}", exc_info=True)
            return False

    async def verify_reset_code(self, code: str) -> Optional[UUID]:
        """
        Verify reset code and return user_id if valid

        Args:
            code: Reset code to verify

        Returns:
            User UUID if valid, None otherwise
        """
        try:
            logger.info(f"🔄 Starting to verify reset code")

            # Get the reset code from database
            reset_code_data = await self.password_reset_repo.get_by_code(code)

            if not reset_code_data:
                logger.warning(f"❌ Reset code not found: {code[:30]}...")
                return None

            logger.info(f"✅ Reset code found in database")

            # Check if already used
            if reset_code_data.get("is_used"):
                logger.warning(f"❌ Reset code already used")
                return None

            logger.info(f"✅ Reset code is not used")

            # Check if expired
            expires_at = reset_code_data.get("expires_at")

            if expires_at < datetime.now(timezone.utc):
                logger.warning(f"❌ Reset code expired")
                return None

            logger.info(f"✅ Reset code is not expired")

            user_id = reset_code_data.get("user_id")
            logger.info(f"✅ Reset code verified for user: {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"❌ Error verifying reset code: {str(e)}", exc_info=True)
            return None

    async def reset_password(self, code: str, new_password: str) -> bool:
        """Reset password using valid code"""
        try:
            logger.info(f"🔄 Starting password reset process")

            # 1. Verify the reset code
            user_id = await self.verify_reset_code(code)
            if not user_id:
                logger.warning(f"❌ Invalid or expired reset code")
                return False
            logger.info(f"✅ Reset code verified for user: {user_id}")

            # 2. Get the user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                logger.error(f"❌ User not found: {user_id}")
                return False
            logger.info(f"✅ User found: {user.first_name}")

            # 3. Hash the new password
            password_hash = await self.hash_password(new_password)
            logger.info(f"✅ Password hashed")

            # 4. Verify hash works before updating
            is_hash_valid = await self.verify_password(new_password, password_hash)
            if not is_hash_valid:
                logger.error(f"❌ Hash verification failed")
                return False
            logger.info(f"✅ Hash verified - hash is correct")

            # 5. Update the user with hashed password
            user.password_hash = password_hash
            logger.info(
                f"✅ Password assigned to user object: {user.password_hash[:50]}..."
            )

            # 6. Update in database
            updated_user = await self.user_repo.update(user_id, user)
            if not updated_user:
                logger.error(f"❌ Failed to update user: {user_id}")
                return False
            logger.info(f"✅ User password updated in database: {user_id}")

            # 7. Verify new password works
            password_verification = await self.verify_password(
                new_password, updated_user.password_hash
            )
            if not password_verification:
                logger.error(f"❌ Password verification FAILED after update!")
                return False
            logger.info(f"✅ Password verification SUCCESS - new password works!")

            # 8. Mark the reset code as used
            await self.password_reset_repo.mark_as_used(code)
            logger.info(f"✅ Reset code marked as used")

            # 9. Revoke all existing tokens for security
            await self.revoke_user_tokens(user_id)
            logger.info(f"✅ All tokens revoked for user")

            logger.info(f"✅ PASSWORD RESET COMPLETELY SUCCESSFUL for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error resetting password: {str(e)}", exc_info=True)
            return False

    async def create_password_reset_code(self, user_id: UUID) -> str:
        """
        Create a password reset code for user

        Args:
            user_id: User UUID

        Returns:
            Reset code string

        Raises:
            Exception: If creation fails
        """
        try:
            logger.info(f"🔄 Creating password reset code for user: {user_id}")

            # Generate unique code
            chars = string.ascii_uppercase + string.digits
            code = "".join(secrets.choice(chars) for _ in range(8))
            logger.debug(f"Generated code: {code}...")

            # Set expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

            # Save to database
            created_code = await self.password_reset_repo.create_reset_code(
                user_id=user_id,
                code=code,
                expires_at=expires_at,
            )

            logger.info(f"✅ Password reset code created for user {user_id}")
            logger.debug(f"   Code: {code[:30]}...")
            logger.debug(f"   Expires at: {expires_at}")

            return created_code

        except Exception as e:
            logger.error(f"❌ Error creating reset code: {str(e)}", exc_info=True)
            raise
