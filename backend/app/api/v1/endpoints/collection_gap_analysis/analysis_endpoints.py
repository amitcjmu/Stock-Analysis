"""
Phase 2: AI-Enhanced Gap Analysis Endpoints
"""

import hashlib
import json
import logging
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.redis_config import get_redis_manager
from app.schemas.collection_gap_analysis import (
    AnalyzeGapsRequest,
)

from .utils import resolve_collection_flow

logger = logging.getLogger(__name__)

# Server-side limits
MAX_GAPS_PER_REQUEST = 200

router = APIRouter()


@router.post("/{flow_id}/analyze-gaps", status_code=202)
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
        "progress_url": "/api/v1/collection/5bf1f5a8-0a4d-428c-afa7-940a26af977b/enhancement-progress",
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
                detail=f"Too many gaps requested ({len(request_body.gaps)}). Maximum allowed: {MAX_GAPS_PER_REQUEST}. Please select fewer gaps or use row selection.",
            )

        logger.info(
            f"🤖 AI analysis request - Flow: {flow_id}, Gaps: {len(request_body.gaps)}"
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
            # Check for existing job (idempotency + rate limit)
            job_key = f"gap_enhancement_job:{collection_flow.id}"
            existing_job = await redis_manager.client.get(job_key)

            if existing_job:
                existing_job_data = json.loads(existing_job)
                job_status = existing_job_data.get("status")

                # Block if job is actively running
                if job_status in ["queued", "running"]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Enhancement job already running for this flow. Job ID: {existing_job_data.get('job_id')}",
                    )

                # Rate limiting: Block if last job completed <10s ago
                if job_status in ["completed", "failed"]:
                    last_updated = existing_job_data.get("updated_at", 0)
                    time_since_last = time.time() - last_updated
                    if time_since_last < 10:  # 10-second cooldown
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Rate limit: Please wait {int(10 - time_since_last)} seconds before submitting another job.",
                        )

            # Initialize job state in Redis
            job_state = {
                "job_id": job_id,
                "status": "queued",
                "flow_id": str(collection_flow.flow_id),
                "total_gaps": len(request_body.gaps),
                "processed_assets": 0,
                "total_assets": len(set(gap.asset_id for gap in request_body.gaps)),
                "enhanced_count": 0,
                "failed_count": 0,
                "gaps_persisted": 0,
                "started_at": time.time(),
                "updated_at": time.time(),
                "idempotency_key": idempotency_key,
            }

            await redis_manager.client.set(
                job_key, json.dumps(job_state), ex=3600  # 1-hour TTL
            )

            logger.info(
                f"✅ Created job {job_id} with idempotency key {idempotency_key}"
            )

        # Enqueue background task (pass primitives, not mutable context)
        background_tasks.add_task(
            _process_gap_enhancement_job,
            job_id=job_id,
            flow_id=flow_id,
            collection_flow_id=collection_flow.id,
            gaps=request_body.gaps,
            selected_asset_ids=request_body.selected_asset_ids,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        progress_url = f"/api/v1/collection/{flow_id}/enhancement-progress"

        logger.info(f"🚀 Queued enhancement job {job_id} for flow {flow_id}")

        return {
            "job_id": job_id,
            "status": "queued",
            "progress_url": progress_url,
            "message": f"Enhancement job queued for {len(request_body.gaps)} gaps across {len(set(gap.asset_id for gap in request_body.gaps))} assets. Poll progress_url for updates.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}",
        )


async def _process_gap_enhancement_job(
    job_id: str,
    flow_id: str,
    collection_flow_id: int,
    gaps: list,
    selected_asset_ids: list,
    client_account_id: str,
    engagement_id: str,
):
    """Background worker for gap enhancement with per-asset persistence.

    Args:
        job_id: Unique job identifier
        flow_id: Collection flow UUID (business identifier)
        collection_flow_id: Collection flow internal ID
        gaps: List of gaps to enhance
        selected_asset_ids: Asset IDs to process
        client_account_id: Client account UUID (primitive, not mutable context)
        engagement_id: Engagement UUID (primitive, not mutable context)
    """
    from app.services.collection.gap_analysis.data_loader import load_assets
    from app.services.collection.gap_analysis.service import GapAnalysisService
    from app.services.collection_phase_progression_service import (
        CollectionPhaseProgressionService,
    )

    redis_manager = get_redis_manager()
    job_key = f"gap_enhancement_job:{collection_flow_id}"

    async def update_job_state(updates: dict):
        """Helper to update job state in Redis."""
        if redis_manager.is_available():
            try:
                job_state_json = await redis_manager.client.get(job_key)
                if job_state_json:
                    job_state = json.loads(job_state_json)
                    job_state.update(updates)
                    job_state["updated_at"] = time.time()
                    await redis_manager.client.set(
                        job_key, json.dumps(job_state), ex=3600
                    )
            except Exception as e:
                logger.warning(f"Failed to update job state: {e}")

    try:
        await update_job_state({"status": "running"})

        # Get database session for background task
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Load assets (using primitive IDs)
            assets = await load_assets(
                selected_asset_ids,
                client_account_id,
                engagement_id,
                db,
            )

            if not assets:
                logger.warning("⚠️ No assets found for AI analysis")
                await update_job_state(
                    {
                        "status": "completed",
                        "message": "No assets found",
                    }
                )
                return

            # Initialize gap analysis service (using primitive IDs)
            gap_service = GapAnalysisService(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                collection_flow_id=str(collection_flow_id),
            )

            # Convert Pydantic gaps to dict format
            gaps_for_ai = [gap.model_dump() for gap in gaps]

            # Run tier_2 AI analysis WITH per-asset persistence
            logger.info(
                f"🤖 Job {job_id}: Running AI enhancement for {len(gaps_for_ai)} gaps"
            )

            # Note: gap_service already initialized above with AgentHelperMixin

            # Override _update_progress to update job state
            original_update_progress = (
                gap_service._update_progress
                if hasattr(gap_service, "_update_progress")
                else None
            )

            async def custom_update_progress(
                flow_id_param, processed, total, current_asset, redis_client
            ):
                await update_job_state(
                    {
                        "processed_assets": processed,
                        "total_assets": total,
                        "current_asset": current_asset,
                    }
                )
                # Call original if exists
                if original_update_progress:
                    await original_update_progress(
                        flow_id_param, processed, total, current_asset, redis_client
                    )

            gap_service._update_progress = custom_update_progress

            # Run enhancement with per-asset persistence
            ai_result = await gap_service._run_tier_2_ai_analysis_with_persist(
                assets=assets,
                collection_flow_id=str(collection_flow_id),
                gaps=gaps_for_ai,
                db=db,
            )

            # Update final job state
            summary = ai_result.get("summary", {})
            await update_job_state(
                {
                    "status": "completed",
                    "enhanced_count": summary.get("total_gaps", 0),
                    "gaps_persisted": summary.get("gaps_persisted", 0),
                    "failed_count": summary.get("assets_failed", 0),
                }
            )

            # Auto-progress to next phase if gaps were persisted
            gaps_persisted = summary.get("gaps_persisted", 0)
            if gaps_persisted > 0:
                try:
                    # Get collection flow for progression
                    from sqlalchemy import select, and_
                    from app.models.collection_flow import CollectionFlow

                    # Use primitive IDs for query (safer than mutable context)
                    from uuid import UUID

                    stmt = select(CollectionFlow).where(
                        and_(
                            CollectionFlow.id == collection_flow_id,
                            CollectionFlow.client_account_id == UUID(client_account_id),
                            CollectionFlow.engagement_id == UUID(engagement_id),
                        )
                    )
                    result = await db.execute(stmt)
                    collection_flow = result.scalar_one_or_none()

                    if collection_flow and collection_flow.master_flow_id:
                        logger.info(
                            f"🚀 Job {job_id}: Auto-progressing to questionnaire_generation"
                        )

                        # Create minimal context from primitives for progression service
                        from app.core.context import RequestContext

                        temp_context = RequestContext(
                            client_account_id=UUID(client_account_id),
                            engagement_id=UUID(engagement_id),
                            user_id=None,  # Background job has no user
                        )

                        progression_service = CollectionPhaseProgressionService(
                            db_session=db, context=temp_context
                        )
                        progression_result = (
                            await progression_service.advance_to_next_phase(
                                flow=collection_flow,
                                target_phase="questionnaire_generation",
                            )
                        )

                        if progression_result["status"] == "success":
                            logger.info(
                                f"✅ Job {job_id}: Advanced to questionnaire_generation"
                            )
                            await update_job_state(
                                {
                                    "phase_progression": "advanced_to_questionnaire_generation"
                                }
                            )
                        else:
                            logger.warning(
                                f"⚠️ Job {job_id}: Phase progression failed: {progression_result.get('error')}"
                            )
                            await update_job_state(
                                {
                                    "phase_progression": f"failed: {progression_result.get('error')}"
                                }
                            )
                except Exception as progression_error:
                    logger.error(
                        f"❌ Job {job_id}: Phase progression error: {progression_error}",
                        exc_info=True,
                    )
                    await update_job_state(
                        {"phase_progression": f"error: {str(progression_error)}"}
                    )

            logger.info(f"✅ Job {job_id}: Enhancement complete")

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)
        await update_job_state(
            {
                "status": "failed",
                "error": str(e),
            }
        )


@router.get("/{flow_id}/enhancement-progress")
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
        "status": "running",  // "not_started" | "queued" | "running" | "completed" | "failed"
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
    from app.core.redis_config import get_redis_manager
    import json

    # Resolve collection flow to get internal ID
    collection_flow = await resolve_collection_flow(
        flow_id=flow_id,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        db=db,
    )

    # Get Redis client
    redis_manager = get_redis_manager()
    if not redis_manager.is_available():
        # Redis unavailable, return not_started
        return {
            "status": "not_started",
            "processed": 0,
            "total": 0,
            "percentage": 0,
        }

    # Use same key as worker: gap_enhancement_job:{collection_flow.id}
    job_key = f"gap_enhancement_job:{collection_flow.id}"

    try:
        job_state_json = await redis_manager.client.get(job_key)

        if not job_state_json:
            # No job found
            return {
                "status": "not_started",
                "processed": 0,
                "total": 0,
                "percentage": 0,
            }

        # Parse job state
        job_state = json.loads(job_state_json)

        # Calculate percentage
        total_assets = job_state.get("total_assets", 0)
        processed_assets = job_state.get("processed_assets", 0)
        percentage = int(
            (processed_assets / total_assets * 100) if total_assets > 0 else 0
        )

        return {
            "status": job_state.get("status", "not_started"),
            "processed": processed_assets,
            "total": total_assets,
            "current_asset": job_state.get("current_asset"),
            "percentage": percentage,
            "enhanced_count": job_state.get("enhanced_count", 0),
            "gaps_persisted": job_state.get("gaps_persisted", 0),
            "updated_at": job_state.get("updated_at"),
        }

    except Exception as e:
        logger.error(f"Failed to get enhancement progress: {e}", exc_info=True)
        # Fail gracefully, return not_started
        return {
            "status": "not_started",
            "processed": 0,
            "total": 0,
            "percentage": 0,
        }
