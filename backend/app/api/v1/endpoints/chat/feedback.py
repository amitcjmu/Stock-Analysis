"""
Chat message feedback and feedback viewing endpoints.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context, get_request_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessageFeedbackRequest(BaseModel):
    """Request model for chat message feedback."""

    message_id: str  # Unique identifier for the message
    feedback_type: str  # "thumbs_up" or "thumbs_down"
    page_route: Optional[str] = None
    flow_type: Optional[str] = None
    flow_id: Optional[str] = None
    additional_comment: Optional[str] = None


class ChatMessageFeedbackResponse(BaseModel):
    """Response model for chat message feedback."""

    status: str
    message: str
    feedback_id: Optional[str] = None


@router.post("/message-feedback")
async def submit_chat_message_feedback(
    request: ChatMessageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> ChatMessageFeedbackResponse:
    """
    Submit feedback for a specific chat message.

    Allows users to provide thumbs up/down feedback on individual AI responses.
    This helps improve the AI assistant's responses over time.

    Args:
        request: ChatMessageFeedbackRequest with message_id and feedback_type
        db: Database session
        context: Request context with tenant information

    Returns:
        ChatMessageFeedbackResponse with submission status

    Issue: #1218 - [Feature] Contextual AI Chat Assistant
    Milestone: Contextual AI Chat Assistant
    """
    try:
        from app.models.feedback import Feedback

        # Validate feedback type
        if request.feedback_type not in ("thumbs_up", "thumbs_down"):
            return ChatMessageFeedbackResponse(
                status="error",
                message="Invalid feedback type. Use 'thumbs_up' or 'thumbs_down'.",
            )

        # Build context-aware comment
        comment_parts = [f"Message feedback: {request.feedback_type}"]
        if request.flow_type:
            comment_parts.append(f"Flow: {request.flow_type}")
        if request.flow_id:
            comment_parts.append(f"Flow ID: {request.flow_id[:8]}...")
        if request.additional_comment:
            comment_parts.append(f"Comment: {request.additional_comment}")

        # Map thumbs feedback to rating (5 for thumbs_up, 1 for thumbs_down)
        rating = 5 if request.feedback_type == "thumbs_up" else 1

        # Create feedback record
        feedback = Feedback(
            feedback_type="chat_message",
            page=request.page_route or "/chat",
            rating=rating,
            comment=" | ".join(comment_parts),
            category="ai_chat_response",
            breadcrumb=f"Chat Message: {request.message_id[:8]}...",
            user_timestamp=datetime.utcnow().isoformat(),
            status="new",
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        logger.info(
            f"Chat message feedback submitted: {request.feedback_type} "
            f"for message {request.message_id[:8]}"
        )

        return ChatMessageFeedbackResponse(
            status="success",
            message="Feedback submitted successfully",
            feedback_id=str(feedback.id),
        )

    except Exception as e:
        logger.error(f"Error submitting chat message feedback: {e}")
        await db.rollback()
        return ChatMessageFeedbackResponse(
            status="error",
            message=f"Failed to submit feedback: {str(e)}",
        )


@router.get("/feedback")
async def get_all_feedback(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
):
    """
    Get all user feedback for the Feedback View page.
    Returns feedback sorted by most recent first.

    This endpoint is mounted under /chat to match frontend expectations.
    Security: Requires authentication to access feedback data.

    Issue: #1218 - [Feature] Contextual AI Chat Assistant
    Milestone: Contextual AI Chat Assistant
    """
    try:
        from app.models.feedback import Feedback

        user_id = context.user_id if context else "anonymous"
        logger.info(f"Fetching feedback for user: {user_id}")

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
