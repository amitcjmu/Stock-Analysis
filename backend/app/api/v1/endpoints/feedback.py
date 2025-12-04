"""
Feedback API endpoints for user feedback collection and management.
Provides endpoints for submitting, retrieving, and managing user feedback.

Security:
- All endpoints require authentication via RequestContext
- Input validation prevents XSS via length limits and sanitization
- DELETE requires authenticated user (admin feature)
"""

import html
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Input validation constants
MAX_COMMENT_LENGTH = 2000
MAX_PAGE_LENGTH = 255
MAX_BREADCRUMB_LENGTH = 500
MAX_USER_NAME_LENGTH = 100


def sanitize_input(value: str, max_length: int) -> str:
    """Sanitize user input to prevent XSS attacks."""
    if not value:
        return value
    # Truncate to max length
    value = value[:max_length]
    # HTML encode special characters
    value = html.escape(value)
    # Remove any potential script injection patterns
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE)
    return value.strip()


# Feedback endpoint models
class FeedbackRequest(BaseModel):
    page: str
    rating: int
    comment: str
    category: str = "ui"
    breadcrumb: Optional[str] = None
    timestamp: str
    user_name: Optional[str] = None  # Display name (validated server-side)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str) -> str:
        if len(v) > MAX_COMMENT_LENGTH:
            raise ValueError(
                f"Comment must be less than {MAX_COMMENT_LENGTH} characters"
            )
        return v

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: str) -> str:
        if len(v) > MAX_PAGE_LENGTH:
            raise ValueError(f"Page must be less than {MAX_PAGE_LENGTH} characters")
        return v


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
):
    """
    Submit user feedback for UI/UX improvements.
    Global feedback endpoint for all app pages.
    Saves directly to the database for retrieval on Feedback View page.

    Security: Requires authentication, sanitizes all user inputs.
    """
    try:
        # Sanitize all user inputs to prevent XSS
        sanitized_page = sanitize_input(request.page, MAX_PAGE_LENGTH)
        sanitized_comment = sanitize_input(request.comment, MAX_COMMENT_LENGTH)
        sanitized_breadcrumb = (
            sanitize_input(request.breadcrumb, MAX_BREADCRUMB_LENGTH)
            if request.breadcrumb
            else None
        )
        sanitized_user_name = (
            sanitize_input(request.user_name, MAX_USER_NAME_LENGTH)
            if request.user_name
            else None
        )

        logger.info(
            f"Feedback submission for page: {sanitized_page} "
            f"by user: {context.user_id or 'anonymous'}"
        )

        from app.models.feedback import Feedback

        # Create feedback record in database with sanitized inputs
        feedback = Feedback(
            feedback_type="ui_feedback",
            page=sanitized_page,
            rating=request.rating,
            comment=sanitized_comment,
            category=request.category,
            breadcrumb=sanitized_breadcrumb,
            user_timestamp=request.timestamp,
            user_name=sanitized_user_name or "Anonymous",
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
    context: RequestContext = Depends(get_request_context),
):
    """
    Get all user feedback for the Feedback View page.
    Returns feedback sorted by most recent first.

    Security: Requires authentication to access feedback data.
    """
    try:
        from app.models.feedback import Feedback

        logger.info(f"Fetching feedback for user: {context.user_id or 'anonymous'}")

        # Query all feedback, ordered by created_at descending
        stmt = select(Feedback).order_by(Feedback.created_at.desc())
        result = await db.execute(stmt)
        feedback_records = result.scalars().all()

        # Transform to response format (output is already sanitized on input)
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
    context: RequestContext = Depends(get_request_context),
):
    """
    Delete a feedback entry. Admin feature for managing feedback.

    Security: Requires authentication AND admin privileges.
    """
    try:
        from uuid import UUID as PyUUID

        from app.core.middleware.auth_utils import check_platform_admin
        from app.models.feedback import Feedback

        # Verify user is authenticated
        if not context.user_id:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to delete feedback",
            )

        # Verify user has admin privileges
        is_admin = await check_platform_admin(context.user_id)
        if not is_admin:
            logger.warning(
                f"Non-admin user {context.user_id} attempted to delete feedback"
            )
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required to delete feedback",
            )

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

        logger.info(f"Feedback deleted: {feedback_id} by user: {context.user_id}")

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
