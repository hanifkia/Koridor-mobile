from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginResponseSchema(BaseModel):
    access_token: str = Field(..., description="JWT access token for API requests")
    token_type: str = Field("bearer", description="OAuth2 token type")
    expires_in: int = Field(3600, description="Token expiration in seconds")
    refresh_token: str = Field(
        ..., description="Refresh token for getting new access tokens"
    )


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str = Field(
        ..., description="Valid refresh token from login response"
    )


class ForgotPasswordRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordResponseSchema(BaseModel):
    message: str
    email: str


class ResetPasswordRequestSchema(BaseModel):
    code: str = Field(..., min_length=1, description="Password reset code from email")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")


class ResetPasswordResponseSchema(BaseModel):
    message: str
    success: bool
