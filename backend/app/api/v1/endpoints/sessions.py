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
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    Session,
    SessionList
)
from app.services.discovery_flow_service import DiscoveryFlowService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=Session)
async def create_session(
    request: SessionCreate,
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
            "id": context.session_id,
            "session_name": getattr(request, 'session_name', 'deprecated_session'),
            "session_display_name": getattr(request, 'session_display_name', 'Deprecated Session'),
            "session_type": getattr(request, 'session_type', 'data_import'),
            "engagement_id": context.engagement_id,
            "client_account_id": context.client_account_id,
            "is_default": False,
            "status": "active",
            "auto_created": True,
            "created_by": context.user_id or "anonymous",
            "created_at": "2025-01-22T00:00:00Z",
            "updated_at": "2025-01-22T00:00:00Z",
            "migration_notice": "Use POST /api/v2/discovery-flows/ for new development"
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    context: dict = Depends(get_current_context)
):
    """
    DEPRECATED: Legacy session endpoint.
    Use V2 Discovery Flow API instead: /api/v2/discovery-flows/
    
    This endpoint provides migration guidance for existing clients.
    """
    try:
        logger.warning("⚠️ Legacy sessions endpoint accessed - recommend V2 migration")
        
        # Initialize V2 services for migration data
        flow_repo = DiscoveryFlowRepository(db, context.get('client_account_id'))
        flow_service = DiscoveryFlowService(flow_repo)
        
        # Get all flows for migration guidance
        flows = await flow_service.get_all_flows()
        
        # Convert to legacy session format for backward compatibility
        legacy_sessions = []
        for flow in flows:
            legacy_sessions.append({
                "id": flow.flow_id,  # Use flow_id as session id
                "session_id": flow.flow_id,  # Deprecated field
                "status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                "migration_note": "Use V2 API: /api/v2/discovery-flows/"
            })
        
        return {
            "success": True,
            "data": legacy_sessions,
            "deprecation_warning": {
                "message": "This endpoint is deprecated. Use V2 Discovery Flow API.",
                "new_endpoint": "/api/v2/discovery-flows/",
                "migration_guide": "Replace session_id with flow_id in all requests"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get legacy sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get sessions - consider migrating to V2 API"
        }

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    context: dict = Depends(get_current_context)
):
    """
    DEPRECATED: Legacy session detail endpoint.
    Use V2 Discovery Flow API instead: /api/v2/discovery-flows/{flow_id}
    """
    try:
        logger.warning(f"⚠️ Legacy session detail endpoint accessed: {session_id}")
        
        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(db, context.get('client_account_id'))
        flow_service = DiscoveryFlowService(flow_repo)
        
        # Try to get flow by ID (treating session_id as flow_id)
        flow = await flow_service.get_flow(session_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}. Use V2 API: /api/v2/discovery-flows/{session_id}"
            )
        
        # Get flow summary
        flow_summary = await flow_service.get_flow_summary(session_id)
        
        return {
            "success": True,
            "data": {
                "id": flow.flow_id,
                "session_id": flow.flow_id,  # Deprecated field
                "flow_id": flow.flow_id,  # New field
                "status": flow.status,
                "current_phase": flow.current_phase,
                "progress_percentage": flow.progress_percentage,
                "summary": flow_summary,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
            },
            "deprecation_warning": {
                "message": "This endpoint is deprecated. Use V2 Discovery Flow API.",
                "new_endpoint": f"/api/v2/discovery-flows/{session_id}",
                "migration_guide": "Replace session_id with flow_id in all requests"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get legacy session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session - consider migrating to V2 API: {str(e)}"
        )

@router.put("/{session_id}", response_model=Session)
async def update_session(
    session_id: str,
    request: SessionUpdate,
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
            "id": session_id,
            "session_name": "deprecated_session",
            "session_display_name": "Deprecated Session",
            "session_type": "data_import",
            "engagement_id": context.engagement_id,
            "client_account_id": context.client_account_id,
            "is_default": False,
            "status": "active",
            "auto_created": True,
            "created_by": context.user_id or "anonymous",
            "created_at": "2025-01-22T00:00:00Z",
            "updated_at": "2025-01-22T00:00:00Z",
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

@router.get("/", response_model=SessionList)
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
