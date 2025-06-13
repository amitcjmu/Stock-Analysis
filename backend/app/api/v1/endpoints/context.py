"""
Context API Endpoints

Provides endpoints for managing user context including:
- Getting complete user context (user, client, engagement, session)
- Switching between available sessions
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.session_management_service import create_session_management_service
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase
from datetime import datetime

router = APIRouter(tags=["context"])

# Demo mode constants
DEMO_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEMO_USER_EMAIL = "demo@democorp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")

@router.get(
    "/clients/default",
    response_model=dict,
    summary="Get default client",
    description="Get the default client for the current user or demo client if none is set."
)
async def get_default_client(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    try:
        service = create_session_management_service(db)
        context = await service.get_user_context(current_user.id)
        if context and context.client:
            return context.client.model_dump()
    except Exception:
        pass  # fallback to demo

    # Fallback to demo client
    return {
        "id": str(DEMO_CLIENT_ID),
        "name": "Democorp",
        "is_demo": True
    }

@router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, and session."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserContext:
    try:
        service = create_session_management_service(db)
        context = await service.get_user_context(current_user.id)
        if context:
            return context
        # Raise an exception to fall through to the demo context creation
        raise ValueError("User context not found, falling back to demo.")
    except Exception:
        # Fallback to demo context
        now = datetime.utcnow()
        demo_client = ClientBase(
            id=DEMO_CLIENT_ID,
            name="Democorp",
            description="Demonstration Client",
            created_at=now,
            updated_at=now
        )
        demo_engagement = EngagementBase(
            id=DEMO_ENGAGEMENT_ID,
            name="Cloud Migration 2024",
            description="Demonstration Engagement",
            client_id=DEMO_CLIENT_ID,
            created_at=now,
            updated_at=now
        )
        demo_session = SessionBase(
            id=DEMO_SESSION_ID,
            name="Demo Session",
            description="Demonstration Session",
            engagement_id=DEMO_ENGAGEMENT_ID,
            is_default=True,
            created_by=DEMO_USER_ID,
            created_at=now,
            updated_at=now
        )
        return UserContext(
            user={"id": str(current_user.id), "email": current_user.email, "role": getattr(current_user, 'role', 'demo')},
            client=demo_client,
            engagement=demo_engagement,
            session=demo_session,
            available_sessions=[demo_session]
        )

@router.post(
    "/sessions/{session_id}/switch",
    response_model=UserContext,
    summary="Switch current session",
    description="Switch the user's current session to the specified session ID."
)
async def switch_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Switch the current user's active session.
    
    Args:
        session_id: The ID of the session to switch to
        
    Returns:
        Updated user context with the new session
    """
    try:
        service = create_session_management_service(db)
        context = await service.switch_session(current_user.id, session_id)
        return context
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
