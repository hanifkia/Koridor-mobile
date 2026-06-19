"""
User service implementation
"""

from typing import Optional, List
import logging
from uuid import UUID

from app.core.entities import User, UserStatus, RoleType, Role
from app.core.interfaces import (
    IUserRepository,
    IRoleRepository,
)
from app.core.services.auth_service_impl import AuthServiceImp
from app.core.services.billing_service import BillingService
from app.core.services.verification_token_service import VerificationTokenService
from app.adapters.services.email.messages import VerificationEmailMessage

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""

    def __init__(
        self,
        user_repo: IUserRepository,
        role_repo: IRoleRepository,
        auth_service: AuthServiceImp,
        billing_service: BillingService,  # ← Add billing service dependency
        token_verification_service: VerificationTokenService,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.auth_service = auth_service
        self.billing_service = billing_service  # ← Store billing service
        self.token_verification_service = token_verification_service

    async def register_user(
        self,
        username: str,
        email: Optional[str],
        password: str,
        first_name: str,
        middle_name: Optional[str],
        last_name: str,
        phone_number: str,
        timezone: str,
    ) -> User:
        """
        Register a new user

        **Validation:**
        1. Check email is not already registered
        2. Check username is not already taken
        3. Check phone number is not already registered
        4. Verify COURIER role exists

        **Returns:**
        - Created user entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If creation fails
        """
        logger.info(f"🔄 Registering new user: {email}")

        # Check if email exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            logger.error(f"❌ Email already registered: {email}")
            raise ValueError("Email already registered")

        logger.info(f"✅ Email available: {email}")

        # Check if username exists
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            logger.error(f"❌ Username already taken: {username}")
            raise ValueError("Username already taken")

        logger.info(f"✅ Username available: {username}")

        # Check if phone exists
        existing_user = await self.user_repo.get_by_phone(phone_number)
        if existing_user:
            logger.error(f"❌ Phone number already registered: {phone_number}")
            raise ValueError("Phone number already registered")

        logger.info(f"✅ Phone number available: {phone_number}")

        # Hash password
        try:
            password_hash = await self.auth_service.hash_password(password)
            logger.info(f"✅ Password hashed")
        except Exception as e:
            logger.error(f"❌ Error hashing password: {str(e)}", exc_info=True)
            raise

        # Get COURIER role
        try:
            role = await self.role_repo.get_by_name(name=RoleType.COURIER)
            if not role:
                logger.error(f"❌ COURIER role not found")
                raise ValueError("COURIER role is not available. Contact support.")

            logger.info(f"✅ COURIER role found: {role.id}")
        except Exception as e:
            logger.error(f"❌ Error fetching role: {str(e)}", exc_info=True)
            raise

        # Create user entity
        try:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                phone_number=phone_number,
                status=UserStatus.INACTIVE,
                role=role,
                timezone=timezone,
            )

            created_user = await self.user_repo.create(user)
            logger.info(f"✅ User registered: {created_user.email}")

            # create free subscription for new user
            try:
                await self.billing_service.create_free_subscription_for_new_user(
                    user_id=created_user.id
                )
            except Exception as e:
                logger.error(
                    f"❌ Error creating free subscription: {str(e)}", exc_info=True
                )

            try:
                # generate verification token (for development, use user ID)
                user_verification_token = (
                    await self.token_verification_service.generate_and_store_token(
                        user_id=created_user.id
                    )
                )
            except Exception as e:
                logger.error(
                    f"❌ Error generating verification token: {str(e)}", exc_info=True
                )

            # send verification email
            try:
                await VerificationEmailMessage(
                    to=created_user.email,
                    name=f"{created_user.first_name} {created_user.last_name}",
                    token=user_verification_token.token,
                ).send()
                logger.info(f"✅ Sent verification email to: {created_user.email}")
            except Exception as e:
                logger.error(
                    f"❌ Error sending verification email: {str(e)}", exc_info=True
                )

            return created_user

        except Exception as e:
            logger.error(f"❌ Error creating user: {str(e)}", exc_info=True)
            raise

    async def resend_verification_email(self, email: str):
        user = await self.user_repo.get_by_email(email)
        try:
            token = await self.token_verification_service.generate_and_store_token(
                user_id=user.id
            )
            await VerificationEmailMessage(
                to=user.email,
                name=f"{user.first_name} {user.last_name}",
                token=token.token,
            ).send()
            logger.info(f"✅ Sent verification email to: {user.email}")
        except Exception as e:
            logger.error(
                f"❌ Error sending verification email: {str(e)}", exc_info=True
            )
            raise

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID

        **Returns:**
        - User entity

        **Raises:**
        - ValueError: If user not found
        """
        logger.info(f"🔄 Getting user: {user_id}")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User found: {user.email}")
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 10) -> List[User]:
        """
        Get all users with pagination

        **Returns:**
        - List of user entities

        **Raises:**
        - Exception: If query fails
        """
        logger.info(f"🔄 Getting all users (skip={skip}, limit={limit})")

        try:
            users = await self.user_repo.get_all(skip=skip, limit=limit)
            logger.info(f"✅ Retrieved {len(users)} users")
            return users

        except Exception as e:
            logger.error(f"❌ Error getting all users: {str(e)}", exc_info=True)
            raise

    async def update_user(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        """
        Update user information

        **Validation:**
        1. Verify user exists
        2. Check new email is not in use (if provided)

        **Returns:**
        - Updated user entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User found: {user.email}")

        # Check if new email exists
        if email and email != user.email:
            existing = await self.user_repo.get_by_email(email)
            if existing:
                logger.error(f"❌ Email already in use: {email}")
                raise ValueError("Email already in use")

            logger.info(f"✅ Email available: {email}")

        # Update fields
        try:
            user.email = email or user.email
            user.first_name = first_name or user.first_name
            user.middle_name = middle_name or user.middle_name
            user.last_name = last_name or user.last_name
            user.phone_number = phone_number or user.phone_number
            user.timezone = timezone or user.timezone

            updated_user = await self.user_repo.update(user_id, user)
            logger.info(f"✅ User updated: {user_id}")

            return updated_user

        except Exception as e:
            logger.error(f"❌ Error updating user: {str(e)}", exc_info=True)
            raise

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete user

        **Validation:**
        1. Verify user exists

        **Returns:**
        - True if deleted

        **Raises:**
        - ValueError: If user not found
        - Exception: If deletion fails
        """
        logger.info(f"🔄 Deleting user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User found: {user.email}")

        try:
            success = await self.user_repo.delete(user_id)
            if not success:
                logger.error(f"❌ Failed to delete user: {user_id}")
                raise ValueError(f"Failed to delete user: {user_id}")

            logger.info(f"✅ User deleted: {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting user: {str(e)}", exc_info=True)
            raise

    async def update_user_status(self, user_id: UUID, status: UserStatus) -> User:
        """
        Update user account status

        **Validation:**
        1. Verify user exists
        2. Verify status is valid

        **Returns:**
        - Updated user entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating user status: {user_id} -> {status.value}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User found: {user.email}")

        try:
            user.status = status
            updated_user = await self.user_repo.update(user_id, user)
            logger.info(f"✅ User status updated: {user_id} -> {status.value}")

            return updated_user

        except Exception as e:
            logger.error(f"❌ Error updating user status: {str(e)}", exc_info=True)
            raise

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password

        **Validation:**
        1. Verify user exists
        2. Verify current password is correct
        3. Verify new passwords match

        **Returns:**
        - True if password changed

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Changing password for user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User found: {user.email}")

        # Verify current password
        try:
            is_valid = await self.auth_service.verify_password(
                current_password, user.password_hash
            )
            if not is_valid:
                logger.error(f"❌ Current password is incorrect for user: {user_id}")
                raise ValueError("Current password is incorrect")

            logger.info(f"✅ Current password verified")

        except Exception as e:
            logger.error(f"❌ Error verifying password: {str(e)}", exc_info=True)
            raise

        # Hash new password
        try:
            new_password_hash = await self.auth_service.hash_password(new_password)
            user.password_hash = new_password_hash

            await self.user_repo.update(user_id, user)
            logger.info(f"✅ Password changed for user: {user_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Error changing password: {str(e)}", exc_info=True)
            raise
