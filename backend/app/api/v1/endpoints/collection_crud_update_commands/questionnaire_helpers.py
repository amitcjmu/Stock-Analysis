"""
Helper functions for questionnaire submission operations.

Extracted to reduce file length and complexity while preserving all
error handling and logging for Issue #980.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.models.asset import Asset

# Import modular helper functions
from ..collection_crud_helpers import (
    apply_asset_writeback,
    resolve_data_gaps,
)

from .assessment_validation import check_and_set_assessment_ready

if TYPE_CHECKING:
    from app.schemas.collection_flow import QuestionnaireSubmissionRequest

logger = logging.getLogger(__name__)


async def _flush_response_records(
    db: AsyncSession, response_records: list, flow_id: int
) -> None:
    """Flush response records to database immediately.

    The async session has autoflush=False (backend/app/core/database.py).
    Without explicit flush, downstream queries run against stale state.
    """
    try:
        await db.flush()
        logger.info(
            f"✅ Flushed {len(response_records)} response records to database: "
            f"IDs={[str(r.id) for r in response_records]}, "
            f"collection_flow_id={flow_id}"
        )
    except Exception as flush_error:
        logger.error(
            f"❌ FLUSH FAILED for collection_flow_id={flow_id}: {flush_error}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist questionnaire responses: {flush_error}",
        ) from flush_error


def _extract_from_response_records(response_records: list) -> set:
    """Extract asset IDs from response records."""
    return {r.asset_id for r in response_records if r.asset_id}


def _extract_from_validated_asset(validated_asset: Any) -> set:
    """Extract asset ID from validated asset."""
    return {validated_asset.id} if validated_asset else set()


def _extract_from_asset_id(asset_id: Any) -> set:
    """Extract asset ID from form metadata."""
    if not asset_id:
        return set()
    try:
        return {UUID(asset_id) if isinstance(asset_id, str) else asset_id}
    except (ValueError, TypeError):
        logger.warning(f"Invalid asset_id in form_metadata: {asset_id}")
        return set()


def _extract_from_composite_field_ids(form_responses: Dict[str, Any]) -> set:
    """Extract asset IDs from composite field IDs (format: {asset_id}__{field_id})."""
    asset_ids = set()
    for field_id in form_responses.keys():
        if "__" in field_id:
            parts = field_id.split("__", 1)
            if len(parts) == 2:
                try:
                    asset_ids.add(UUID(parts[0]))
                except (ValueError, TypeError):
                    pass  # Not a UUID, skip
    return asset_ids


def _extract_from_flow_metadata(flow: CollectionFlow) -> set:
    """Extract asset IDs from flow metadata."""
    if not flow.flow_metadata:
        return set()

    selected_asset_ids = flow.flow_metadata.get("selected_asset_ids", [])
    if not selected_asset_ids:
        return set()

    asset_ids = set()
    try:
        for aid in selected_asset_ids[:5]:  # Limit to 5 for performance
            asset_ids.add(UUID(aid) if isinstance(aid, str) else aid)
    except (ValueError, TypeError):
        logger.warning(f"Invalid asset IDs in flow metadata: {selected_asset_ids}")

    return asset_ids


async def _extract_asset_ids_for_reanalysis(
    response_records: list,
    validated_asset: Any,
    asset_id: Any,
    form_responses: Dict[str, Any],
    flow: CollectionFlow,
) -> list:
    """Extract asset IDs from response records for readiness re-analysis.

    Response records extract asset_id from composite field IDs (format: {asset_id}__{field_id}).
    Uses cascading fallback strategy to find asset IDs from multiple sources.
    """
    # Try primary source first
    asset_ids = _extract_from_response_records(response_records)

    # Fallback sources if primary source is empty
    if not asset_ids:
        asset_ids = _extract_from_validated_asset(validated_asset)
    if not asset_ids:
        asset_ids = _extract_from_asset_id(asset_id)
    if not asset_ids:
        asset_ids = _extract_from_composite_field_ids(form_responses)
    if not asset_ids:
        asset_ids = _extract_from_flow_metadata(flow)

    # Convert to list and log
    asset_ids_list = list(asset_ids)
    logger.info(
        f"📋 Extracted {len(asset_ids_list)} asset ID(s) "
        f"for readiness re-analysis: {[str(aid) for aid in asset_ids_list]}"
    )

    return asset_ids_list


async def _resolve_gaps_and_update_flow(
    response_records: list,
    gap_index: Dict[str, Any],
    form_responses: Dict[str, Any],
    flow: CollectionFlow,
    questionnaire_uuid: UUID,
    request_data: "QuestionnaireSubmissionRequest",
    context: RequestContext,
    db: AsyncSession,
) -> int:
    """Mark gaps as resolved and update questionnaire completion status.

    Returns the number of gaps resolved.
    """
    gaps_resolved = 0

    if response_records:
        # ✅ CRITICAL FIX (Issue #980): Flush before resolve_data_gaps
        # resolve_data_gaps modifies gap objects (resolution_status, resolved_value)
        # We need to flush response_records first so gaps can reference them
        try:
            await db.flush()
            logger.debug(
                f"Flushed before resolve_data_gaps for collection_flow_id={flow.id}"
            )
        except Exception as flush_error:
            logger.error(
                f"❌ FLUSH FAILED before resolve_data_gaps: {flush_error}",
                exc_info=True,
            )
            raise

        gaps_resolved = await resolve_data_gaps(gap_index, form_responses, db)

    # CRITICAL FIX: Mark questionnaire as completed after successful submission
    # This prevents the same questionnaire from being returned in a loop
    questionnaire_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(AdaptiveQuestionnaire.id == questionnaire_uuid)
        .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
    )
    questionnaire = questionnaire_result.scalar_one_or_none()

    if questionnaire:
        # CRITICAL FIX (Issue #692): Check save_type to determine completion status
        # - save_progress: Keep as in_progress, skip assessment check
        # - submit_complete: Mark as completed, trigger assessment check
        if request_data.save_type == "submit_complete":
            questionnaire.completion_status = "completed"
            questionnaire.completed_at = datetime.utcnow()
            logger.info(
                f"✅ FIX#692: Marking questionnaire {questionnaire_uuid} as completed "
                f"(save_type={request_data.save_type})"
            )

            # Check if collection is complete and ready for assessment
            # Required attributes: business_criticality, environment
            await check_and_set_assessment_ready(
                flow, form_responses, db, context, logger
            )
        else:
            # save_progress: Keep as in_progress
            questionnaire.completion_status = "in_progress"
            logger.info(
                f"💾 FIX#692: Saving progress for questionnaire {questionnaire_uuid} "
                f"(save_type={request_data.save_type}, status=in_progress)"
            )

        # Always update responses_collected for both save types
        questionnaire.responses_collected = form_responses
    else:
        logger.warning(
            f"⚠️ Could not find questionnaire {questionnaire_uuid} to mark as completed"
        )

    return gaps_resolved


async def _commit_with_writeback(
    gaps_resolved: int,
    flow: CollectionFlow,
    context: RequestContext,
    current_user: User,
    response_records: list,
    db: AsyncSession,
) -> None:
    """Apply asset writeback and commit all changes atomically."""
    # Apply resolved gaps to assets via write-back service before commit
    # This preserves atomicity - both DB changes and writeback succeed or both fail
    try:
        await apply_asset_writeback(gaps_resolved, flow, context, current_user, db)
        logger.info(f"✅ Asset writeback completed for {gaps_resolved} resolved gaps")
    except Exception as writeback_error:
        logger.error(
            f"❌ WRITEBACK FAILED for collection_flow_id={flow.id}: {writeback_error}",
            exc_info=True,
        )
        raise

    # Commit all changes (including writeback updates) atomically
    try:
        # Check transaction is still active before committing
        if not db.in_transaction():
            logger.error(
                f"❌ Transaction NOT ACTIVE before commit for collection_flow_id={flow.id}"
            )
            raise HTTPException(
                status_code=500,
                detail="Transaction rolled back unexpectedly - cannot commit responses",
            )

        logger.info(
            f"Committing {len(response_records)} response records to database "
            f"(collection_flow_id={flow.id}, response_ids={[str(r.id) for r in response_records[:5]]}...)"
        )
        await db.commit()
        logger.info(
            f"✅ COMMIT SUCCESSFUL for collection_flow_id={flow.id} - "
            f"{len(response_records)} responses persisted"
        )
    except Exception as commit_error:
        logger.error(
            f"❌ COMMIT FAILED for collection_flow_id={flow.id}: {commit_error}",
            exc_info=True,
        )
        raise


async def _create_canonical_app_for_questionnaire(
    application_name: str,
    asset_id: UUID,
    flow: CollectionFlow,
    context: RequestContext,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Create canonical application and junction record for questionnaire submission.

    This ensures questionnaire path has same behavior as bulk import path.
    Non-blocking: failures don't halt questionnaire submission.

    ISSUE-999 Phase 2: Canonicalization for Questionnaire Path
    """
    try:
        logger.info(
            f"[ISSUE-999-PHASE2] Creating canonical app for questionnaire: "
            f"'{application_name}' (asset: {asset_id})"
        )

        # Import models
        from app.models.canonical_applications.canonical_application import (
            CanonicalApplication,
        )
        from app.models.canonical_applications.collection_flow_app import (
            CollectionFlowApplication,
        )
        from uuid import uuid4

        # Create/find canonical application (with Phase 1 retry logic)
        canonical_app, is_new, variant = (
            await CanonicalApplication.find_or_create_canonical(
                db=db,
                application_name=application_name,
                client_account_id=UUID(context.client_account_id),
                engagement_id=UUID(context.engagement_id),
                user_id=current_user.id if current_user else None,
            )
        )

        logger.info(
            f"[ISSUE-999-PHASE2] Canonical app: {canonical_app.canonical_name} "
            f"(ID: {canonical_app.id}, is_new: {is_new})"
        )

        # Check if junction record already exists
        from sqlalchemy import select as sa_select

        existing_junction_result = await db.execute(
            sa_select(CollectionFlowApplication).where(
                CollectionFlowApplication.asset_id == asset_id,
                CollectionFlowApplication.collection_flow_id == flow.id,
            )
        )
        junction_exists = existing_junction_result.scalar_one_or_none() is not None

        if not junction_exists:
            # Create junction record
            junction_record = CollectionFlowApplication(
                id=uuid4(),
                collection_flow_id=flow.id,
                asset_id=asset_id,
                application_name=application_name,
                canonical_application_id=canonical_app.id,
                name_variant_id=variant.id if variant else None,
                client_account_id=UUID(context.client_account_id),
                engagement_id=UUID(context.engagement_id),
                deduplication_method="questionnaire_auto",
                match_confidence=canonical_app.confidence_score,
                collection_status="pending",
            )
            db.add(junction_record)

            logger.info(
                f"[ISSUE-999-PHASE2] Created junction record: "
                f"asset {asset_id} → canonical app {canonical_app.id}"
            )
        else:
            logger.info(
                f"[ISSUE-999-PHASE2] Junction record already exists for "
                f"asset {asset_id} in flow {flow.id}"
            )

    except Exception as e:
        logger.error(
            f"[ISSUE-999-PHASE2] Failed to create canonical app for questionnaire: {e}",
            exc_info=True,
        )
        # Don't fail entire submission - canonical app creation is non-critical
        # The asset and questionnaire responses are still valid without it


async def _update_asset_readiness(
    asset_ids_to_reanalyze: list,
    request_data: "QuestionnaireSubmissionRequest",
    context: RequestContext,
    db: AsyncSession,
) -> bool:
    """Re-analyze asset readiness after questionnaire submission.

    Returns True if any asset readiness was updated.

    IMPORTANT: This function does NOT commit changes - the caller must manage
    the transaction to ensure atomicity with other operations.

    CC FIX: For questionnaire completion, we set assessment_readiness='ready'
    directly because:
    1. The questionnaire was generated by IntelligentGapScanner for TRUE gaps
    2. The user has submitted answers for those gaps
    3. Therefore, the data collection is complete for this asset

    We don't re-run GapAnalyzer because it uses different (stricter) requirements
    than IntelligentGapScanner and would create a mismatch.
    """
    readiness_updated = False

    if not (asset_ids_to_reanalyze and request_data.save_type == "submit_complete"):
        return False

    try:
        logger.info(
            f"🔄 Updating readiness for {len(asset_ids_to_reanalyze)} asset(s) "
            f"after questionnaire submission (save_type={request_data.save_type})"
        )

        # CC FIX: Mark assets as ready directly when questionnaire is completed
        # The questionnaire was generated for TRUE gaps by IntelligentGapScanner
        # User has now submitted responses, so the asset is ready for assessment
        for asset_uuid in asset_ids_to_reanalyze:
            update_stmt = (
                update(Asset)
                .where(
                    Asset.id == asset_uuid,
                    Asset.client_account_id == context.client_account_id,
                    Asset.engagement_id == context.engagement_id,
                )
                .values(
                    # CC FIX: Set to 'ready' directly - questionnaire completion = data collection complete
                    assessment_readiness="ready",
                    # Also update sixr_ready for Assessment Flow UI
                    sixr_ready="ready",
                )
            )
            await db.execute(update_stmt)
            readiness_updated = True

            logger.info(
                f"✅ CC FIX: Marked asset {asset_uuid} as assessment_readiness='ready' "
                f"(questionnaire completed via submit_complete)"
            )

        if readiness_updated:
            logger.info("✅ Asset readiness updates staged for commit.")

    except Exception as e:
        logger.error(
            f"Failed to update asset readiness after submission: {e}",
            exc_info=True,
        )
        # Re-raise to ensure transaction is rolled back
        raise

    return readiness_updated
