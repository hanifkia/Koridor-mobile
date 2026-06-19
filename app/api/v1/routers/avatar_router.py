import logging
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.api.v1.schemas.avatar_schema import (
    AvatarUploadResponse,
    AvatarResponse,
    AvatarDeleteResponse,
    AvatarBase64UploadRequest,
)
from app.core.services.avatar_service import AvatarService
from app.config.dependencies import (
    get_avatar_service,
)
from app.config.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/avatars", tags=["Avatars"])


@router.post(
    "/upload", response_model=AvatarUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_avatar(
    file: UploadFile = File(
        ..., description="Avatar file (JPG, PNG, GIF, WebP max 5MB)"
    ),
    current_user: dict = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service),
) -> AvatarUploadResponse:
    """
    Upload user avatar

    - **file**: Image file (JPG, PNG, GIF, WebP)
    - **Max size**: 5MB
    """
    user_id = current_user["user_id"]

    logger.info(f"📤 Avatar upload request from user: {user_id}")

    success, result = await avatar_service.upload_avatar(user_id, file)

    if not success:
        logger.error(f"❌ Avatar upload failed: {result}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    logger.info(f"✅ Avatar uploaded successfully: {result.id}")
    return AvatarUploadResponse(
        id=result.id,
        user_id=result.user_id,
        file_name=result.file_name,
        file_type=result.file_type,
        file_size=result.file_size,
        created_at=result.created_at,
    )


@router.post(
    "/upload/base64",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_avatar_base64(
    payload: AvatarBase64UploadRequest,
    current_user: dict = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service),
) -> AvatarUploadResponse:
    """
    Upload user avatar as a base64 encoded image

    - **image_data**: Base64 string — raw or with data URI prefix
      (`data:image/png;base64,<data>`)
    - **file_name**: Optional filename hint
    - **Supported types**: JPG, PNG, GIF, WebP
    - **Max size**: 5MB
    """
    user_id = current_user["user_id"]

    logger.info(f"📤 Base64 avatar upload request from user: {user_id}")

    success, result = await avatar_service.upload_avatar_base64(
        user_id,
        payload.image_data,
        payload.file_name,
    )

    if not success:
        logger.error(f"❌ Base64 avatar upload failed: {result}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    logger.info(f"✅ Base64 avatar uploaded successfully: {result.id}")
    return AvatarUploadResponse(
        id=result.id,
        user_id=result.user_id,
        file_name=result.file_name,
        file_type=result.file_type,
        file_size=result.file_size,
        created_at=result.created_at,
    )


@router.get("/", response_model=AvatarResponse)
async def get_avatar(
    avatar_service: AvatarService = Depends(get_avatar_service),
    current_user: dict = Depends(get_current_user),
) -> AvatarResponse:
    """Get user avatar metadata"""
    user_id = current_user["user_id"]
    logger.info(f"🔍 Getting avatar for user: {user_id}")

    avatar = await avatar_service.get_avatar(user_id)

    if not avatar:
        logger.warning(f"❌ Avatar not found for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar not found for user: {user_id}",
        )

    url = await avatar_service.get_avatar_url(user_id)

    logger.info(f"✅ Avatar retrieved: {avatar.id}")
    return AvatarResponse(
        id=avatar.id,
        user_id=avatar.user_id,
        file_name=avatar.file_name,
        file_type=avatar.file_type,
        file_size=avatar.file_size,
        url=url,
    )


@router.get("/download")
async def download_avatar(
    avatar_service: AvatarService = Depends(get_avatar_service),
    current_user: dict = Depends(get_current_user),
) -> FileResponse:
    """Download user avatar file"""
    user_id = current_user["user_id"]
    logger.info(f"📥 Downloading avatar for user: {user_id}")

    avatar = await avatar_service.get_avatar(user_id)

    if not avatar:
        logger.warning(f"❌ Avatar not found for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avatar not found for user: {user_id}",
        )

    logger.info(f"✅ Avatar file served: {avatar.file_path}")
    return FileResponse(
        path=avatar.file_path,
        filename=avatar.file_name,
        media_type=avatar.file_type,
    )


@router.delete("/", response_model=AvatarDeleteResponse)
async def delete_avatar(
    current_user: dict = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service),
) -> AvatarDeleteResponse:
    """Delete user avatar"""
    # Verify user is deleting their own avatar
    user_id = current_user["user_id"]

    logger.info(f"🗑️ Deleting avatar for user: {user_id}")

    success, message = await avatar_service.delete_avatar(user_id)

    if not success:
        logger.error(f"❌ Avatar deletion failed: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    logger.info(f"✅ Avatar deleted successfully: {user_id}")
    return AvatarDeleteResponse(success=success, message=message)
