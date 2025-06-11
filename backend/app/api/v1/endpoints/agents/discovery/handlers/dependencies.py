"""
Dependency analysis handler for discovery agent.

This module contains the dependency analysis endpoints for the discovery agent.
"""
import logging
from typing import Dict, Any, List, Optional

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_current_context
from app.db.session import get_db
from app.models.client_account import User
from app.services.crewai_flow_service import crewai_flow_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dependencies", tags=["dependencies"])

@router.post("/analyze")
async def analyze_dependencies(
    dependency_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Comprehensive dependency analysis using Dependency Intelligence Agent.
    
    Request body:
    {
        "assets": [...],
        "applications": [...],
        "user_context": {...}
    }
    """
    try:
        assets = dependency_request.get("assets", [])
        applications = dependency_request.get("applications", [])
        user_context = dependency_request.get("user_context", {})
        
        if not assets and not applications:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'assets' or 'applications' must be provided"
            )
        
        # Get the current user or fall back to demo user
        user = None
        if context and context.user_id:
            user = await db.get(User, context.user_id)
        
        # If no user is authenticated, use the demo user
        if not user:
            demo_user_result = await db.execute(
                select(User).where(User.email == 'demo@democorp.com')
            )
            user = demo_user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Demo user not configured. Please contact support."
                )
        
        # Initialize session service
        session_service = SessionManagementService(db)
        session = None
        
        # If we have a session ID, try to get the session
        if context.session_id:
            try:
                session = await session_service.get_session(context.session_id)
                logger.info(f"Found existing session for dependency analysis: {session.id if session else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting session {context.session_id} for dependency analysis: {e}")
        
        # If no session exists but we have client/engagement context, create a new one
        if not session and context.client_account_id and context.engagement_id:
            try:
                session = await session_service.create_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_name=f"Dependency Analysis - {context.client_account_id[:8]}",
                    description="Auto-created session for dependency analysis"
                )
                logger.info(f"Created new session for dependency analysis: {session.id}")
            except Exception as e:
                logger.error(f"Error creating session for dependency analysis: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create analysis session"
                )
        
        # Perform the dependency analysis with the session
        analysis_result = await crewai_flow_service.analyze_dependencies(
            assets=assets,
            applications=applications,
            user_context=user_context,
            user_id=str(user.id),
            client_id=context.client_account_id,
            engagement_id=context.engagement_id,
            session_id=str(session.id) if session else None
        )
        
        return {
            "status": "success",
            "result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error analyzing dependencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze dependencies: {str(e)}"
        )

@router.post("/process-feedback")
async def process_dependency_feedback(
    feedback_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process user feedback on dependency analysis for agent learning.
    
    Request body:
    {
        "feedback_type": "dependency_validation|conflict_resolution|impact_assessment",
        "dependency_id": "string",
        "original_analysis": {...},
        "user_correction": {...}
    }
    """
    try:
        feedback_type = feedback_request.get("feedback_type")
        dependency_id = feedback_request.get("dependency_id")
        original_analysis = feedback_request.get("original_analysis")
        user_correction = feedback_request.get("user_correction")
        
        if not all([feedback_type, dependency_id, original_analysis is not None, user_correction is not None]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: feedback_type, dependency_id, original_analysis, and user_correction are required"
            )
        
        # Process the feedback
        feedback_result = await crewai_flow_service.process_dependency_feedback(
            feedback_type=feedback_type,
            dependency_id=dependency_id,
            original_analysis=original_analysis,
            user_correction=user_correction
        )
        
        return {
            "status": "success",
            "result": feedback_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing dependency feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process dependency feedback: {str(e)}"
        )

@router.post("/analyze-tech-debt")
async def analyze_tech_debt(
    tech_debt_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyzes technical debt across the application portfolio using an agent.
    
    Request body:
    {
        "applications": [...],
        "dependencies": [...],
        "assessment_criteria": {...}
    }
    """
    try:
        applications = tech_debt_request.get("applications", [])
        dependencies = tech_debt_request.get("dependencies", [])
        assessment_criteria = tech_debt_request.get("assessment_criteria", {})
        
        if not applications and not dependencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'applications' or 'dependencies' must be provided"
            )
        
        # Analyze technical debt
        analysis_result = await crewai_flow_service.analyze_technical_debt(
            applications=applications,
            dependencies=dependencies,
            assessment_criteria=assessment_criteria
        )
        
        return {
            "status": "success",
            "result": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error analyzing technical debt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze technical debt: {str(e)}"
        )

@router.post("/process-tech-debt-feedback")
async def process_tech_debt_feedback(
    feedback_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process stakeholder feedback on tech debt risk tolerance and business requirements.
    
    Request body:
    {
        "feedback_type": "risk_tolerance|business_priority|migration_timeline",
        "risk_item_id": "string",
        "original_assessment": {...},
        "stakeholder_input": {...}
    }
    """
    try:
        feedback_type = feedback_request.get("feedback_type")
        risk_item_id = feedback_request.get("risk_item_id")
        original_assessment = feedback_request.get("original_assessment")
        stakeholder_input = feedback_request.get("stakeholder_input")
        
        if not all([feedback_type, risk_item_id, original_assessment is not None, stakeholder_input is not None]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: feedback_type, risk_item_id, original_assessment, and stakeholder_input are required"
            )
        
        # Process the tech debt feedback
        feedback_result = await crewai_flow_service.process_tech_debt_feedback(
            feedback_type=feedback_type,
            risk_item_id=risk_item_id,
            original_assessment=original_assessment,
            stakeholder_input=stakeholder_input
        )
        
        return {
            "status": "success",
            "result": feedback_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing tech debt feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process tech debt feedback: {str(e)}"
        )
