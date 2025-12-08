"""
Password Reset Schemas
Pydantic schemas for password reset functionality.
"""

from typing import Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: str = Field(
        ...,
        description="User's email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    reset_url_base: Optional[str] = Field(
        None,
        description="Base URL for reset link (defaults to FRONTEND_URL from config)",
    )


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response."""

    status: str
    message: str
    email_sent: bool = False


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request (with token)."""

    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(
        ..., min_length=8, description="New password (minimum 8 characters)"
    )
    confirm_password: str = Field(..., description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        # Check for at least one letter and one number for security
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one number")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ResetPasswordResponse(BaseModel):
    """Schema for password reset response."""

    status: str
    message: str


class ValidateResetTokenRequest(BaseModel):
    """Schema for validating reset token."""

    token: str = Field(..., description="Password reset token to validate")


class ValidateResetTokenResponse(BaseModel):
    """Schema for reset token validation response."""

    status: str
    valid: bool
    message: str
    email: Optional[str] = None  # Masked email for display
