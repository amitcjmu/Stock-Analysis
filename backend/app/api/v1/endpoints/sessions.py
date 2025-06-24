"""
Session Management Endpoints

⚠️ DEPRECATED NOTICE: Traditional session management is deprecated in favor of V2 Discovery Flow architecture.
These endpoints provide minimal compatibility but should be migrated to V2 API.

Use /api/v2/discovery-flows/ endpoints for new development.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.schemas.session_schemas import (
    SessionCreateRequest,
    SessionUpdateRequest,
    SessionResponse,
    SessionListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Create a new session
    
    Use V2 Discovery Flow API: POST /api/v2/discovery-flows/
    """
    logger.warning("⚠️ Deprecated endpoint used - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "session_id": context.session_id,
            "status": "created",
            "message": "Session created (deprecated - use V2 Discovery Flow API)",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "metadata": request.metadata or {},
            "migration_notice": "Use POST /api/v2/discovery-flows/ for new development"
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Get session by ID
    
    Use V2 Discovery Flow API: GET /api/v2/discovery-flows/{flow_id}
    """
    logger.warning(f"⚠️ Deprecated session lookup for {session_id} - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "session_id": session_id,
            "status": "unknown",
            "message": "Session lookup deprecated - use V2 Discovery Flow API",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "metadata": {},
            "migration_notice": f"Use GET /api/v2/discovery-flows/ to find flows for this context"
        }
        
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Update session
    
    Use V2 Discovery Flow API: PUT /api/v2/discovery-flows/{flow_id}
    """
    logger.warning(f"⚠️ Deprecated session update for {session_id} - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "session_id": session_id,
            "status": "updated",
            "message": "Session update deprecated - use V2 Discovery Flow API",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "metadata": request.metadata or {},
            "migration_notice": f"Use PUT /api/v2/discovery-flows/{{flow_id}} for updates"
        }
        
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Delete session
    
    Use V2 Discovery Flow API: DELETE /api/v2/discovery-flows/{flow_id}
    """
    logger.warning(f"⚠️ Deprecated session deletion for {session_id} - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "session_id": session_id,
            "status": "deleted",
            "message": "Session deletion deprecated - use V2 Discovery Flow API",
            "migration_notice": f"Use DELETE /api/v2/discovery-flows/{{flow_id}} for deletion"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: List sessions for current client account
    
    Use V2 Discovery Flow API: GET /api/v2/discovery-flows/
    """
    logger.warning("⚠️ Deprecated session listing - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "sessions": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "message": "Session listing deprecated - use V2 Discovery Flow API",
            "migration_notice": "Use GET /api/v2/discovery-flows/ to list flows for your context"
        }
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )

@router.get("/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Get session status
    
    Use V2 Discovery Flow API: GET /api/v2/discovery-flows/{flow_id}/status
    """
    logger.warning(f"⚠️ Deprecated session status lookup for {session_id} - migrate to V2 Discovery Flow API")
    
    try:
        # Minimal compatibility response
        return {
            "session_id": session_id,
            "status": "unknown",
            "current_phase": "unknown",
            "progress": 0,
            "message": "Session status lookup deprecated - use V2 Discovery Flow API",
            "migration_notice": f"Use GET /api/v2/discovery-flows/{{flow_id}}/status for real status"
        }
        
    except Exception as e:
        logger.error(f"Failed to get session status {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session status: {str(e)}"
        )
