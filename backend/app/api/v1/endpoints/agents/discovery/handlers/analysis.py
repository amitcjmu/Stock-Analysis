"""
Analysis handler for discovery agent.

This module contains the analysis-related endpoints for the discovery agent.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_current_context
from app.db.session import get_db
from app.models.client_account import User
from app.services.crewai_flow_service import crewai_flow_service
from app.services.session_management_service import SessionManagementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/agent-analysis")
async def agent_analysis(
    analysis_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Multi-agent data analysis for different page contexts and analysis types.
    Enhanced with multi-tenant context awareness.
    
    Request body:
    {
        "data_source": {
            "file_data": [...],
            "metadata": {...},
            "upload_context": {...}
        },
        "analysis_type": "data_source_analysis",
        "page_context": "data-import"
    }
    OR for dependency context:
    {
        "data_context": {
            "dependency_analysis": {...},
            "cross_app_dependencies": [...],
            "impact_summary": {...}
        },
        "analysis_type": "dependency_mapping",
        "page_context": "dependencies"
    }
    """
    try:
        # Get the current user
        user = await db.get(User, context.user_id) if context and context.user_id else None
        
        # If no user is authenticated, use the demo user
        if not user:
            from sqlalchemy import select
            demo_user_result = await db.execute(
                select(User).where(User.email == 'demo@democorp.com')
            )
            user = demo_user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Demo user not configured. Please contact support."
                )
        
        # Get the page context and analysis type
        page_context = analysis_request.get("page_context", "data-import")
        analysis_type = analysis_request.get("analysis_type")
        
        if not analysis_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: analysis_type"
            )
        
        # Initialize session service
        session_service = SessionManagementService(db)
        session = None
        
        # If we have a session ID, try to get the session
        if context.session_id:
            try:
                session = await session_service.get_session(context.session_id)
                logger.info(f"Found existing session: {session.id if session else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting session {context.session_id}: {e}")
        
        # If no session exists and we have client/engagement context, create a new one
        if not session and context.client_account_id and context.engagement_id:
            try:
                session = await session_service.create_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_name=f"Analysis Session - {analysis_type}",
                    description=f"Auto-created session for {analysis_type} analysis"
                )
                logger.info(f"Created new session: {session.id}")
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create analysis session"
                )
        elif not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID or client/engagement context is required for analysis"
            )
        
        # Process the analysis request based on the analysis type
        if analysis_type == "data_source_analysis":
            result = await _process_data_source_analysis(
                analysis_request, session, page_context, context
            )
        elif analysis_type == "dependency_mapping":
            result = await _process_dependency_mapping(
                analysis_request, session, page_context, context
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported analysis type: {analysis_type}"
            )
        
        return {
            "status": "success",
            "session_id": str(session.id),
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in agent analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process analysis: {str(e)}"
        )

async def _process_data_source_analysis(
    analysis_request: Dict[str, Any],
    session: Any,
    page_context: str,
    context: RequestContext
) -> Dict[str, Any]:
    """Process data source analysis request."""
    data_source = analysis_request.get("data_source")
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: data_source"
        )
    
    # Process the data source with the appropriate agent
    result = await crewai_flow_service.process_data_source(
        data_source=data_source,
        session_id=str(session.id),
        page_context=page_context,
        user_id=str(context.user_id) if context.user_id else None,
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )
    
    return result

async def _process_dependency_mapping(
    analysis_request: Dict[str, Any],
    session: Any,
    page_context: str,
    context: RequestContext
) -> Dict[str, Any]:
    """Process dependency mapping request."""
    data_context = analysis_request.get("data_context")
    if not data_context:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: data_context"
        )
    
    # Process the dependency mapping with the appropriate agent
    result = await crewai_flow_service.process_dependency_mapping(
        data_context=data_context,
        session_id=str(session.id),
        page_context=page_context,
        user_id=str(context.user_id) if context.user_id else None,
        client_id=context.client_account_id,
        engagement_id=context.engagement_id
    )
    
    return result
