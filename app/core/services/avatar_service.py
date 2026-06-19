import os
import logging
from uuid import UUID
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import base64
import binascii

from app.core.entities import UserAvatar
from app.adapters.repositories.avatar_repository import IAvatarRepository
from app.adapters.repositories.user_repository import UserRepositoryImp
from app.config.settings import settings

logger = logging.getLogger(__name__)

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


class AvatarService:
    """Avatar service for handling avatar operations"""

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(
        self,
        avatar_repo: IAvatarRepository,
        user_repo: UserRepositoryImp,
    ):
        self.avatar_repo = avatar_repo
        self.user_repo = user_repo
        self._logger = logger

    def _get_upload_dir(self, user_id: UUID) -> Path:
        """Get upload directory for user avatars"""
        upload_dir = Path(settings.UPLOAD_DIR) / "avatars" / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    def _validate_file(self, file: UploadFile) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file

        Returns:
            (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return (
                False,
                f"File type {file_ext} not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )

        # Check file size (will be checked when reading)
        return True, None

    async def upload_avatar(
        self, user_id: UUID, file: UploadFile
    ) -> tuple[bool, UserAvatar | str]:
        """
        Upload user avatar

        Args:
            user_id: User ID
            file: File to upload

        Returns:
            (success, UserAvatar or error_message)
        """
        try:
            self._logger.info(f"📤 Uploading avatar for user: {user_id}")

            # Verify user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return False, f"User not found: {user_id}"

            # Validate file
            is_valid, error = self._validate_file(file)
            if not is_valid:
                return False, error

            # Read file content
            file_content = await file.read()

            # Check file size
            if len(file_content) > self.MAX_FILE_SIZE:
                return (
                    False,
                    f"File size exceeds {self.MAX_FILE_SIZE / (1024*1024):.1f}MB limit",
                )

            # Get upload directory
            upload_dir = self._get_upload_dir(user_id)

            # Generate filename
            file_ext = Path(file.filename).suffix.lower()
            filename = f"{user_id}{file_ext}"
            file_path = upload_dir / filename

            self._logger.info(f"✅ File saved: {file_path}")

            # Delete old avatar if exists
            old_avatar = await self.avatar_repo.get_by_user_id(user_id)
            if old_avatar:
                old_file_path = Path(old_avatar.file_path)
                if old_file_path.exists():
                    old_file_path.unlink()
                    self._logger.info(f"🗑️ Old avatar deleted: {old_file_path}")

                await self.avatar_repo.delete(old_avatar.id)

            # Save file
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Create avatar entity
            avatar = UserAvatar(
                user_id=user_id,
                file_name=filename,
                file_path=str(file_path).replace("/app", ""),
                file_type=file.content_type or "image/jpeg",
                file_size=len(file_content),
            )

            # Save to database
            saved_avatar = await self.avatar_repo.create(avatar)

            self._logger.info(f"✅ Avatar uploaded successfully: {saved_avatar.id}")
            return True, saved_avatar

        except Exception as e:
            self._logger.error(f"❌ Error uploading avatar: {str(e)}", exc_info=True)
            return False, f"Error uploading avatar: {str(e)}"

    async def get_avatar(self, user_id: UUID) -> Optional[UserAvatar]:
        """Get user avatar"""
        self._logger.debug(f"🔍 Fetching avatar for user: {user_id}")

        avatar = await self.avatar_repo.get_by_user_id(user_id)
        if avatar:
            self._logger.info(f"✅ Avatar found: {avatar.id}")
        else:
            self._logger.debug(f"ℹ️ No avatar found for user: {user_id}")

        return avatar

    async def delete_avatar(self, user_id: UUID) -> tuple[bool, str]:
        """
        Delete user avatar

        Returns:
            (success, message)
        """
        try:
            self._logger.info(f"🗑️ Deleting avatar for user: {user_id}")

            avatar = await self.avatar_repo.get_by_user_id(user_id)
            if not avatar:
                return False, f"No avatar found for user: {user_id}"

            # Delete file
            file_path = Path(avatar.file_path)
            if file_path.exists():
                file_path.unlink()
                self._logger.info(f"✅ Avatar file deleted: {file_path}")

            # Delete from database
            await self.avatar_repo.delete(avatar.id)

            self._logger.info(f"✅ Avatar deleted successfully for user: {user_id}")
            return True, "Avatar deleted successfully"

        except Exception as e:
            self._logger.error(f"❌ Error deleting avatar: {str(e)}", exc_info=True)
            return False, f"Error deleting avatar: {str(e)}"

    async def get_avatar_url(self, user_id: UUID) -> Optional[str]:
        """
        Get avatar URL for user

        Returns:
            URL path or None if no avatar
        """
        avatar = await self.avatar_repo.get_by_user_id(user_id)
        if avatar:
            return f"/uploads/avatars/{user_id}/{avatar.file_name}"
        return None

    def _parse_base64_image(
        self, image_data: str
    ) -> tuple[bool, bytes | str, str, str]:
        """
        Parse base64 image string (with or without data URI prefix)

        Returns:
            (is_valid, file_bytes or error_msg, mime_type, file_ext)
        """
        mime_type = "image/jpeg"  # default fallback
        file_ext = ".jpg"

        # Handle data URI format: data:image/png;base64,<data>
        if image_data.startswith("data:"):
            try:
                header, raw_b64 = image_data.split(",", 1)
                # header looks like: data:image/png;base64
                mime_part = header.split(";")[0].replace("data:", "")
                mime_type = mime_part.strip().lower()

                if mime_type not in self.MIME_TO_EXT:
                    return (
                        False,
                        f"Unsupported image type '{mime_type}'. "
                        f"Allowed: {', '.join(self.MIME_TO_EXT.keys())}",
                        "",
                        "",
                    )

                file_ext = self.MIME_TO_EXT[mime_type]
            except ValueError:
                return False, "Invalid data URI format", "", ""
        else:
            raw_b64 = image_data

        # Decode base64
        try:
            # Add padding if necessary
            padding = 4 - len(raw_b64) % 4
            if padding != 4:
                raw_b64 += "=" * padding

            file_bytes = base64.b64decode(raw_b64)
        except binascii.Error as e:
            return False, f"Invalid base64 encoding: {str(e)}", "", ""

        return True, file_bytes, mime_type, file_ext

    async def upload_avatar_base64(
        self, user_id: UUID, image_data: str, file_name: str = "avatar"
    ) -> tuple[bool, UserAvatar | str]:
        try:
            self._logger.info(f"📤 Uploading base64 avatar for user: {user_id}")

            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return False, f"User not found: {user_id}"

            is_valid, result, mime_type, file_ext = self._parse_base64_image(image_data)
            if not is_valid:
                return False, result

            file_bytes: bytes = result  # type: ignore

            if len(file_bytes) > self.MAX_FILE_SIZE:
                return (
                    False,
                    f"File size exceeds {self.MAX_FILE_SIZE / (1024 * 1024):.1f}MB limit",
                )

            upload_dir = self._get_upload_dir(user_id)

            filename = f"{user_id}{file_ext}"
            file_path = upload_dir / filename

            # Delete old avatar BEFORE saving the new file
            old_avatar = await self.avatar_repo.get_by_user_id(user_id)
            if old_avatar:
                old_file_path = Path(old_avatar.file_path)

                if old_file_path.exists():
                    old_file_path.unlink()
                    self._logger.info(f"🗑️ Old avatar deleted: {old_file_path}")

                await self.avatar_repo.delete(old_avatar.id)

            # Now save new file
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            self._logger.info(f"✅ Base64 avatar file saved: {file_path}")

            avatar = UserAvatar(
                user_id=user_id,
                file_name=filename,
                file_path=str(file_path),
                file_type=mime_type,
                file_size=len(file_bytes),
            )

            saved_avatar = await self.avatar_repo.create(avatar)

            self._logger.info(
                f"✅ Base64 avatar uploaded successfully: {saved_avatar.id}"
            )
            return True, saved_avatar

        except Exception as e:
            self._logger.error(
                f"❌ Error uploading base64 avatar: {str(e)}",
                exc_info=True,
            )
            return False, f"Error uploading avatar: {str(e)}"
