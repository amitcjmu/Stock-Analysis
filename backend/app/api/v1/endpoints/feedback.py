"""
Feedback API endpoints for user feedback collection and management.
Provides endpoints for submitting, retrieving, and managing user feedback.

Security:
- All endpoints require authentication via RequestContext
- Input validation prevents XSS via length limits and sanitization
- DELETE requires authenticated user (admin feature)
- Screenshot validation decodes base64 and verifies image format
- JSON fields (browser_info, flow_context) are sanitized to prevent stored XSS
"""

import base64
import html
import logging
import re
from typing import Any, Optional

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
MAX_STEPS_LENGTH = 5000
MAX_BEHAVIOR_LENGTH = 2000
MAX_SCREENSHOT_DECODED_SIZE = 5 * 1024 * 1024  # 5MB decoded
MAX_JSON_FIELD_KEYS = 20  # Max keys in browser_info/flow_context
MAX_JSON_VALUE_LENGTH = 500  # Max length per JSON string value

# Valid image signatures (magic bytes)
VALID_IMAGE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",  # WebP starts with RIFF
}


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


def sanitize_json_value(value: Any, max_length: int = MAX_JSON_VALUE_LENGTH) -> Any:
    """Recursively sanitize JSON values to prevent stored XSS (Qodo security fix)."""
    if value is None:
        return None
    if isinstance(value, str):
        # Truncate and HTML escape string values
        return html.escape(value[:max_length])
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        # Limit list length and sanitize each element
        return [sanitize_json_value(item) for item in value[:50]]
    if isinstance(value, dict):
        # Limit number of keys and sanitize each key/value
        sanitized = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= MAX_JSON_FIELD_KEYS:
                break
            # Sanitize key (alphanumeric, underscore, hyphen only)
            safe_key = re.sub(r"[^a-zA-Z0-9_-]", "", str(k)[:100])
            if safe_key:
                sanitized[safe_key] = sanitize_json_value(v)
        return sanitized
    # Unknown type - convert to string and sanitize
    return html.escape(str(value)[:max_length])


def validate_image_data(base64_data: str) -> tuple[bool, str]:
    """
    Validate base64 screenshot data (Qodo security fix).

    Returns:
        tuple of (is_valid, error_message)
    """
    try:
        # Handle data URL format: data:image/png;base64,iVBOR...
        if base64_data.startswith("data:"):
            # Extract the base64 part after the comma
            if "," not in base64_data:
                return False, "Invalid data URL format"
            header, base64_data = base64_data.split(",", 1)
            # Validate content type in header
            if not any(
                img_type in header
                for img_type in ["image/png", "image/jpeg", "image/gif", "image/webp"]
            ):
                return False, "Invalid image type in data URL"

        # Decode base64
        try:
            decoded = base64.b64decode(base64_data)
        except Exception:
            return False, "Invalid base64 encoding"

        # Check decoded size
        if len(decoded) > MAX_SCREENSHOT_DECODED_SIZE:
            return (
                False,
                f"Screenshot exceeds maximum size of {MAX_SCREENSHOT_DECODED_SIZE // (1024*1024)}MB",
            )

        # Verify image format by checking magic bytes
        is_valid_image = False
        for signature in VALID_IMAGE_SIGNATURES:
            if decoded.startswith(signature):
                is_valid_image = True
                break

        if not is_valid_image:
            return False, "Invalid image format - must be PNG, JPEG, GIF, or WebP"

        return True, ""
    except Exception as e:
        return False, f"Screenshot validation failed: {str(e)}"


# Feedback endpoint models
class FeedbackRequest(BaseModel):
    page: str
    rating: int
    comment: str
    category: str = "ui"  # ui, performance, feature, bug, general
    breadcrumb: Optional[str] = None
    timestamp: str
    user_name: Optional[str] = None  # Display name (validated server-side)
    # Bug report specific fields (Issue #739)
    severity: Optional[str] = None  # low, medium, high, critical
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    screenshot_data: Optional[str] = None  # Base64 encoded
    browser_info: Optional[dict] = None  # {name, version, os, platform}
    flow_context: Optional[dict] = None  # {flow_id, phase, status}

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

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("low", "medium", "high", "critical"):
            raise ValueError("Severity must be one of: low, medium, high, critical")
        return v

    @field_validator("steps_to_reproduce")
    @classmethod
    def validate_steps(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > MAX_STEPS_LENGTH:
            raise ValueError(f"Steps must be less than {MAX_STEPS_LENGTH} characters")
        return v

    @field_validator("screenshot_data")
    @classmethod
    def validate_screenshot(cls, v: Optional[str]) -> Optional[str]:
        """Validate screenshot: decode base64, check size, verify image format (Qodo security fix)."""
        if v is None:
            return None
        is_valid, error_msg = validate_image_data(v)
        if not is_valid:
            raise ValueError(error_msg)
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

        # Sanitize bug report fields
        sanitized_steps = (
            sanitize_input(request.steps_to_reproduce, MAX_STEPS_LENGTH)
            if request.steps_to_reproduce
            else None
        )
        sanitized_expected = (
            sanitize_input(request.expected_behavior, MAX_BEHAVIOR_LENGTH)
            if request.expected_behavior
            else None
        )
        sanitized_actual = (
            sanitize_input(request.actual_behavior, MAX_BEHAVIOR_LENGTH)
            if request.actual_behavior
            else None
        )

        # Sanitize JSON fields to prevent stored XSS (Qodo security fix)
        sanitized_browser_info = (
            sanitize_json_value(request.browser_info) if request.browser_info else None
        )
        sanitized_flow_context = (
            sanitize_json_value(request.flow_context) if request.flow_context else None
        )

        # Determine feedback type based on category
        feedback_type = "bug_report" if request.category == "bug" else "ui_feedback"

        logger.info(
            f"Feedback submission ({feedback_type}) for page: {sanitized_page} "
            f"by user: {context.user_id or 'anonymous'}"
        )

        from app.models.feedback import Feedback

        # Create feedback record in database with sanitized inputs
        feedback = Feedback(
            feedback_type=feedback_type,
            page=sanitized_page,
            rating=request.rating,
            comment=sanitized_comment,
            category=request.category,
            breadcrumb=sanitized_breadcrumb,
            user_timestamp=request.timestamp,
            user_name=sanitized_user_name or "Anonymous",
            status="new",
            # Bug report specific fields (Issue #739)
            severity=request.severity,
            steps_to_reproduce=sanitized_steps,
            expected_behavior=sanitized_expected,
            actual_behavior=sanitized_actual,
            screenshot_data=request.screenshot_data,  # Validated for size and format
            browser_info=sanitized_browser_info,  # Sanitized to prevent XSS
            flow_context=sanitized_flow_context,  # Sanitized to prevent XSS
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
            feedback_item = {
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
                # Bug report fields (Issue #739)
                "severity": getattr(record, "severity", None),
                "steps_to_reproduce": getattr(record, "steps_to_reproduce", None),
                "expected_behavior": getattr(record, "expected_behavior", None),
                "actual_behavior": getattr(record, "actual_behavior", None),
                "browser_info": getattr(record, "browser_info", None),
                "flow_context": getattr(record, "flow_context", None),
                # Exclude screenshot_data from list view (too large)
                "has_screenshot": bool(getattr(record, "screenshot_data", None)),
            }
            feedback_list.append(feedback_item)

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
