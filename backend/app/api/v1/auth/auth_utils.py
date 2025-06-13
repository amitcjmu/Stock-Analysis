"""
Authentication Utilities
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import get_db
from app.models.client_account import User
from app.schemas.auth_schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# Demo mode constants
DEMO_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEMO_USER_EMAIL = "demo@democorp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")
ADMIN_USER_ID = UUID("55555555-5555-5555-5555-555555555555")
ADMIN_USER_EMAIL = "admin@democorp.com"

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user_id = UUID(token_data.sub)
        
        user = await db.get(User, user_id)
        if user:
            return user

        # If user not found in DB, create a mock user object based on ID
        if user_id == ADMIN_USER_ID:
            mock_user = User(id=ADMIN_USER_ID, email=ADMIN_USER_EMAIL, is_active=True, is_mock=True)
            mock_user.role = "admin"
        else: # Default to regular demo user
            mock_user = User(id=DEMO_USER_ID, email=DEMO_USER_EMAIL, is_active=True, is_mock=True)
            mock_user.role = "demo"
            
        # Attach required relationship data to the mock object
        mock_user.client_accounts = [{"id": str(DEMO_CLIENT_ID), "name": "Democorp"}]
        mock_user.engagements = [{"id": str(DEMO_ENGAGEMENT_ID), "name": "Cloud Migration 2024"}]
        return mock_user

    except (JWTError, ValidationError, Exception):
        # Fallback for any error during token processing or DB access
        mock_user = User(id=DEMO_USER_ID, email=DEMO_USER_EMAIL, is_active=True, is_mock=True)
        mock_user.role = "demo"
        mock_user.client_accounts = [{"id": str(DEMO_CLIENT_ID), "name": "Democorp"}]
        mock_user.engagements = [{"id": str(DEMO_ENGAGEMENT_ID), "name": "Cloud Migration 2024"}]
        return mock_user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 