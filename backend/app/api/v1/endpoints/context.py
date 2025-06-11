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
from app.schemas.context import UserContext

router = APIRouter(prefix="/context", tags=["context"])

@router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, and session."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the complete context for the current user.
    
    Returns:
        User context including client, engagement, and session info
    """
    try:
        service = create_session_management_service(db)
        context = await service.get_user_context(current_user.id)
        return context
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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
