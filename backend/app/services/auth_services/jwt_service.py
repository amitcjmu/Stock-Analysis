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
            logger.info(f"Created access token for user: {data.get('sub', 'unknown')}")
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
                logger.warning("Invalid token type")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging/logging)."""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Token decoding error: {e}")
            return None

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full verification."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp")
            if exp:
                return datetime.utcnow() > datetime.fromtimestamp(exp)
            return True
        except Exception:
            return True

    def get_token_remaining_time(self, token: str) -> Optional[int]:
        """Get remaining time in seconds for a token."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp")
            if exp:
                remaining = datetime.fromtimestamp(exp) - datetime.utcnow()
                return max(0, int(remaining.total_seconds()))
            return None
        except Exception:
            return None
