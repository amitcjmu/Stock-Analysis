"""
Authentication Utilities
"""
from typing import Annotated, Optional
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import get_db
from app.models.client_account import User
from app.schemas.auth_schemas import TokenPayload
from app.services.auth_services.jwt_service import JWTService

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

# Demo mode constants - Fixed UUIDs for frontend fallback
DEMO_USER_ID = UUID("33333333-3333-3333-3333-333333333333")
DEMO_USER_EMAIL = "demo@demo-corp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_FLOW_ID = UUID("44444444-4444-4444-4444-444444444444")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Use JWT service for token validation
        try:
            jwt_service = JWTService()
            payload = jwt_service.verify_token(token)
        except Exception as jwt_error:
            logger.error(f"JWT service error: {jwt_error}")
            raise credentials_exception
        
        if payload is None:
            raise credentials_exception
            
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        try:
            user_id = UUID(user_id_str)
            
            # Find user by ID
            user = await db.get(User, user_id)
            if user is None:
                raise credentials_exception
                
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
                
            return user
            
        except ValueError:
            raise credentials_exception
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception


def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_optional(token: Annotated[Optional[str], Depends(oauth2_scheme_optional)], db = Depends(get_db)) -> Optional[User]:
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