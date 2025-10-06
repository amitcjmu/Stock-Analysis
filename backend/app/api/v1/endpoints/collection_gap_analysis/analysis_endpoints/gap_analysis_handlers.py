"""
Gap Analysis Request Handler

Handles POST /analyze-gaps endpoint for Phase 2 AI enhancement.
"""

import hashlib
import json
import logging
import time

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.redis_config import get_redis_manager
from app.schemas.collection_gap_analysis import AnalyzeGapsRequest

from ..utils import resolve_collection_flow
from .background_workers import process_gap_enhancement_job
from .job_state_manager import create_job_state, get_job_state

logger = logging.getLogger(__name__)

# Server-side limits
MAX_GAPS_PER_REQUEST = 200


async def analyze_gaps(
    flow_id: str,
    request_body: AnalyzeGapsRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    **Phase 2: AI-Enhanced Gap Analysis (Non-Blocking)**

    Enqueues background job for AI-powered gap enhancement.
    Returns immediately with job_id for progress polling.

    **Architecture:**
    - Non-blocking: Returns 202 Accepted immediately
    - Background processing: Per-asset enhancement with incremental persistence
    - Progress polling: Frontend polls /enhancement-progress
    - Rate limited: 1 request per 10 seconds per flow
    - Idempotent: Hash of selected gap IDs prevents duplicate jobs

    **Request Body (POST):**
    ```json
    {
        "gaps": [...],  // Output from scan-gaps (max 200)
        "selected_asset_ids": ["uuid1", "uuid2"]
    }
    ```

    **Response (202 Accepted):**
    ```json
    {
        "job_id": "enhance_5bf1f5a8_1728187234",
        "status": "queued",
        "progress_url": "/api/v1/collection/...",
        "message": "Enhancement job queued. Poll progress_url for updates."
    }
    ```

    **Error Responses:**
    - 400: >200 gaps requested
    - 409: Job already running for this flow
    - 422: Invalid request format
    """
    try:
        # Server-side limit enforcement
        if len(request_body.gaps) > MAX_GAPS_PER_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Too many gaps requested ({len(request_body.gaps)}). "
                    f"Maximum allowed: {MAX_GAPS_PER_REQUEST}. "
                    f"Please select fewer gaps or use row selection."
                ),
            )

        logger.info(
            f"🤖 AI analysis request - Flow: {flow_id}, "
            f"Gaps: {len(request_body.gaps)}"
        )

        # Resolve collection flow (validates tenant access)
        collection_flow = await resolve_collection_flow(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # Create idempotency key from selected gap IDs
        gap_ids = sorted(
            [f"{gap.asset_id}:{gap.field_name}" for gap in request_body.gaps]
        )
        idempotency_key = hashlib.sha256(json.dumps(gap_ids).encode()).hexdigest()[:16]

        # Generate job ID
        job_id = f"enhance_{flow_id[:8]}_{int(time.time())}_{idempotency_key}"

        # Check for running jobs and enforce rate limiting in Redis
        redis_manager = get_redis_manager()
        if redis_manager.is_available():
            existing_job = await get_job_state(collection_flow.id)

            if existing_job:
                job_status = existing_job.get("status")

                # Block if job is actively running
                if job_status in ["queued", "running"]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Enhancement job already running for this flow. "
                            f"Job ID: {existing_job.get('job_id')}"
                        ),
                    )

                # Rate limiting: Block if last job completed <10s ago
                if job_status in ["completed", "failed"]:
                    last_updated = existing_job.get("updated_at", 0)
                    time_since_last = time.time() - last_updated
                    if time_since_last < 10:  # 10-second cooldown
                        wait_time = int(10 - time_since_last)
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=(
                                f"Rate limit: Please wait {wait_time} seconds "
                                f"before submitting another job."
                            ),
                        )

            # Initialize job state in Redis
            num_assets = len(set(gap.asset_id for gap in request_body.gaps))
            await create_job_state(
                job_id=job_id,
                flow_id=flow_id,
                collection_flow_id=collection_flow.id,
                total_gaps=len(request_body.gaps),
                total_assets=num_assets,
                idempotency_key=idempotency_key,
            )

        # Enqueue background task (pass primitives, not mutable context)
        background_tasks.add_task(
            process_gap_enhancement_job,
            job_id=job_id,
            collection_flow_id=collection_flow.id,
            gaps=request_body.gaps,
            selected_asset_ids=request_body.selected_asset_ids,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        progress_url = f"/api/v1/collection/{flow_id}/enhancement-progress"

        logger.info(f"🚀 Queued enhancement job {job_id} for flow {flow_id}")

        num_gaps = len(request_body.gaps)
        num_assets = len(set(gap.asset_id for gap in request_body.gaps))

        return {
            "job_id": job_id,
            "status": "queued",
            "progress_url": progress_url,
            "message": (
                f"Enhancement job queued for {num_gaps} gaps "
                f"across {num_assets} assets. "
                f"Poll progress_url for updates."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}",
        )
