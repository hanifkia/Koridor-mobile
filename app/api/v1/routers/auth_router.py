from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.api.v1.schemas.auth_schemas import (
    LoginResponseSchema,
    RefreshTokenRequestSchema,
    ForgotPasswordRequestSchema,
    ForgotPasswordResponseSchema,
    ResetPasswordRequestSchema,
    ResetPasswordResponseSchema,
)
from app.api.v1.schemas.user_schemas import UserResponseSchema
from app.core.services.auth_service_impl import AuthServiceImp
from app.config.dependencies import (
    get_auth_service,
    get_user_repository,
)
from app.config.security import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post(
    "/login",
    response_model=LoginResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Login",
    description="Standard OAuth2 password flow login endpoint",
    responses={
        200: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "refresh_token": "refresh_token_string",
                    }
                }
            },
        },
        401: {"description": "Invalid username or password"},
        403: {"description": "User account is not active"},
    },
)
async def login(
    # ✅ OAuth2PasswordRequestForm - Swagger will show username/password fields
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthServiceImp = Depends(get_auth_service),
    user_repo=Depends(get_user_repository),
):
    """
    **OAuth2 compatible token endpoint**

    This endpoint implements the OAuth2 password flow:
    - Takes username/email and password
    - Returns JWT access token and refresh token
    - Conforms to RFC 6749 OAuth2 standards

    **Usage in Swagger UI:**
    1. Click "Authorize" button (lock icon at top right)
    2. Enter username/email in "username" field
    3. Enter password in "password" field
    4. Click "Authorize"

    **Parameters:**
    - **username**: Username or email address (OAuth2 field)
    - **password**: User password (OAuth2 field)
    - **scope**: (Optional) Space-separated scopes: "read write admin"

    **Response:**
    - **access_token**: JWT token for API requests
    - **token_type**: Always "bearer"
    - **expires_in**: Token expiration time in seconds
    - **refresh_token**: Token for refreshing access
    """
    logger.info(f"Login attempt for: {form_data.username}")

    # Find user by email or username
    user = await user_repo.get_by_email(form_data.username)
    if not user:
        user = await user_repo.get_by_username(form_data.username)

    if not user:
        logger.warning(f"User not found: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    is_valid = await auth_service.verify_password(
        form_data.password, user.password_hash
    )
    if not is_valid:
        logger.warning(f"Invalid password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user has a role assigned
    if not user.role:
        logger.error(f"User {user.id} has no role assigned")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not properly configured",
        )

    # Generate tokens
    access_token = await auth_service.generate_access_token(
        user_id=user.id,
        role=user.role,
        expires_in=3600,
    )
    refresh_token = await auth_service.generate_refresh_token(user.id)

    # Update last login
    await user_repo.update_last_login(user.id)

    logger.info(f"Successful login for user: {user.id}")

    return LoginResponseSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=LoginResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    responses={
        200: {"description": "New access token generated"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: RefreshTokenRequestSchema,
    auth_service: AuthServiceImp = Depends(get_auth_service),
):
    """
    **Refresh access token**

    When your access token expires, use this endpoint with the refresh token
    to get a new access token without re-authenticating.
    """
    refresh_token_value = request.refresh_token

    if not refresh_token_value:
        logger.warning("Refresh token endpoint called without token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required",
        )

    # Refresh tokens
    result = await auth_service.refresh_access_token(refresh_token_value)

    if not result:
        logger.warning("Failed to refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, new_refresh_token = result

    return LoginResponseSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthServiceImp = Depends(get_auth_service),
):
    """
    **User logout**

    Revokes all refresh tokens for the user, effectively logging them out
    of all devices/sessions.

    **Requires:** Valid access token in Authorization header
    """
    await auth_service.revoke_user_tokens(current_user["user_id"])
    logger.info(f"User {current_user['user_id']} logged out")
    return {"message": "Successfully logged out"}


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    request: ForgotPasswordRequestSchema,
    auth_service: AuthServiceImp = Depends(get_auth_service),
    user_repo=Depends(get_user_repository),
):
    """
    **Request password reset**

    Sends a password reset code to the user's email address.
    For development, the code is returned in the response.
    """
    user = await user_repo.get_by_email(request.email)
    if not user:
        logger.warning(
            f"Password reset requested for non-existent email: {request.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    reset_code = await auth_service.create_password_reset_code(user.id)

    # Send email (mock in development)
    from app.adapters.services.email.messages import PasswordResetEmail

    await PasswordResetEmail(
        to=user.email, name=f"{user.first_name} {user.last_name}", code=reset_code
    ).send()

    return ForgotPasswordResponseSchema(
        message="Password reset code sent to email",
        email=request.email,
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    request: ResetPasswordRequestSchema,
    auth_service: AuthServiceImp = Depends(get_auth_service),
):
    """
    Reset password using reset code
    """
    logger.info(
        f"🔄 Starting password reset endpoint with code: {request.code[:30]}..."
    )

    # Validate passwords match
    if request.new_password != request.confirm_password:
        logger.warning("❌ Passwords do not match")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    logger.info(f"✅ Passwords match, proceeding with reset")

    # Call reset_password
    success = await auth_service.reset_password(request.code, request.new_password)

    if not success:
        logger.error("❌ Password reset failed - invalid or expired code")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    logger.info("✅ Password reset endpoint completed successfully")
    return ResetPasswordResponseSchema(
        message="Password successfully reset",
        success=True,
    )


@router.get("/me", response_model=UserResponseSchema, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    user_repo=Depends(get_user_repository),
):
    """
    **Get current authenticated user**

    Returns the profile information of the currently authenticated user.

    **Requires:** Valid access token
    """
    user = await user_repo.get_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponseSchema.from_orm(user)
