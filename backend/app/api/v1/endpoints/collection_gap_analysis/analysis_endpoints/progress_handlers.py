"""
Progress Polling Handlers

Handles GET /enhancement-progress endpoint for HTTP polling of job status.
"""

import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db

from ..utils import resolve_collection_flow
from .job_state_manager import get_job_state

logger = logging.getLogger(__name__)


async def get_enhancement_progress(
    flow_id: str,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current progress of gap enhancement (HTTP polling).

    Frontend polls this endpoint every 2-3 seconds during AI enhancement
    to display progress bar and current asset being processed.

    **Polling Strategy:**
    - Poll every 2-3 seconds while status == "queued" | "running"
    - Stop polling when status == "completed" | "failed" | "not_started"
    - Display: "{processed}/{total} assets ({percentage}%) - {current_asset}"

    **Response:**
    ```json
    {
        "status": "running",
        "processed": 5,
        "total": 10,
        "current_asset": "Web Server 03",
        "percentage": 50,
        "updated_at": "2025-10-05T18:30:45.123Z"
    }
    ```

    **Note:** Job state has 1-hour TTL in Redis. Returns "not_started"
    if no enhancement is running or TTL expired.
    """
    # Resolve collection flow to get internal ID
    collection_flow = await resolve_collection_flow(
        flow_id=flow_id,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        db=db,
    )

    # Get job state from Redis
    job_state = await get_job_state(collection_flow.id)

    if not job_state:
        # No job found or Redis unavailable
        return {
            "status": "not_started",
            "processed": 0,
            "total": 0,
            "percentage": 0,
        }

    # Calculate percentage
    total_assets = job_state.get("total_assets", 0)
    processed_assets = job_state.get("processed_assets", 0)
    percentage = int((processed_assets / total_assets * 100) if total_assets > 0 else 0)

    # Bug #1180 Fix: Include error details for failed jobs so frontend can display them
    response = {
        "status": job_state.get("status", "not_started"),
        "processed": processed_assets,
        "total": total_assets,
        "current_asset": job_state.get("current_asset"),
        "percentage": percentage,
        "enhanced_count": job_state.get("enhanced_count", 0),
        "gaps_persisted": job_state.get("gaps_persisted", 0),
        "updated_at": job_state.get("updated_at"),
        "message": job_state.get(
            "message"
        ),  # Bug #1105 Fix: Include message for better UX
    }

    # Bug #1180 Fix: Add error fields when job has failed
    if job_state.get("status") == "failed":
        error_message = job_state.get("error")
        user_message = job_state.get("user_message")

        response["error"] = error_message or "Unknown error occurred"
        response["error_type"] = job_state.get("error_type")
        response["error_category"] = job_state.get("error_category")
        response["user_message"] = (
            user_message or error_message or "AI enhancement failed. Please try again."
        )

    return response
