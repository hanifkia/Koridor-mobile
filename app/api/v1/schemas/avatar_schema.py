from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime


class AvatarUploadResponse(BaseModel):
    """Avatar upload response"""

    id: UUID
    user_id: UUID
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class AvatarBase64UploadRequest(BaseModel):
    image_data: str  # base64 encoded image, with or without data URI prefix
    file_name: str = "avatar"  # optional hint for extension detection

    @field_validator("image_data")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        # Accept both raw base64 and data URI format
        # data:image/png;base64,iVBORw0KGgo...
        if not v:
            raise ValueError("image_data cannot be empty")
        return v


class AvatarResponse(BaseModel):
    """Avatar response"""

    id: UUID
    user_id: UUID
    file_name: str
    file_type: str
    file_size: int
    url: str | None = None

    class Config:
        from_attributes = True


class AvatarDeleteResponse(BaseModel):
    """Avatar delete response"""

    success: bool
    message: str
