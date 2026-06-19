from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


class IPasswordResetRepository(ABC):
    """Password reset token repository interface"""

    @abstractmethod
    async def create_reset_code(
        self, user_id: int, code: str, expires_at: datetime
    ) -> str:
        """Create password reset code"""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[dict]:
        """Get reset code info"""
        pass

    @abstractmethod
    async def mark_as_used(self, code: str) -> bool:
        """Mark reset code as used"""
        pass

    @abstractmethod
    async def delete_expired_codes(self, user_id: int) -> bool:
        """Delete expired reset codes for user"""
        pass


class IRefreshTokenRepository(ABC):
    """Refresh token repository interface"""

    @abstractmethod
    async def create_token(self, user_id: int, token: str, expires_at: datetime) -> str:
        """Create refresh token"""
        pass

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[dict]:
        """Get token info"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        pass

    @abstractmethod
    async def revoke_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for user"""
        pass

    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens, return count deleted"""
        pass
