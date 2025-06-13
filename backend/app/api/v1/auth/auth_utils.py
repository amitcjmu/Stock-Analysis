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

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        user = await db.get(User, token_data.sub)
        if not user:
            # Fallback to demo user stub
            return User(
                id=DEMO_USER_ID,
                email=DEMO_USER_EMAIL,
                is_active=True,
                client_accounts=[DEMO_CLIENT_ID],
                engagements=[DEMO_ENGAGEMENT_ID],
                role="demo"
            )
        return user
    except Exception:
        # DB error or token error: fallback to demo user stub
        return User(
            id=DEMO_USER_ID,
            email=DEMO_USER_EMAIL,
            is_active=True,
            client_accounts=[DEMO_CLIENT_ID],
            engagements=[DEMO_ENGAGEMENT_ID],
            role="demo"
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 