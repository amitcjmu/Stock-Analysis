"""
Feedback API endpoints for user feedback collection and management.
Provides endpoints for submitting, retrieving, and managing user feedback.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# Feedback endpoint models
class FeedbackRequest(BaseModel):
    page: str
    rating: int
    comment: str
    category: str = "ui"
    breadcrumb: Optional[str] = None
    timestamp: str
    user_name: Optional[str] = None  # Display name of user submitting feedback


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit user feedback for UI/UX improvements.
    Global feedback endpoint for all app pages.
    Saves directly to the database for retrieval on Feedback View page.
    """
    try:
        logger.info(f"Feedback submission for page: {request.page}")

        from app.models.feedback import Feedback

        # Create feedback record in database
        feedback = Feedback(
            feedback_type="ui_feedback",
            page=request.page,
            rating=request.rating,
            comment=request.comment,
            category=request.category,
            breadcrumb=request.breadcrumb,
            user_timestamp=request.timestamp,
            user_name=request.user_name or "Anonymous",
            status="new",
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        logger.info(f"Feedback saved with ID: {feedback.id}")

        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": str(feedback.id),
            "timestamp": request.timestamp,
        }

    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Feedback submission failed: {str(e)}"
        )


@router.get("/feedback")
async def get_all_feedback(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all user feedback for the Feedback View page.
    Returns feedback sorted by most recent first.
    """
    try:
        from app.models.feedback import Feedback

        # Query all feedback, ordered by created_at descending
        stmt = select(Feedback).order_by(Feedback.created_at.desc())
        result = await db.execute(stmt)
        feedback_records = result.scalars().all()

        # Transform to response format
        feedback_list = []
        for record in feedback_records:
            feedback_list.append(
                {
                    "id": str(record.id),
                    "feedback_type": record.feedback_type,
                    "page": record.page or "Unknown",
                    "rating": record.rating or 0,
                    "comment": record.comment or "",
                    "category": record.category or "general",
                    "status": record.status or "new",
                    "timestamp": record.user_timestamp
                    or (record.created_at.isoformat() if record.created_at else None),
                    "user_name": getattr(record, "user_name", None) or "Anonymous",
                }
            )

        return {
            "success": True,
            "feedback": feedback_list,
            "total": len(feedback_list),
        }

    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch feedback: {str(e)}"
        )


@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a feedback entry. Admin feature for managing feedback.
    """
    try:
        from uuid import UUID as PyUUID
        from app.models.feedback import Feedback

        # Parse the UUID
        try:
            feedback_uuid = PyUUID(feedback_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feedback ID format")

        # Find the feedback record
        stmt = select(Feedback).where(Feedback.id == feedback_uuid)
        result = await db.execute(stmt)
        feedback_record = result.scalar_one_or_none()

        if not feedback_record:
            raise HTTPException(status_code=404, detail="Feedback not found")

        # Delete the record
        await db.delete(feedback_record)
        await db.commit()

        logger.info(f"Feedback deleted: {feedback_id}")

        return {
            "success": True,
            "message": "Feedback deleted successfully",
            "deleted_id": feedback_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete feedback: {str(e)}"
        )
