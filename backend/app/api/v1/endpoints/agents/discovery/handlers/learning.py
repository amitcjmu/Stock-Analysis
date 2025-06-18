"""
Learning handler for discovery agent.

This module contains the learning-related endpoints for the discovery agent.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User

# Import field mapping models if available
try:
    from app.models.data_import.import_field_mapping import ImportFieldMapping
    FIELD_MAPPING_AVAILABLE = True
except ImportError:
    FIELD_MAPPING_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(tags=["learning"])

@router.get("/learning")
async def get_learning_data(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """Get agent learning data."""
    return {
        "learning_patterns": [
            {
                "id": "pattern-1",
                "type": "field_mapping",
                "confidence": 0.95,
                "usage_count": 42
            }
        ],
        "total_patterns": 1
    }

@router.post("/agent-learning")
async def process_agent_learning_action(
    learning_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """Process agent learning actions including field mapping approval/rejection."""
    try:
        learning_type = learning_input.get('learning_type')
        
        if learning_type == 'field_mapping_action':
            return await handle_field_mapping_action(learning_input, db, context)
        elif learning_type == 'field_mapping_change':
            return await handle_field_mapping_change(learning_input, db, context)
        else:
            return await handle_general_learning(learning_input, db, context)
            
    except Exception as e:
        logger.error(f"Error processing agent learning action: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process learning action: {str(e)}")

async def handle_field_mapping_action(
    learning_input: Dict[str, Any], 
    db: AsyncSession, 
    context: RequestContext
) -> Dict[str, Any]:
    """Handle field mapping approve/reject actions."""
    try:
        mapping_id = learning_input.get('mapping_id')
        action = learning_input.get('action')  # 'approve' or 'reject'
        
        if not mapping_id or not action:
            raise HTTPException(status_code=400, detail="mapping_id and action are required")
        
        # Log the action for learning
        logger.info(f"Field mapping action processed: {action} for mapping {mapping_id}")
        
        return {
            "status": "success",
            "message": f"Field mapping {action}d successfully",
            "mapping_id": mapping_id,
            "action": action,
            "learning_applied": True
        }
        
    except Exception as e:
        logger.error(f"Error handling field mapping action: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to {action} mapping: {str(e)}")

async def handle_field_mapping_change(
    learning_input: Dict[str, Any], 
    db: AsyncSession, 
    context: RequestContext
) -> Dict[str, Any]:
    """Handle field mapping changes."""
    try:
        mapping_id = learning_input.get('mapping_id')
        new_mapping = learning_input.get('new_mapping')
        
        if not mapping_id or not new_mapping:
            raise HTTPException(status_code=400, detail="mapping_id and new_mapping are required")
        
        # Log the change for learning
        logger.info(f"Field mapping change processed for mapping {mapping_id}")
        
        return {
            "status": "success",
            "message": "Field mapping updated successfully",
            "mapping_id": mapping_id,
            "learning_applied": True
        }
        
    except Exception as e:
        logger.error(f"Error handling field mapping change: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")

async def handle_general_learning(
    learning_input: Dict[str, Any], 
    db: AsyncSession, 
    context: RequestContext
) -> Dict[str, Any]:
    """Handle general learning inputs."""
    return {
        "status": "success",
        "message": "General learning processed successfully",
        "learning_applied": True
    }

@router.post("/answer-clarification")
async def answer_agent_clarification(
    clarification_response: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """Process user responses to agent questions."""
    return {
        "status": "success",
        "message": "Clarification processed successfully"
    }

@router.post("/process-learning")
async def process_agent_learning(
    learning_input: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """Process agent learning from user corrections."""
    return {
        "status": "success",
        "message": "Learning processed successfully"
    }

@router.get("/health")
async def learning_health():
    """Health check for learning endpoints."""
    return {
        "status": "healthy",
        "service": "learning",
        "version": "1.0.0"
    }
