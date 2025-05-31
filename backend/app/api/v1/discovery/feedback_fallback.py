"""
Fallback Feedback System for Railway Deployment Issues.
Provides basic feedback collection when database is unavailable.
"""

import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.api.v1.discovery.models import PageFeedbackRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for fallback (will be lost on restart, but better than nothing)
FALLBACK_FEEDBACK_STORE = []

@router.post("/feedback/fallback")
async def submit_fallback_feedback(request: PageFeedbackRequest):
    """
    Submit feedback using fallback in-memory storage.
    Used when database connection is unavailable.
    """
    try:
        # Create feedback entry in memory
        feedback_entry = {
            "id": str(uuid.uuid4()),
            "feedback_type": "page_feedback",
            "page": request.page,
            "rating": request.rating,
            "comment": request.comment,
            "category": request.category,
            "breadcrumb": request.breadcrumb,
            "user_timestamp": request.timestamp,
            "created_at": datetime.utcnow().isoformat(),
            "status": "new",
            "storage_method": "fallback_memory"
        }
        
        FALLBACK_FEEDBACK_STORE.append(feedback_entry)
        
        logger.info(f"Fallback feedback stored for {request.page}: {request.rating}/5")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully (fallback mode)",
            "feedback_id": feedback_entry["id"],
            "storage_method": "fallback_memory",
            "warning": "Database unavailable - feedback stored temporarily"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit fallback feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/feedback/fallback")
async def get_fallback_feedback():
    """
    Get feedback from fallback storage.
    """
    try:
        return {
            "feedback": FALLBACK_FEEDBACK_STORE,
            "total_count": len(FALLBACK_FEEDBACK_STORE),
            "storage_method": "fallback_memory",
            "warning": "This is fallback data - may be incomplete"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve fallback feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

@router.get("/feedback/fallback/status")
async def get_fallback_status():
    """
    Get status of fallback feedback system.
    """
    return {
        "status": "active",
        "storage_method": "fallback_memory",
        "total_feedback": len(FALLBACK_FEEDBACK_STORE),
        "description": "Fallback feedback system - no database required",
        "limitations": [
            "Data lost on server restart",
            "No persistent storage",
            "Limited functionality"
        ]
    } 