from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.core.entities import UserStatus, RoleType


class UserAvatarSchema(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_type: str
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class RoleSchema(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    middle_name: Optional[str] = Field(None, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: EmailStr | None = None
    username: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=8)
    timezone: str = Field(..., min_length=1)


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    middle_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    timezone: Optional[str] = Field(None, min_length=1)


class UserResponseSchema(BaseModel):
    id: UUID
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    email: str | None = None
    is_email_verified: bool
    email_verified_at: Optional[datetime] = None
    is_terminal_setup_completed: bool
    is_courier_profile_completed: bool
    username: str
    status: UserStatus
    full_name: str
    timezone: str
    currency: str
    avatar: Optional[UserAvatarSchema] = None
    role: Optional[RoleSchema] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponseSchema(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    username: str
    phone_number: str
    status: UserStatus
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")


class UpdateStatusSchema(BaseModel):
    status: UserStatus


class UserVerifyEmailSchema(BaseModel):
    email: EmailStr


class EmailVerificationSchema(BaseModel):
    token: str = Field(..., min_length=1)
    # user_id: int = Field(..., gt=0) --- IGNORE ---


class EmailVerificationResponseSchema(BaseModel):
    message: str


class ResendCodeSchema(BaseModel):
    email: EmailStr
