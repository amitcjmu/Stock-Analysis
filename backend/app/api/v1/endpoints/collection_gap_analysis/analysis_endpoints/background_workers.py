"""
Background Workers for Gap Analysis Jobs

Handles asynchronous processing of comprehensive AI gap analysis with per-asset persistence.

CRITICAL: This uses comprehensive analysis (_run_tier_2_ai_analysis), NOT enhancement.
The AI analyzes the ENTIRE asset to find ALL gaps, not just enhance predetermined ones.
"""

import logging
from uuid import UUID

from .job_state_manager import update_job_state

logger = logging.getLogger(__name__)


async def verify_ai_gaps_consistency(assets, db):
    """Verify that assets marked as AI-analyzed have gaps with confidence_score.

    This ensures data consistency across all collection flows, not just the current one.

    Args:
        assets: List of Asset objects to verify
        db: AsyncSession database session
    """
    from sqlalchemy import select, func
    from app.models.collection_data_gap import CollectionDataGap

    for asset in assets:
        # Check if gaps with AI enhancement exist for this asset (across ALL flows)
        stmt = select(func.count()).where(
            CollectionDataGap.asset_id == asset.id,
            CollectionDataGap.confidence_score.is_not(None),
        )
        result = await db.execute(stmt)
        ai_gaps_count = result.scalar()

        if ai_gaps_count == 0:
            logger.warning(
                f"⚠️ Consistency issue: Asset {asset.id} marked as AI-analyzed "
                f"(status=2) but has no gaps with confidence_score"
            )
        else:
            logger.debug(
                f"✅ Asset {asset.id} consistency verified - "
                f"{ai_gaps_count} AI-enhanced gaps found"
            )


async def process_gap_enhancement_job(  # noqa: C901
    job_id: str,
    collection_flow_id: UUID,
    selected_asset_ids: list,
    client_account_id: str,
    engagement_id: str,
    force_refresh: bool = False,
):
    """Background worker for comprehensive AI gap analysis.

    Performs full asset analysis without requiring predetermined gaps.
    This enables comprehensive discovery of all data gaps.

    Skips assets with ai_gap_analysis_status = 2 unless force_refresh = True.
    Implements stale detection by comparing ai_gap_analysis_timestamp with asset.updated_at.

    Args:
        job_id: Unique job identifier
        collection_flow_id: Collection flow internal ID (used for all DB operations)
        selected_asset_ids: Asset IDs to analyze comprehensively
        client_account_id: Client account UUID (primitive, not mutable context)
        engagement_id: Engagement UUID (primitive, not mutable context)
        force_refresh: Force re-analysis even if status=2 (default: False)
    """
    from app.services.collection.gap_analysis.data_loader import load_assets
    from app.services.collection.gap_analysis.service import GapAnalysisService
    from datetime import datetime, timezone

    try:
        await update_job_state(collection_flow_id, {"status": "running"})

        # Get database session for background task
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Load assets (using primitive IDs)
            all_assets = await load_assets(
                selected_asset_ids,
                client_account_id,
                engagement_id,
                db,
            )

            if not all_assets:
                logger.warning("⚠️ No assets found for AI analysis")
                await update_job_state(
                    collection_flow_id,
                    {
                        "status": "completed",
                        "message": "No assets found",
                    },
                )
                return

            # Filter assets based on AI analysis status and staleness
            if force_refresh:
                # User forced re-analysis - analyze all assets
                assets_to_analyze = all_assets
                logger.info(
                    f"🔄 Force refresh enabled - analyzing all {len(all_assets)} assets"
                )
            else:
                # Skip assets that already completed AI analysis (status = 2) AND aren't stale
                assets_to_analyze = []
                assets_skipped = 0
                assets_stale = 0

                for asset in all_assets:
                    # Check if AI analysis completed
                    if asset.ai_gap_analysis_status != 2:
                        assets_to_analyze.append(asset)
                        continue

                    # Check if analysis is stale (asset updated after analysis)
                    if (
                        asset.ai_gap_analysis_timestamp
                        and asset.updated_at
                        and asset.updated_at > asset.ai_gap_analysis_timestamp
                    ):
                        assets_to_analyze.append(asset)
                        assets_stale += 1
                        logger.debug(
                            f"📊 Asset {asset.id} marked for re-analysis - "
                            f"updated_at={asset.updated_at} > "
                            f"ai_analysis_timestamp={asset.ai_gap_analysis_timestamp}"
                        )
                    else:
                        assets_skipped += 1

                logger.info(
                    f"📊 AI analysis plan - "
                    f"Analyze: {len(assets_to_analyze)} "
                    f"(new: {len(assets_to_analyze) - assets_stale}, stale: {assets_stale}), "
                    f"Skipped (cached): {assets_skipped}"
                )

            if not assets_to_analyze:
                logger.info("✅ All assets already have AI analysis - nothing to do")
                await update_job_state(
                    collection_flow_id,
                    {
                        "status": "completed",
                        "progress": 100,
                        "message": "All assets already analyzed",
                    },
                )
                return

            # Mark assets as in-progress (status = 1)
            for asset in assets_to_analyze:
                asset.ai_gap_analysis_status = 1
            await db.flush()

            # Initialize gap analysis service (using primitive IDs)
            gap_service = GapAnalysisService(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                collection_flow_id=str(collection_flow_id),
            )

            # Run tier_2 comprehensive AI analysis
            logger.info(
                f"🤖 Job {job_id}: Running COMPREHENSIVE AI analysis "
                f"on {len(assets_to_analyze)} assets"
            )

            # Correct - comprehensive analysis on assets only
            ai_result = await gap_service._run_tier_2_ai_analysis(
                assets=assets_to_analyze,
                collection_flow_id=str(collection_flow_id),
                db=db,
            )

            # Mark assets as completed (status = 2) with timestamp
            completion_time = datetime.now(timezone.utc)

            for asset in assets_to_analyze:
                asset.ai_gap_analysis_status = 2
                asset.ai_gap_analysis_timestamp = completion_time

            await db.commit()

            # Verify consistency: gaps with confidence_score should exist
            await verify_ai_gaps_consistency(assets_to_analyze, db)

            logger.info(
                f"✅ AI analysis completed for {len(assets_to_analyze)} assets "
                f"at {completion_time.isoformat()}"
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
        # Bug #892 Fix: Capture detailed error information for user feedback
        error_type = type(e).__name__
        error_message = str(e)

        logger.error(
            f"❌ Job {job_id} failed - {error_type}: {error_message}", exc_info=True
        )

        # Reset status to 0 on failure so analysis can be retried
        from app.core.database import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as db:
                from app.services.collection.gap_analysis.data_loader import load_assets

                # Reload assets to reset status
                failed_assets = await load_assets(
                    selected_asset_ids,
                    client_account_id,
                    engagement_id,
                    db,
                )

                for asset in failed_assets:
                    asset.ai_gap_analysis_status = 0
                    asset.ai_gap_analysis_timestamp = None

                await db.commit()

                logger.info(
                    f"🔄 Reset AI analysis status for {len(failed_assets)} assets to allow retry"
                )
        except Exception as reset_error:
            logger.error(
                f"❌ Failed to reset asset status: {reset_error}", exc_info=True
            )

        # Categorize error for better user messaging
        if "timeout" in error_message.lower() or "TimeoutError" in error_type:
            user_message = (
                "LLM API request timed out. Please try again with fewer assets or gaps."
            )
            error_category = "timeout"
        elif "connection" in error_message.lower() or "ConnectionError" in error_type:
            user_message = "Connection to AI service failed. Please check your network and try again."
            error_category = "connection"
        elif "no assets" in error_message.lower():
            user_message = "No assets found for analysis. Please ensure assets are properly selected."
            error_category = "no_assets"
        elif "authentication" in error_message.lower() or "401" in error_message:
            user_message = "AI service authentication failed. Please contact support."
            error_category = "auth"
        else:
            user_message = f"Enhancement failed: {error_message}"
            error_category = "unknown"

        await update_job_state(
            collection_flow_id,
            {
                "status": "failed",
                "error": error_message,
                "error_type": error_type,
                "error_category": error_category,
                "user_message": user_message,
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
