"""
User router with service layer
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID
import logging

from app.api.v1.schemas.user_schemas import (
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema,
    UserListResponseSchema,
    ChangePasswordSchema,
    UpdateStatusSchema,
    EmailVerificationResponseSchema,
    EmailVerificationSchema,
    ResendCodeSchema,
)
from app.core.services.user_service import UserService
from app.config.dependencies import get_user_service, get_verification_token_service
from app.config.security import get_current_user
from app.core.services.verification_token_service import VerificationTokenService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserCreateSchema,
    user_service: UserService = Depends(get_user_service),
):
    """Register a new user"""

    try:
        user = await user_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            middle_name=request.middle_name,
            last_name=request.last_name,
            phone_number=request.phone_number,
            timezone=request.timezone,
        )
        logger.info(f"✅ User registered: {user.email}")
        return UserResponseSchema.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
)
async def resend_verification_email(
    request: ResendCodeSchema,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Resend email verification link to current user"""

    try:
        await user_service.resend_verification_email(user_id=current_user["user_id"])
        logger.info(f"✅ Resent verification email to user: {current_user['user_id']}")
        return {"message": "Verification email resent successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to resend verification email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email",
        )


@router.post(
    "/email-verification",
    status_code=status.HTTP_200_OK,
    response_model=EmailVerificationResponseSchema,
)
async def verify_email(
    request: EmailVerificationSchema,
    user_service: UserService = Depends(get_user_service),
    verification_token_service: VerificationTokenService = Depends(
        get_verification_token_service
    ),
):
    """Verify user's email address"""

    try:
        user_id = await verification_token_service.verify_token(token=request.token)
        if not user_id:
            raise ValueError("Invalid or expired token")

        return EmailVerificationResponseSchema(message="Email verified successfully")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Email verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.get(
    "/",
    response_model=List[UserListResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Get all users with pagination"""

    try:
        users = await user_service.get_all_users(skip=skip, limit=limit)
        return [UserListResponseSchema.from_orm(u) for u in users]

    except Exception as e:
        logger.error(f"❌ Failed to list users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@router.get(
    "/me",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Get current user profile"""

    try:
        user = await user_service.get_user_by_id(user_id=current_user["user_id"])
        return UserResponseSchema.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get user profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Get user by ID"""

    try:
        user = await user_service.get_user_by_id(user_id=user_id)
        return UserResponseSchema.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


@router.patch(
    "/",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_current_user(
    request: UserUpdateSchema,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Update current user information"""

    try:
        user = await user_service.update_user(
            user_id=current_user["user_id"],
            email=request.email,
            first_name=request.first_name,
            middle_name=request.middle_name,
            last_name=request.last_name,
            phone_number=request.phone_number,
            timezone=request.timezone,
        )
        logger.info(f"✅ User updated: {user.id}")
        return UserResponseSchema.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to update user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Delete current user"""

    try:
        await user_service.delete_user(user_id=current_user["user_id"])
        logger.info(f"✅ User deleted: {current_user['user_id']}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to delete user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )


@router.patch(
    "/{user_id}/status",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user_status(
    user_id: UUID,
    request: UpdateStatusSchema,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Update user account status (admin only)"""

    # Authorization check
    if current_user["role"] != "admin":
        logger.warning(
            f"⚠️  Unauthorized status update attempt by user: {current_user['user_id']}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user status",
        )

    try:
        user = await user_service.update_user_status(
            user_id=user_id,
            status=request.status,
        )
        logger.info(f"✅ User status updated: {user_id} -> {request.status.value}")
        return UserResponseSchema.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to update user status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status",
        )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordSchema,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """Change user password"""

    try:
        # Validate passwords match
        request.validate_passwords_match()

        await user_service.change_password(
            user_id=current_user["user_id"],
            current_password=request.current_password,
            new_password=request.new_password,
        )
        logger.info(f"✅ Password changed for user: {current_user['user_id']}")

        return {"message": "Password changed successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to change password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )
