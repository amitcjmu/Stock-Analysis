"""
JWT Authentication Service
Handles JWT token creation, validation, and management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


class JWTService:
    """Service for JWT token operations."""

    def __init__(self):
        try:
            self.secret_key = settings.SECRET_KEY
            self.algorithm = settings.ALGORITHM
            self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

            if not self.secret_key:
                raise ValueError("SECRET_KEY is not configured")

        except Exception as e:
            logger.error(f"JWT Service initialization error: {e}")
            raise

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token with expiration."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        try:
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != "access":
                logger.error(
                    f"❌ [JWT] Invalid token type: {payload.get('type')} (expected 'access')"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            # Normal occurrence - don't log expired tokens
            return None
        except jwt.InvalidTokenError:
            # Normal occurrence - don't log invalid tokens
            return None
        except Exception as e:
            logger.error(f"❌ [JWT] Token verification error: {e}", exc_info=True)
            return None

    def get_token_metadata(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token metadata with full verification for security."""
        # Security fix: Always verify tokens - removed unverified decode
        return self.verify_token(token)

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired with proper verification."""
        # Security fix: Use verified token decode instead of unverified
        payload = self.verify_token(token)
        if not payload:
            return True  # Invalid tokens are considered expired

        exp = payload.get("exp")
        if exp:
            return datetime.utcnow() > datetime.fromtimestamp(exp)
        return True

    def get_token_remaining_time(self, token: str) -> Optional[int]:
        """Get remaining time in seconds for a token with proper verification."""
        # Security fix: Use verified token decode instead of unverified
        payload = self.verify_token(token)
        if not payload:
            return None  # Invalid tokens have no remaining time

        exp = payload.get("exp")
        if exp:
            remaining = datetime.fromtimestamp(exp) - datetime.utcnow()
            return max(0, int(remaining.total_seconds()))
        return None

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token with longer expiration (7 days).
        Refresh tokens are used to obtain new access tokens.
        """
        to_encode = data.copy()
        # Refresh tokens expire after 7 days
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

        try:
            token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT refresh token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != "refresh":
                logger.error(
                    f"❌ [JWT] Invalid token type: {payload.get('type')} (expected 'refresh')"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Refresh token expired")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Invalid refresh token")
            return None
        except Exception as e:
            logger.error(
                f"❌ [JWT] Refresh token verification error: {e}", exc_info=True
            )
            return None
