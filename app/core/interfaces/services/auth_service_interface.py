"""
Authentication service interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from uuid import UUID

from app.core.entities import User, Role


class IAuthService(ABC):
    """Authentication service interface"""

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Hashed password

        Raises:
            Exception: If hashing fails
        """
        pass

    @abstractmethod
    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """
        Verify password against hash

        Args:
            plain_password: Plain text password
            password_hash: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        pass

    @abstractmethod
    async def generate_access_token(
        self, user_id: UUID, role: Role, expires_in: int = 3600
    ) -> str:
        """
        Generate JWT access token

        Args:
            user_id: User UUID
            role: User role with permissions
            expires_in: Token expiration time in seconds (default: 1 hour)

        Returns:
            JWT access token

        Raises:
            Exception: If token generation fails
        """
        pass

    @abstractmethod
    async def generate_refresh_token(self, user_id: UUID) -> str:
        """
        Generate secure refresh token

        Args:
            user_id: User UUID

        Returns:
            Refresh token string

        Raises:
            Exception: If token generation fails
        """
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify

        Returns:
            Token payload dict if valid, None otherwise
        """
        pass

    @abstractmethod
    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """
        Generate new access and refresh tokens

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) if valid,
            None if refresh token is invalid/expired/revoked
        """
        pass

    @abstractmethod
    async def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a single refresh token

        Args:
            token: Refresh token to revoke

        Returns:
            True if revoked successfully, False otherwise
        """
        pass

    @abstractmethod
    async def revoke_user_tokens(self, user_id: UUID) -> bool:
        """
        Revoke all tokens for a user (logout)

        Args:
            user_id: User UUID

        Returns:
            True if all tokens revoked, False otherwise
        """
        pass

    @abstractmethod
    async def verify_reset_code(self, code: str) -> Optional[UUID]:
        """
        Verify password reset code

        Args:
            code: Reset code to verify

        Returns:
            User UUID if code is valid and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def reset_password(self, code: str, new_password: str) -> bool:
        """
        Reset user password using valid reset code

        Args:
            code: Password reset code
            new_password: New password

        Returns:
            True if password reset successfully, False otherwise
        """
        pass

    @abstractmethod
    async def create_password_reset_code(self, user_id: UUID) -> str:
        """
        Create a password reset code for user

        Args:
            user_id: User UUID

        Returns:
            Reset code string

        Raises:
            Exception: If code creation fails
        """
        pass
