"""
Status handler for discovery agent.

This module contains the status-related endpoints for the discovery agent.
"""
import logging
from typing import Optional, Dict, Any

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.services.crewai_flow_service import crewai_flow_service
from app.services.session_management_service import SessionManagementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/agent-status")
async def get_agent_status(
    page_context: Optional[str] = None,
    engagement_id: Optional[str] = None,
    client_id: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Returns the status of the active discovery flow with session context.
    
    Args:
        page_context: The context of the page making the request (e.g., 'data-import', 'dependencies')
        engagement_id: Optional engagement ID to scope the data
        client_id: Optional client ID to scope the data
        session_id: Optional specific session ID to get status for
    """
    from app.services.crewai_flow_service import crewai_flow_service
    from app.services.session_management_service import SessionManagementService
    
    # Ensure we have a valid page context
    page_context = page_context or "data-import"
    session_service = SessionManagementService(db)
    
    try:
        # Get the current user's session context if available
        user = None
        
        # If no user is authenticated, use the demo user
        if not context or not context.user_id:
            # Get the demo user (email: demo@democorp.com)
            from sqlalchemy import select
            demo_user_result = await db.execute(
                select(User).where(User.email == 'demo@democorp.com')
            )
            user = demo_user_result.scalar_one_or_none()
            
            if not user:
                logger.warning("Demo user not found in database")
                return {
                    "status": "error",
                    "message": "Demo user not configured. Please contact support.",
                    "session_id": None,
                    "workflow_state": None,
                    "available_clients": [],
                    "available_engagements": [],
                    "available_sessions": []
                }
        else:
            # Get the authenticated user
            user = await db.get(User, context.user_id)
            
        if not user:
            return {
                "status": "error",
                "message": "User not found",
                "session_id": None,
                "workflow_state": None,
                "available_clients": [],
                "available_engagements": [],
                "available_sessions": []
            }
            
        # Initialize session and workflow state
        session = None
        workflow_state = {
            "status": "idle",
            "current_step": None,
            "progress": 0,
            "message": "No active workflow"
        }
        
        # Try to get the session if session_id is provided
        if session_id:
            try:
                session = await session_service.get_session(session_id)
                logger.info(f"Found existing session: {session.id if session else 'None'}")
                
                if session:
                    # Get the flow state for this session
                    flow_state = crewai_flow_service.get_flow_state(session_id)
                    if flow_state:
                        workflow_state = {
                            "status": getattr(flow_state, 'status', 'active'),
                            "current_step": getattr(flow_state, 'current_phase', None),
                            "progress": getattr(flow_state, 'progress_percentage', 0),
                            "message": getattr(flow_state, 'status_message', 'Workflow in progress')
                        }
            except Exception as e:
                logger.warning(f"Error getting session {session_id}: {e}")
        
        # Get available clients, engagements, and sessions (simplified for now)
        available_clients = []
        available_engagements = []
        available_sessions = []
        
        # Prepare the response
        response = {
            "status": "success",
            "session_id": str(session.id) if session and hasattr(session, 'id') else None,
            "workflow_state": workflow_state,
            "available_clients": available_clients,
            "available_engagements": available_engagements,
            "available_sessions": available_sessions
        }
        
        logger.info(f"Returning status response for session: {response['session_id']}")
        return response
        
    except Exception as e:
        logger.exception(f"Error getting agent status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )

# Health check endpoint
@router.get("/health")
async def agent_discovery_health():
    """Health check for agent discovery endpoints."""
    return {
        "status": "healthy",
        "service": "agent_discovery",
        "version": "1.0.0"
    }
