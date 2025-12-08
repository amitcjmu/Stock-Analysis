"""
Password Reset Service.

Handles the business logic for password reset flows including
token generation, validation, and password update.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.client_account.user import User
from app.services.auth_services.authentication_service import AuthenticationService
from app.services.auth_services.email_service import get_email_service

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for handling password reset operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.email_service = get_email_service()
        self.auth_service = AuthenticationService(db)

    def _generate_reset_token(self) -> Tuple[str, str]:
        """
        Generate a secure password reset token.

        Returns:
            Tuple of (plain_token, hashed_token)
            - plain_token: Sent to user via email
            - hashed_token: Stored in database
        """
        # Generate a cryptographically secure token
        plain_token = secrets.token_urlsafe(32)

        # Hash the token for storage (using SHA256)
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()

        return plain_token, hashed_token

    def _hash_token(self, token: str) -> str:
        """Hash a token for comparison with stored hash."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _mask_email(self, email: str) -> str:
        """Mask email for display (e.g., j***@example.com)."""
        if not email or "@" not in email:
            return "***@***"

        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "***"
        else:
            masked_local = local[0] + "***" + local[-1]

        return f"{masked_local}@{domain}"

    async def initiate_password_reset(
        self,
        email: str,
        reset_url_base: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Initiate password reset by generating token and sending email.

        Args:
            email: User's email address
            reset_url_base: Base URL for reset link (defaults to FRONTEND_URL)

        Returns:
            Tuple of (success, message)

        Note:
            Always returns success message even if email doesn't exist
            to prevent email enumeration attacks.
        """
        # Find user by email
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Don't reveal if email exists - always return generic message
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True, (
                "If an account exists with this email, "
                "you will receive a password reset link shortly."
            )

        if not user.is_active:
            logger.info(f"Password reset requested for inactive user: {email}")
            return True, (
                "If an account exists with this email, "
                "you will receive a password reset link shortly."
            )

        # Generate reset token
        plain_token, hashed_token = self._generate_reset_token()

        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        # Store hashed token in database
        user.password_reset_token = hashed_token
        user.password_reset_token_expires_at = expires_at

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save reset token for {email}: {e}")
            return False, "An error occurred. Please try again later."

        # Determine reset URL base
        url_base = reset_url_base or settings.FRONTEND_URL

        # Get user's name for email personalization
        user_name = None
        if user.first_name:
            user_name = user.first_name
        elif user.username:
            user_name = user.username

        # Send email with plain token
        email_sent = await self.email_service.send_password_reset_email(
            to_email=email,
            reset_token=plain_token,
            reset_url_base=url_base,
            user_name=user_name,
        )

        if not email_sent:
            # Clear token if email failed
            user.password_reset_token = None
            user.password_reset_token_expires_at = None
            await self.db.commit()
            logger.error(f"Failed to send password reset email to {email}")
            return False, "Failed to send reset email. Please try again later."

        logger.info(f"Password reset email sent to {email}")
        return True, (
            "If an account exists with this email, "
            "you will receive a password reset link shortly."
        )

    async def validate_reset_token(self, token: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a password reset token.

        Args:
            token: Plain text token from URL

        Returns:
            Tuple of (valid, message, masked_email)
        """
        hashed_token = self._hash_token(token)

        # Find user with this token
        stmt = select(User).where(User.password_reset_token == hashed_token)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("Invalid password reset token attempted")
            return False, "Invalid or expired reset link.", None

        # Check expiration
        if not user.password_reset_token_expires_at:
            return False, "Invalid or expired reset link.", None

        if datetime.now(timezone.utc) > user.password_reset_token_expires_at:
            # Clear expired token
            user.password_reset_token = None
            user.password_reset_token_expires_at = None
            await self.db.commit()
            logger.info(f"Expired reset token used for {user.email}")
            return False, "This reset link has expired. Please request a new one.", None

        masked_email = self._mask_email(user.email)
        return True, "Token is valid.", masked_email

    async def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user's password using valid token.

        Args:
            token: Plain text token from URL
            new_password: New password to set

        Returns:
            Tuple of (success, message)
        """
        hashed_token = self._hash_token(token)

        # Find user with this token
        stmt = select(User).where(User.password_reset_token == hashed_token)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("Invalid password reset token used for password reset")
            return False, "Invalid or expired reset link."

        # Check expiration
        if not user.password_reset_token_expires_at:
            return False, "Invalid or expired reset link."

        if datetime.now(timezone.utc) > user.password_reset_token_expires_at:
            user.password_reset_token = None
            user.password_reset_token_expires_at = None
            await self.db.commit()
            return False, "This reset link has expired. Please request a new one."

        # Hash new password
        password_hash = self.auth_service.get_password_hash(new_password)

        # Update password and clear reset token
        user.password_hash = password_hash
        user.password_reset_token = None
        user.password_reset_token_expires_at = None

        try:
            await self.db.commit()
            logger.info(f"Password successfully reset for {user.email}")
            return (
                True,
                "Your password has been reset successfully. You can now log in.",
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to reset password for {user.email}: {e}")
            return False, "An error occurred. Please try again later."
