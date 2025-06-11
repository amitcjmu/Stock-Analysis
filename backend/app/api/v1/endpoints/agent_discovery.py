"""
Agent Discovery API Router

This module serves as the main entry point for agent discovery endpoints.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.services.crewai_flow_service import crewai_flow_service
from app.services.session_management_service import SessionManagementService

logger = logging.getLogger(__name__)

# Create the main router
router = APIRouter()

@router.get("/agent-status")
async def get_agent_status(
    page_context: str = "data-import",
    engagement_id: str = None,
    client_id: str = None,
    session_id: str = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> dict:
    """
    Returns the status of the active discovery flow with session context.
    
    Args:
        page_context: The context of the page making the request (e.g., 'data-import', 'dependencies')
        engagement_id: Optional engagement ID to scope the data
        client_id: Optional client ID to scope the data
        session_id: Optional specific session ID to get status for
    """
    session_service = SessionManagementService(db)
    
    try:
        # Get the current user's session context if available
        user = None
        
        # If no user is authenticated, use the demo user
        if not context or not context.user_id:
            # Get the demo user (email: demo@democorp.com)
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
            user_result = await db.execute(
                select(User).where(User.id == context.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Initialize session and workflow state
        session = None
        workflow_state = {
            "status": "idle",
            "current_step": None,
            "progress": 0,
            "message": "No active workflow"
        }
        
        # If we have a session ID, try to get its state
        if session_id:
            try:
                logger.info(f"Looking up session with ID: {session_id}")
                # Try to get the session if it exists
                session = await session_service.get_session(session_id)
                logger.info(f"Session found: {session is not None}")
                
                if session:
                    logger.info(f"Getting flow state for session: {session_id}")
                    # Get the flow state for this session
                    flow_state = crewai_flow_service.get_flow_state(session_id)
                    logger.info(f"Flow state found: {flow_state is not None}")
                    
                    if flow_state:
                        workflow_state = {
                            "status": getattr(flow_state, 'status', 'active'),
                            "current_step": getattr(flow_state, 'current_phase', None),
                            "progress": getattr(flow_state, 'progress_percentage', 0),
                            "message": getattr(flow_state, 'status_message', 'Workflow in progress')
                        }
                        logger.info(f"Updated workflow state: {workflow_state}")
                    else:
                        logger.info("No flow state found for session")
                else:
                    logger.info(f"No session found with ID: {session_id}")
                    
            except Exception as e:
                logger.error(f"Error getting session or flow state for session_id {session_id}", exc_info=True)
        else:
            logger.info("No session ID provided, using default workflow state")
        
        # Prepare response with workflow state
        response = {
            "status": "success",
            "workflow_state": workflow_state,
            "session_id": str(session.id) if session and hasattr(session, 'id') else None,
            "available_clients": [],  # These will be populated by the frontend
            "available_engagements": [],  # These will be populated by the frontend
            "available_sessions": []  # These will be populated by the frontend
        }
        
        logger.info(f"Returning response with workflow state: {workflow_state['status']}, session_id: {response['session_id']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")
