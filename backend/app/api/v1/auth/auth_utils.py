"""
Authentication Utilities
"""

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.client_account import User
from app.services.auth_services.jwt_service import JWTService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False
)

# Demo mode constants - Fixed UUIDs for frontend fallback
DEMO_USER_ID = UUID("33333333-3333-3333-3333-333333333333")
DEMO_USER_EMAIL = "demo@demo-corp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_FLOW_ID = UUID("44444444-4444-4444-4444-444444444444")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db=Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Bug #684 debugging: Log token reception
        logger.info(
            f"🔐 [AUTH] Received token for validation (length: {len(token) if token else 0})"
        )

        # Use JWT service for token validation
        try:
            jwt_service = JWTService()
            logger.info("🔐 [AUTH] JWT service initialized, verifying token...")
            payload = jwt_service.verify_token(token)

            if payload:
                logger.info(
                    f"🔐 [AUTH] Token verified successfully, payload keys: {list(payload.keys())}"
                )
            else:
                logger.warning(
                    "⚠️ [AUTH] Token verification returned None (invalid/expired token)"
                )

        except Exception as jwt_error:
            logger.error(f"❌ [AUTH] JWT service error: {jwt_error}")
            raise credentials_exception

        if payload is None:
            logger.warning("⚠️ [AUTH] Payload is None, raising credentials_exception")
            raise credentials_exception

        user_id_str = payload.get("sub")
        if user_id_str is None:
            logger.warning("⚠️ [AUTH] No 'sub' claim in token payload")
            raise credentials_exception

        logger.info(f"🔐 [AUTH] Extracted user_id from token: {user_id_str}")

        try:
            user_id = UUID(user_id_str)

            # Find user by ID with eager loading of associations
            logger.info(f"🔐 [AUTH] Querying database for user_id: {user_id}")
            result = await db.execute(
                select(User)
                .where(User.id == user_id)
                .options(selectinload(User.user_associations))
            )
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"⚠️ [AUTH] User not found in database: {user_id}")
                raise credentials_exception

            logger.info(
                f"✅ [AUTH] User found: {user.email}, is_active: {user.is_active}"
            )

            # Check if user is active
            if not user.is_active:
                logger.warning(f"⚠️ [AUTH] User account is inactive: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                )

            logger.info(f"✅ [AUTH] Authentication successful for user: {user.email}")
            return user

        except ValueError as ve:
            logger.error(
                f"❌ [AUTH] Invalid UUID format for user_id: {user_id_str}, error: {ve}"
            )
            raise credentials_exception

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTH] Unexpected authentication error: {e}", exc_info=True)
        raise credentials_exception


def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme_optional)], db=Depends(get_db)
) -> Optional[User]:
    """
    Optional version of get_current_user that returns None if no token provided.
    This is useful for endpoints that need to work for both authenticated and anonymous users.
    """
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        # If token is invalid, return None instead of raising
        return None
