"""
Session Management API Endpoints

Provides endpoints for managing data import sessions, including:
- Creating and updating sessions
- Setting default sessions
- Merging sessions
- Listing sessions for an engagement
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.session_management_service import SessionManagementService, create_session_management_service
from app.models.data_import_session import SessionType, SessionStatus
from app.schemas.session import Session, SessionCreate, SessionUpdate, SessionList
from app.api.v1.auth.auth_utils import get_current_user
from app.models import User

router = APIRouter(tags=["sessions"])


@router.post(
    "",
    response_model=Session,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new data import session with the provided details.",
)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new data import session.
    
    Args:
        client_account_id: The ID of the client account
        engagement_id: The ID of the engagement
        session_name: Optional custom session name (auto-generated if not provided)
        session_display_name: Optional user-friendly display name
        description: Optional session description
        is_default: Whether this should be the default session for the engagement
        session_type: Type of session (data_import, validation_run, etc.)
        auto_created: Whether this session was auto-created
        metadata: Optional metadata for the session
        
    Returns:
        The created session
    """
    service = create_session_management_service(db)
    try:
        # Convert Pydantic model to dict and add created_by
        session_data_dict = session_data.model_dump()
        session_data_dict['created_by'] = current_user.id
        
        # Remove fields that the service doesn't accept
        service_fields = {
            'client_account_id', 'engagement_id', 'session_name', 'session_display_name',
            'description', 'is_default', 'session_type', 'auto_created', 'metadata', 'created_by'
        }
        filtered_data = {k: v for k, v in session_data_dict.items() if k in service_fields}
        
        # Create the session using the service
        db_session = await service.create_session(**filtered_data)
        
        # Convert SQLAlchemy model to Pydantic model
        return Session.model_validate(db_session, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{session_id}",
    response_model=Session,
    summary="Get session by ID",
    description="Retrieve a session by its ID.",
)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a session by ID.
    
    Args:
        session_id: The ID of the session to retrieve
        
    Returns:
        The requested session
    """
    service = create_session_management_service(db)
    session = await service.get_session(str(session_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return session


@router.get(
    "/engagements/{engagement_id}/default",
    response_model=Session,
    summary="Get default session for engagement",
    description="Retrieve the default session for an engagement.",
)
async def get_default_session(
    engagement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the default session for an engagement.
    
    Args:
        engagement_id: The ID of the engagement
        
    Returns:
        The default session, or 404 if none exists
    """
    service = create_session_management_service(db)
    session = await service.get_default_session(str(engagement_id))
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No default session found for engagement {engagement_id}"
        )
    return session


@router.post(
    "/{source_session_id}/merge/{target_session_id}",
    response_model=Session,
    summary="Merge sessions",
    description="Merge data from one session into another.",
)
async def merge_sessions(
    source_session_id: UUID,
    target_session_id: UUID,
    merge_metadata: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Merge data from one session into another.
    
    Args:
        source_session_id: The ID of the session to merge from
        target_session_id: The ID of the session to merge into
        merge_metadata: Optional metadata about the merge
        
    Returns:
        The target session with merged data
    """
    service = create_session_management_service(db)
    try:
        session = await service.merge_sessions(
            str(source_session_id),
            str(target_session_id),
            merge_metadata=merge_metadata
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/engagement/{engagement_id}",
    response_model=List[Session],
    summary="List sessions for engagement",
    description="List all sessions for a specific engagement, optionally filtered by status.",
)
async def list_sessions(
    engagement_id: UUID,
    status: Optional[SessionStatus] = None,
    limit: Optional[int] = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all sessions for an engagement.
    
    Args:
        engagement_id: The ID of the engagement
        status: Optional status filter
        limit: Maximum number of sessions to return
        
    Returns:
        List of sessions
    """
    service = create_session_management_service(db)
    sessions = await service.get_sessions_for_engagement(
        engagement_id=str(engagement_id),
        status=status.value if status else None,
        limit=limit
    )
    return [Session.model_validate(session, from_attributes=True) for session in sessions]
