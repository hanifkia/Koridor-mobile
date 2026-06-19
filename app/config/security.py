from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging
import jwt
from uuid import UUID
from datetime import datetime, timezone

from app.core.services.auth_service_impl import AuthServiceImp
from app.config.dependencies import (
    get_auth_service,
    get_user_repository,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)

# ✅ OAuth2 Password Flow - This shows username/password login in Swagger
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",  # The endpoint that issues tokens
    description="OAuth2 authentication with username and password",
    scopes={
        "read": "Read access",
        "write": "Write access",
        "admin": "Admin access",
    },
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthServiceImp = Depends(get_auth_service),
    user_repo=Depends(get_user_repository),
):
    """
    Get current authenticated user from JWT token

    This dependency validates the OAuth2 token and returns the current user.
    If token is invalid or expired, raises 401 Unauthorized.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify JWT token
        payload = await auth_service.verify_token(token)
        if not payload:
            logger.warning("Invalid or expired token")
            raise credentials_exception

        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.warning("Token payload missing user ID")
            raise credentials_exception

        # Convert string to UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            logger.error(f"Invalid UUID format in token: {user_id_str}")
            raise credentials_exception

        # Fetch user
        user = await user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise credentials_exception

        # Build permissions list
        permissions = []
        if user.role and user.role.permissions:
            for p in user.role.permissions:
                for action in p.actions:
                    permissions.append(f"{p.table_name}_{action.value}")

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.name.value if user.role else None,
            "permissions": permissions,
            "user": user,
            "timezone": user.timezone,
            "currency": user.currency,
        }

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise credentials_exception
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error validating token: {str(e)}", exc_info=True)
        raise credentials_exception


async def require_permission(table_name: str, action: str):
    """Factory for permission checking dependency"""

    async def check_permission(current_user: dict = Depends(get_current_user)):
        required_permission = f"{table_name}_{action}"
        if required_permission not in current_user["permissions"]:
            logger.warning(
                f"User {current_user['user_id']} missing permission: {required_permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {required_permission}",
            )
        return current_user

    return check_permission


async def require_role(*allowed_roles: str):
    """Factory for role checking dependency"""

    async def check_role(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            logger.warning(
                f"User {current_user['user_id']} has invalid role: {user_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role not allowed. Required: {allowed_roles}",
            )
        return current_user

    return check_role
