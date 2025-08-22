"""
Authentication utilities for middleware components.
Provides user ID extraction and platform admin verification.
"""

import logging
from typing import Optional

from fastapi import Request

from ..security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


def extract_user_id(request: Request) -> Optional[str]:
    """Extract user ID from request headers or token."""
    # First check for explicit user ID headers
    user_id = (
        request.headers.get("X-User-ID")
        or request.headers.get("x-user-id")
        or request.headers.get("X-User-Id")
    )

    if user_id:
        return user_id

    # Extract from Authorization token if no explicit header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

        # Try JWT token first
        try:
            from app.services.auth_services.jwt_service import JWTService

            jwt_service = JWTService()
            payload = jwt_service.verify_token(token)
            if payload:
                return payload.get("sub")
        except Exception as jwt_error:
            logger.debug(f"JWT token verification failed in middleware: {jwt_error}")

        # Handle db-token format: db-token-{user_id}-{suffix} (backward compatibility)
        if token.startswith("db-token-"):
            try:
                # Remove the "db-token-" prefix
                token_without_prefix = token[9:]  # len("db-token-") = 9

                # Find the last hyphen to separate the suffix
                last_hyphen = token_without_prefix.rfind("-")
                if last_hyphen > 0:
                    # Extract UUID part (everything before the last hyphen)
                    user_uuid = token_without_prefix[:last_hyphen]
                    return user_uuid
            except Exception as e:
                logger.debug(f"Failed to parse db-token format: {e}")
                # Return None to continue with other token formats

    return None


async def check_platform_admin(user_id: str) -> bool:
    """Check if user is a platform administrator."""
    try:
        import uuid

        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.rbac import UserRole

        # Convert string to UUID if needed
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(
                safe_log_format(
                    "Invalid UUID format for user_id: {user_id}", user_id=user_id
                )
            )
            return False

        async with AsyncSessionLocal() as db:
            # First check if user has is_admin flag
            from app.models.client_account import User

            user_result = await db.execute(select(User).where(User.id == user_uuid))
            user = user_result.scalar_one_or_none()

            if user and user.is_admin:
                logger.info(
                    safe_log_format(
                        "User {user_id} is platform admin (is_admin=True)",
                        user_id=user_id,
                    )
                )
                return True

            # Also check UserRole for platform_admin role
            query = select(UserRole).where(
                and_(
                    UserRole.user_id == user_uuid,
                    UserRole.role_type == "platform_admin",
                    UserRole.is_active is True,
                )
            )
            result = await db.execute(query)
            role = result.scalar_one_or_none()

            if role:
                logger.info(
                    safe_log_format(
                        "Platform admin role confirmed for user {user_id}",
                        user_id=user_id,
                    )
                )
                return True
            else:
                logger.warning(
                    safe_log_format(
                        "No platform admin role found for user {user_id}",
                        user_id=user_id,
                    )
                )
                return False

    except Exception as e:
        logger.error(
            safe_log_format(
                "Error checking platform admin status for {user_id}: {e}",
                user_id=user_id,
                e=e,
            )
        )
        return False
