"""
Learning handler for discovery agent.

This module contains the learning-related endpoints for the discovery agent.
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

router = APIRouter(prefix="/learning", tags=["learning"])

@router.post("/answer-clarification")
async def answer_agent_clarification(
    clarification_response: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    User responses to agent questions for learning and clarification.
    
    Request body:
    {
        "question_id": "uuid",
        "response": "user_answer",
        "response_type": "text|selection|multiple_choice",
        "page_context": "data-import"
    }
    """
    try:
        question_id = clarification_response.get("question_id")
        response = clarification_response.get("response")
        response_type = clarification_response.get("response_type", "text")
        page_context = clarification_response.get("page_context", "data-import")
        
        if not question_id or response is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: question_id and response are required"
            )
        
        # Initialize session service
        session_service = SessionManagementService(db)
        session = None
        
        # If we have a session ID, try to get the session
        if context and context.session_id:
            try:
                session = await session_service.get_session(context.session_id)
                logger.info(f"Found existing session for learning: {session.id if session else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting session {context.session_id} for learning: {e}")
        
        # If no session exists but we have client/engagement context, create a new one
        if not session and context and context.client_account_id and context.engagement_id:
            try:
                session = await session_service.create_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_name=f"Learning Session - {context.client_account_id[:8]}",
                    description="Auto-created session for agent learning"
                )
                logger.info(f"Created new session for learning: {session.id}")
            except Exception as e:
                logger.error(f"Error creating session for learning: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create learning session"
                )
        
        # Process the clarification response with the session
        result = await _process_agent_learning(
            question_id=question_id,
            response=response,
            response_type=response_type,
            page_context=page_context,
            db=db,
            context=context
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing clarification response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process clarification: {str(e)}"
        )

@router.post("/process-learning")
async def process_agent_learning(
    learning_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Agent learning from user corrections and feedback.
    
    Request body:
    {
        "learning_type": "field_mapping|data_classification|pattern_recognition|insight_feedback",
        "original_prediction": {...},
        "user_correction": {...},
        "context": {...},
        "page_context": "data-import"
    }
    """
    try:
        learning_type = learning_input.get("learning_type")
        original_prediction = learning_input.get("original_prediction")
        user_correction = learning_input.get("user_correction")
        context_data = learning_input.get("context", {})
        page_context = learning_input.get("page_context", "data-import")
        
        # Get the current user or fall back to demo user
        user = None
        if context and context.user_id:
            user = await db.get(User, context.user_id)
        
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
                logger.info(f"Found existing session for learning: {session.id if session else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting session {context.session_id} for learning: {e}")
        
        # If no session exists but we have client/engagement context, create a new one
        if not session and context.client_account_id and context.engagement_id:
            try:
                session = await session_service.create_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_name=f"Learning Session - {learning_type}",
                    description=f"Auto-created session for {learning_type} learning"
                )
                logger.info(f"Created new session for learning: {session.id}")
            except Exception as e:
                logger.error(f"Error creating session for learning: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create learning session"
                )
        elif not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID or client/engagement context is required for learning"
            )
        
        if not all([learning_type, original_prediction is not None, user_correction is not None]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: learning_type, original_prediction, and user_correction are required"
            )
        
        # Process the learning input
        result = await _apply_agent_learning(
            learning_type=learning_type,
            original_prediction=original_prediction,
            user_correction=user_correction,
            context=context,
            page_context=page_context,
            db=db
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing agent learning: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process learning: {str(e)}"
        )

async def _process_agent_learning(
    question_id: str,
    response: Any,
    response_type: str,
    page_context: str,
    db: AsyncSession,
    context: RequestContext
) -> Dict[str, Any]:
    """Process agent learning from user responses."""
    # Get the original question from the session or database
    # This is a simplified example - in a real implementation, you would retrieve the original question
    # from the database or session state
    original_question = {
        "id": question_id,
        "question": "Please provide additional context",
        "question_type": response_type,
        "context": {}
    }
    
    # Process the response based on the question type
    if response_type == "text":
        processed_response = {"text": str(response)}
    elif response_type == "selection":
        processed_response = {"selected_option": response}
    elif response_type == "multiple_choice":
        processed_response = {"selected_options": response if isinstance(response, list) else [response]}
    else:
        processed_response = {"raw_response": response}
    
    # Update the agent's knowledge based on the response
    # In a real implementation, this would involve updating the agent's memory or training data
    learning_result = {
        "question_id": question_id,
        "response": processed_response,
        "page_context": page_context,
        "timestamp": "2023-01-01T00:00:00Z",  # Use actual timestamp in production
        "user_id": str(context.user_id) if context.user_id else None
    }
    
    # Return the learning result
    return {
        "status": "processed",
        "learning_result": learning_result,
        "next_steps": ["Update agent knowledge base", "Continue with workflow"]
    }

async def _apply_agent_learning(
    learning_type: str,
    original_prediction: Dict[str, Any],
    user_correction: Dict[str, Any],
    context: Dict[str, Any],
    page_context: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Apply specific learning based on the type of correction."""
    # This is a simplified example - in a real implementation, you would have specific
    # learning logic for each learning type
    
    learning_result = {
        "learning_type": learning_type,
        "original_prediction": original_prediction,
        "user_correction": user_correction,
        "context": context,
        "page_context": page_context,
        "timestamp": "2023-01-01T00:00:00Z",  # Use actual timestamp in production
        "applied_changes": {},
        "next_steps": []
    }
    
    # Apply different learning based on the type
    if learning_type == "field_mapping":
        learning_result["applied_changes"] = {
            "field_mapping_updated": True,
            "original_field": original_prediction.get("field"),
            "corrected_field": user_correction.get("field")
        }
        learning_result["next_steps"].append("Update field mapping rules")
        
    elif learning_type == "data_classification":
        learning_result["applied_changes"] = {
            "data_classification_updated": True,
            "original_classification": original_prediction.get("classification"),
            "corrected_classification": user_correction.get("classification")
        }
        learning_result["next_steps"].append("Update data classification model")
        
    elif learning_type == "pattern_recognition":
        learning_result["applied_changes"] = {
            "pattern_recognized": True,
            "pattern_details": user_correction.get("pattern_details")
        }
        learning_result["next_steps"].append("Update pattern recognition model")
        
    elif learning_type == "insight_feedback":
        learning_result["applied_changes"] = {
            "insight_feedback_received": True,
            "feedback_type": user_correction.get("feedback_type", "general"),
            "feedback_details": user_correction.get("details", {})
        }
        learning_result["next_steps"].append("Update insight generation model")
    
    # Add a default next step if none were added
    if not learning_result["next_steps"]:
        learning_result["next_steps"].append("Continue with workflow")
    
    return learning_result
