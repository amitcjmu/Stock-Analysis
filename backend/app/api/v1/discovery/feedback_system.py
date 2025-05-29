"""
Feedback System Endpoints.
Handles user feedback collection and management.
"""

import logging
import uuid
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
import pandas as pd

from app.api.v1.discovery.models import PageFeedbackRequest
from app.api.v1.discovery.persistence import save_to_file, load_from_file

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize feedback store
feedback_store = load_from_file("feedback_store", [])

@router.post("/feedback")
async def submit_page_feedback(request: PageFeedbackRequest):
    """
    Submit general page feedback.
    """
    try:
        feedback_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": pd.Timestamp.now().isoformat(),
            "page": request.page,
            "rating": request.rating,
            "comment": request.comment,
            "category": request.category,
            "breadcrumb": request.breadcrumb,
            "user_timestamp": request.timestamp,
            "feedback_type": "page_feedback"
        }
        
        feedback_store.append(feedback_entry)
        save_to_file("feedback_store", feedback_store)
        
        logger.info(f"Page feedback received for {request.page}: {request.rating}/5")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_entry["id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to submit page feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/feedback")
async def get_feedback():
    """
    Get all feedback for analysis (admin endpoint).
    """
    try:
        # Return all feedback entries
        return {
            "feedback": feedback_store,
            "total_count": len(feedback_store),
            "summary": {
                "by_type": _get_feedback_by_type(),
                "by_page": _get_feedback_by_page(),
                "by_rating": _get_feedback_by_rating(),
                "recent_feedback": _get_recent_feedback(10)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

# Helper functions
def _get_feedback_by_type() -> Dict[str, int]:
    """Get feedback count by type."""
    type_count = {}
    for feedback in feedback_store:
        feedback_type = feedback.get('feedback_type', 'unknown')
        type_count[feedback_type] = type_count.get(feedback_type, 0) + 1
    return type_count

def _get_feedback_by_page() -> Dict[str, int]:
    """Get feedback count by page."""
    page_count = {}
    for feedback in feedback_store:
        page = feedback.get('page', 'unknown')
        page_count[page] = page_count.get(page, 0) + 1
    return page_count

def _get_feedback_by_rating() -> Dict[str, int]:
    """Get feedback count by rating."""
    rating_count = {}
    for feedback in feedback_store:
        rating = feedback.get('rating')
        if rating is not None:
            rating_key = f"{rating} stars"
            rating_count[rating_key] = rating_count.get(rating_key, 0) + 1
    return rating_count

def _get_recent_feedback(limit: int = 10) -> List[Dict[str, Any]]:
    """Get most recent feedback entries."""
    # Sort by timestamp (most recent first)
    sorted_feedback = sorted(
        feedback_store, 
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    return sorted_feedback[:limit] 