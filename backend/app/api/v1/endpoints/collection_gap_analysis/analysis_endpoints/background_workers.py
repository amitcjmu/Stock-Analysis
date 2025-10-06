"""
Background Workers for Gap Enhancement Jobs

Handles asynchronous processing of gap enhancement jobs with per-asset persistence.
"""

import logging
from uuid import UUID

from .job_state_manager import update_job_state

logger = logging.getLogger(__name__)


async def process_gap_enhancement_job(
    job_id: str,
    collection_flow_id: UUID,
    gaps: list,
    selected_asset_ids: list,
    client_account_id: str,
    engagement_id: str,
):
    """Background worker for gap enhancement with per-asset persistence.

    Args:
        job_id: Unique job identifier
        collection_flow_id: Collection flow internal ID (used for all DB operations)
        gaps: List of gaps to enhance
        selected_asset_ids: Asset IDs to process
        client_account_id: Client account UUID (primitive, not mutable context)
        engagement_id: Engagement UUID (primitive, not mutable context)
    """
    from app.services.collection.gap_analysis.data_loader import load_assets
    from app.services.collection.gap_analysis.service import GapAnalysisService

    try:
        await update_job_state(collection_flow_id, {"status": "running"})

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
                    collection_flow_id,
                    {
                        "status": "completed",
                        "message": "No assets found",
                    },
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
                f"🤖 Job {job_id}: Running AI enhancement "
                f"for {len(gaps_for_ai)} gaps"
            )

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
                    collection_flow_id,
                    {
                        "processed_assets": processed,
                        "total_assets": total,
                        "current_asset": current_asset,
                    },
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
                collection_flow_id,
                {
                    "status": "completed",
                    "enhanced_count": summary.get("total_gaps", 0),
                    "gaps_persisted": summary.get("gaps_persisted", 0),
                    "failed_count": summary.get("assets_failed", 0),
                },
            )

            # Auto-progress to next phase if gaps were persisted
            await _auto_progress_phase(
                job_id=job_id,
                collection_flow_id=collection_flow_id,
                gaps_persisted=summary.get("gaps_persisted", 0),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=db,
            )

            logger.info(f"✅ Job {job_id}: Enhancement complete")

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)
        await update_job_state(
            collection_flow_id,
            {
                "status": "failed",
                "error": str(e),
            },
        )


async def _auto_progress_phase(
    job_id: str,
    collection_flow_id: UUID,
    gaps_persisted: int,
    client_account_id: str,
    engagement_id: str,
    db,
):
    """Auto-progress to questionnaire_generation phase if gaps were persisted.

    Args:
        job_id: Job identifier for logging
        collection_flow_id: Collection flow internal ID
        gaps_persisted: Number of gaps successfully persisted
        client_account_id: Client account UUID (primitive)
        engagement_id: Engagement UUID (primitive)
        db: Database session
    """
    if gaps_persisted <= 0:
        return

    try:
        # Get collection flow for progression
        from sqlalchemy import and_, select

        from app.models.collection_flow import CollectionFlow

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

            # IMPORTANT: Create immutable context from primitives for progression service
            # Background jobs receive only primitive IDs (str), not mutable request context.
            # This RequestContext is constructed here as an immutable container of primitives
            # required by CollectionPhaseProgressionService and MFO utilities.
            # It is NOT the request context from the HTTP handler.
            from app.core.context import RequestContext
            from app.services.collection_phase_progression_service import (
                CollectionPhaseProgressionService,
            )

            temp_context = RequestContext(
                client_account_id=UUID(
                    client_account_id
                ),  # Converted from str primitive
                engagement_id=UUID(engagement_id),  # Converted from str primitive
                user_id=None,  # Background job has no user
            )

            progression_service = CollectionPhaseProgressionService(
                db_session=db, context=temp_context
            )
            progression_result = await progression_service.advance_to_next_phase(
                flow=collection_flow,
                target_phase="questionnaire_generation",
            )

            if progression_result["status"] == "success":
                logger.info(f"✅ Job {job_id}: Advanced to questionnaire_generation")
                await update_job_state(
                    collection_flow_id,
                    {"phase_progression": "advanced_to_questionnaire_generation"},
                )
            else:
                error_msg = progression_result.get("error")
                logger.warning(f"⚠️ Job {job_id}: Phase progression failed: {error_msg}")
                await update_job_state(
                    collection_flow_id,
                    {"phase_progression": f"failed: {error_msg}"},
                )
    except Exception as progression_error:
        logger.error(
            f"❌ Job {job_id}: Phase progression error: {progression_error}",
            exc_info=True,
        )
        await update_job_state(
            collection_flow_id,
            {"phase_progression": f"error: {progression_error}"},
        )
