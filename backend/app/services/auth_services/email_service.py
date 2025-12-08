"""
Email Service using Resend API.

Handles transactional emails for authentication flows including
password reset and email verification.
"""

# flake8: noqa: E501
# HTML email templates contain inline CSS which requires long lines for readability

import logging
from typing import Optional

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails via Resend."""

    def __init__(self):
        """Initialize Resend with API key."""
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
        else:
            logger.warning(
                "RESEND_API_KEY not configured. Email sending will be disabled."
            )

    def _is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(settings.RESEND_API_KEY)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        reset_url_base: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """
        Send password reset email.

        Args:
            to_email: Recipient email address
            reset_token: The password reset token (unhashed)
            reset_url_base: Base URL for reset link (e.g., http://localhost:8081)
            user_name: Optional user's name for personalization

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._is_configured():
            logger.error(
                "Cannot send password reset email: RESEND_API_KEY not configured"
            )
            return False

        reset_url = f"{reset_url_base}/reset-password?token={reset_token}"
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">{greeting}</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
            We received a request to reset your password for your AI Modernize Platform account.
            Click the button below to create a new password:
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Reset Password
            </a>
        </div>

        <p style="font-size: 14px; color: #6b7280; margin-bottom: 10px;">
            This link will expire in <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes</strong>.
        </p>

        <p style="font-size: 14px; color: #6b7280; margin-bottom: 20px;">
            If you didn't request a password reset, you can safely ignore this email.
            Your password will remain unchanged.
        </p>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">

        <p style="font-size: 12px; color: #9ca3af; margin-bottom: 5px;">
            If the button doesn't work, copy and paste this link into your browser:
        </p>
        <p style="font-size: 12px; color: #667eea; word-break: break-all;">
            {reset_url}
        </p>
    </div>

    <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
        <p style="margin: 0;">AI Modernize Platform</p>
        <p style="margin: 5px 0 0 0;">This is an automated message. Please do not reply.</p>
    </div>
</body>
</html>
"""

        text_content = f"""
{greeting}

We received a request to reset your password for your AI Modernize Platform account.

Click the link below to create a new password:
{reset_url}

This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you didn't request a password reset, you can safely ignore this email.
Your password will remain unchanged.

---
AI Modernize Platform
This is an automated message. Please do not reply.
"""

        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [to_email],
                "subject": "Reset Your Password - AI Modernize Platform",
                "html": html_content,
                "text": text_content,
            }

            response = resend.Emails.send(params)

            # Resend SDK may return different response types depending on version
            # Handle both object with 'id' attribute and dict with 'id' key
            email_id = None
            if response:
                if hasattr(response, "id"):
                    email_id = response.id
                elif isinstance(response, dict) and "id" in response:
                    email_id = response["id"]

            if email_id:
                logger.info(
                    f"Password reset email sent successfully to {to_email}, "
                    f"email_id={email_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to send password reset email to {to_email}. "
                    f"Response type: {type(response)}, Response: {response}"
                )
                return False

        except Exception as e:
            logger.error(f"Error sending password reset email to {to_email}: {str(e)}")
            return False


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create EmailService singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
